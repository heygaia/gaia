"""Agent session management and event handling."""

import asyncio
import logging
from typing import Optional

from livekit import rtc
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    MetricsCollectedEvent,
    RoomInputOptions,
    metrics,
)
from livekit.plugins import deepgram, elevenlabs, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from .config import config
from .llm import CustomLLM
from .utils import extract_metadata

logger = logging.getLogger("agent")


class VoiceAgentSession:
    """
    Manages the voice agent session including setup, event handling, and lifecycle.
    
    This class encapsulates all the session-related functionality including:
    - Agent session configuration
    - Event listener registration
    - Metrics collection
    - Participant management
    """
    
    def __init__(self, context: JobContext, custom_llm: CustomLLM):
        """
        Initialize the voice agent session.
        
        Args:
            context: LiveKit job context
            custom_llm: Configured CustomLLM instance
        """
        self.context = context
        self.custom_llm = custom_llm
        self.session: Optional[AgentSession] = None
        self.usage_collector = metrics.UsageCollector()
        self.background_tasks: set[asyncio.Task] = set()
        
        # Configure logging context
        context.log_context_fields = {"room": context.room.name}
    
    async def setup_session(self) -> AgentSession:
        """
        Set up and configure the agent session with all required components.
        
        Returns:
            Configured AgentSession ready for use
        """
        # Validate configuration
        config.validate()
        
        # Create agent session with all components
        self.session = AgentSession(
            llm=self.custom_llm,
            stt=self._create_stt(),
            tts=self._create_tts(),
            turn_detection=MultilingualModel(),
            vad=self.context.proc.userdata["vad"],
            preemptive_generation=True,  # Allows TTS to start while ASR is finishing
            use_tts_aligned_transcript=True,  # Reduces barge-in artifacts
        )
        
        # Register event handlers
        self._register_event_handlers()
        
        return self.session
    
    def _create_stt(self) -> deepgram.STT:
        """
        Create and configure the Speech-to-Text component.
        
        Returns:
            Configured Deepgram STT instance
        """
        return deepgram.STT(model="nova-3", language="multi")
    
    def _create_tts(self) -> elevenlabs.TTS:
        """
        Create and configure the Text-to-Speech component.
        
        Returns:
            Configured ElevenLabs TTS instance
        """
        return elevenlabs.TTS(
            api_key=config.elevenlabs_api_key,
            voice_id=config.elevenlabs_voice_id,
            model=config.elevenlabs_model,
            voice_settings=elevenlabs.VoiceSettings(**config.voice_settings),
        )
    
    def _register_event_handlers(self) -> None:
        """Register all event handlers for the session and room."""
        if not self.session:
            raise ValueError("Session must be created before registering event handlers")
        
        # Session event handlers
        self.session.on("agent_false_interruption")(self._on_agent_false_interruption)
        self.session.on("metrics_collected")(self._on_metrics_collected)
        
        # Room event handlers - register before connecting
        self.context.room.on("participant_connected")(self._on_participant_connected)
        self.context.room.on("participant_metadata_changed")(self._on_participant_metadata_changed)
        
        # Add shutdown callback for usage logging
        self.context.add_shutdown_callback(self._log_usage)
    
    def _on_agent_false_interruption(self, event: AgentFalseInterruptionEvent) -> None:
        """
        Handle false positive interruptions by resuming generation.
        
        Args:
            event: The false interruption event
        """
        logger.info("False positive interruption detected, resuming generation")
        if self.session:
            self.session.generate_reply(instructions=event.extra_instructions or NOT_GIVEN)
    
    def _on_metrics_collected(self, event: MetricsCollectedEvent) -> None:
        """
        Handle metrics collection events.
        
        Args:
            event: The metrics collected event
        """
        metrics.log_metrics(event.metrics)
        self.usage_collector.collect(event.metrics)
    
    def _on_participant_connected(self, participant: rtc.RemoteParticipant) -> None:
        """
        Handle new participant connections.
        
        Args:
            participant: The newly connected participant
        """
        logger.info(f"Participant {participant.identity} connected")
        task = asyncio.create_task(
            self._process_participant_metadata(
                getattr(participant, "metadata", None), 
                "participant_connected", 
                participant.identity
            )
        )
        self._track_background_task(task)
    
    def _on_participant_metadata_changed(
        self, 
        participant: rtc.Participant, 
        old_metadata: str, 
        new_metadata: str
    ) -> None:
        """
        Handle participant metadata changes.
        
        Args:
            participant: The participant whose metadata changed
            old_metadata: Previous metadata value
            new_metadata: New metadata value
        """
        logger.info(f"Metadata changed for participant {participant.identity}")
        task = asyncio.create_task(
            self._process_participant_metadata(
                new_metadata, 
                "participant_metadata_changed", 
                participant.identity
            )
        )
        self._track_background_task(task)
    
    async def _process_participant_metadata(
        self, 
        metadata: Optional[str], 
        origin: str, 
        participant_identity: str
    ) -> None:
        """
        Process participant metadata to extract agent token and conversation ID.
        
        Args:
            metadata: JSON metadata string from participant
            origin: Source of the metadata (for logging)
            participant_identity: Identity of the participant
        """
        agent_token, conversation_id = extract_metadata(metadata)
        
        if agent_token:
            logger.info(f"Setting agent token from {origin} for {participant_identity}")
            self.custom_llm.set_agent_token(agent_token)
        
        if conversation_id:
            logger.info(f"Setting conversation ID from {origin} for {participant_identity}")
            await self.custom_llm.set_conversation_id(conversation_id)
    
    def _track_background_task(self, task: asyncio.Task) -> None:
        """
        Track a background task to prevent it from being garbage collected.
        
        Args:
            task: The task to track
        """
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _log_usage(self) -> None:
        """Log usage statistics at shutdown."""
        summary = self.usage_collector.get_summary()
        logger.info(f"Session usage summary: {summary}")
    
    async def connect_and_start(self) -> None:
        """
        Connect to the room and start the agent session.
        
        This method handles the complete connection process including:
        - Connecting to the LiveKit room
        - Processing existing participants
        - Starting the agent session
        """
        if not self.session:
            raise ValueError("Session must be set up before connecting")
        
        # Connect to the room
        await self.context.connect()
        
        # Process any participants already in the room
        for participant in self.context.room.remote_participants.values():
            logger.info(f"Processing existing participant: {participant.identity}")
            await self._process_participant_metadata(
                getattr(participant, "metadata", None), 
                "existing_participant", 
                participant.identity
            )
        
        # Start the agent session
        await self.session.start(
            agent=Agent(instructions=config.default_instructions),
            room=self.context.room,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )


def create_voice_agent_session(context: JobContext) -> VoiceAgentSession:
    """
    Factory function to create a configured voice agent session.
    
    Args:
        context: LiveKit job context
        
    Returns:
        Configured VoiceAgentSession instance
    """
    # Create CustomLLM instance
    custom_llm = CustomLLM(
        base_url=config.backend_url,
        room=context.room,
    )
    
    # Create and return session
    return VoiceAgentSession(context, custom_llm)