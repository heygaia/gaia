import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional
import aiohttp
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.llm import LLM, ChatChunk, ChatContext, ChoiceDelta
from livekit.plugins import deepgram, noise_cancellation, silero, elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
logging.basicConfig(level=logging.INFO)
load_dotenv(".env")


def _extract_meta_data(md: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Extract agentToken and conversationId from participant metadata JSON."""
    if not md:
        return None, None
    try:
        obj = json.loads(md)
        tok = obj.get("agentToken")
        conv_id = obj.get("conversationId")
        tok = tok if isinstance(tok, str) and tok else None
        conv_id = conv_id if isinstance(conv_id, str) and conv_id else None
        return tok, conv_id
    except Exception:
        return None, None


def _extract_latest_user_text(chat_ctx: ChatContext) -> str:
    """Best-effort extraction of the latest user text string from ChatContext."""
    for item in reversed(chat_ctx.items):
        role = getattr(item, "role", item.__class__.__name__.lower())
        if role == "user":
            content = getattr(item, "content", [getattr(item, "output", "")])
            parts = []
            for c in content:
                if hasattr(c, "model_dump"):
                    d = c.model_dump()
                    if isinstance(d, dict):
                        parts.append(d.get("text", ""))
                else:
                    parts.append(str(c))
            out = " ".join(p for p in parts if p)
            if out:
                return out
    return ""


class CustomLLM(LLM):
    def __init__(self, base_url: str, request_timeout_s: float = 60.0, room=None):
        super().__init__()
        self.base_url = base_url
        self.agent_token: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.request_timeout_s = request_timeout_s
        self.room = room  # LiveKit room instance

    def set_agent_token(self, token: Optional[str]):
        self.agent_token = token

    async def set_conversation_id(self, conversation_id: Optional[str]):
        self.conversation_id = conversation_id
        if self.room and self.room.local_participant:
            try:
                await self.room.local_participant.send_text(
                    conversation_id, topic="conversation-id"
                )
            except Exception as e:
                print(f"Failed to send conversation ID: {e}")

    @asynccontextmanager
    async def chat(self, chat_ctx: ChatContext, **kwargs):
        """
        Stream Server-Sent Events from your backend and yield tiny ChatChunks so
        LiveKit can TTS-stream them immediately to ElevenLabs.
        """

        async def gen() -> AsyncGenerator[ChatChunk, None]:
            user_message = _extract_latest_user_text(chat_ctx)

            timeout = aiohttp.ClientTimeout(total=self.request_timeout_s)
            headers = {"x-timezone": "UTC"}
            if self.agent_token:
                headers["Authorization"] = f"Bearer {self.agent_token}"

            payload = {
                "message": user_message,
                "messages": [{"role": "user", "content": user_message}],
            }
            if self.conversation_id:
                payload["conversation_id"] = self.conversation_id

            async with aiohttp.ClientSession(timeout=timeout) as session:  # noqa: SIM117
                async with session.post(
                    f"{self.base_url}/api/v1/chat-stream",
                    headers=headers,
                    json=payload,
                ) as resp:
                    resp.raise_for_status()

                    buf: list[str] = []

                    async for raw in resp.content:
                        if not raw:
                            continue
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if not line or not line.startswith("data:"):
                            continue

                        data = line[5:].strip()
                        if data == "[DONE]":
                            if buf:
                                chunk = "".join(buf).strip()
                                if chunk:
                                    yield ChatChunk(
                                        id="custom", delta=ChoiceDelta(content=chunk)
                                    )
                                    buf.clear()  # Clear buffer after yielding to avoid duplicate final flush
                            break

                        try:
                            payload = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        conv_id = payload.get("conversation_id")
                        if isinstance(conv_id, str) and conv_id:
                            await self.set_conversation_id(conv_id)
                            continue  # skip control frames

                        piece = payload.get("response", "")
                        if not piece:
                            continue

                        # Ensure only strings are appended to buf
                        if isinstance(piece, str):
                            buf.append(piece)
                        elif isinstance(piece, (list, tuple, set)):
                            buf.append("".join(str(x) for x in piece))
                        else:
                            buf.append(str(piece))
                        joined = "".join(buf)

                        # --- Improved flush strategy ---
                        should_flush = False

                        # Natural sentence boundary
                        if any(joined.endswith(p) for p in [".", "!", "?"]):
                            if len(joined) >= 40:  # avoid ultra-short chunks
                                should_flush = True

                        # Mid-sentence, buffer getting long
                        elif len(joined) >= 120:
                            should_flush = True

                        if should_flush:
                            out = joined.strip()
                            buf.clear()
                            if len(out) >= 15:  # safety: never flush tiny fragments
                                # small debounce to coalesce nearby tokens
                                yield ChatChunk(
                                    id="custom", delta=ChoiceDelta(content=out)
                                )
                                await asyncio.sleep(0.1)

                    # Final flush (only if buffer is not empty, and wasn't just flushed)
                    if buf:
                        tail = "".join(buf).strip()
                        if len(tail) >= 1:
                            yield ChatChunk(
                                id="custom", delta=ChoiceDelta(content=tail)
                            )

        yield gen()


def prewarm(proc: JobProcess):
    # Preload VAD to avoid first-turn latency
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    custom_llm = CustomLLM(
        base_url=os.getenv("GAIA_BACKEND_URL", "http://host.docker.internal:8000"), room=ctx.room
    )

    session = AgentSession(
        llm=custom_llm,
        stt=deepgram.STT(model="nova-3", language="multi"),
        tts=elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
            model=os.getenv("ELEVENLABS_TTS_MODEL", "eleven_turbo_v2_5"),
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
                speed=1.0,
            ),
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,  # lets TTS get going while ASR is finishing
        use_tts_aligned_transcript=True,  # helps reduce barge-in artifacts
    )

    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # --- Register event listeners BEFORE connecting ---
    async def _maybe_set_from_md(md: Optional[str], origin: str, who: str):
        tok, conv_id = _extract_meta_data(md)
        if tok:
            custom_llm.set_agent_token(tok)
        if conv_id:
            await custom_llm.set_conversation_id(conv_id)

    background_tasks = set()

    @ctx.room.on("participant_connected")
    def _on_participant_connected(p: rtc.RemoteParticipant):
        logger.info("ddd")
        task = asyncio.create_task(
            _maybe_set_from_md(
                getattr(p, "metadata", None), "participant_connected", p.identity
            )
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    @ctx.room.on("participant_metadata_changed")
    def _on_participant_metadata_changed(p: rtc.Participant, old_md: str, new_md: str):
        task = asyncio.create_task(
            _maybe_set_from_md(new_md, "participant_metadata_changed", p.identity)
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    await ctx.connect()
    for p in ctx.room.remote_participants.values():
        logger.info("participant already present, processing metadata")
        await _maybe_set_from_md(
            getattr(p, "metadata", None), "existing_participant", p.identity
        )

    await session.start(
        agent=Agent(instructions="Avoid markdowns"),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
