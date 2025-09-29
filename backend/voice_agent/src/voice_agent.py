"""
Voice Agent for Gaia Backend Integration.

This module provides the main entry point for the voice agent that integrates
with the Gaia backend to provide real-time voice interaction capabilities
using LiveKit for communication and ElevenLabs for TTS.
"""

import logging

from livekit.agents import JobContext, JobProcess, WorkerOptions, cli
from livekit.plugins import silero

from .session import create_voice_agent_session

# Configure logging
logger = logging.getLogger("agent")
logging.basicConfig(level=logging.INFO)


def prewarm(process: JobProcess) -> None:
    """
    Preload components to avoid first-turn latency.
    
    This function preloads the Voice Activity Detection (VAD) model
    to reduce initialization time during the first interaction.
    
    Args:
        process: LiveKit job process instance
    """
    # Preload VAD model to avoid first-turn latency
    process.userdata["vad"] = silero.VAD.load()


async def entrypoint(context: JobContext) -> None:
    """
    Main entry point for the voice agent.
    
    This function sets up and starts the complete voice agent session,
    including LLM integration, session management, and event handling.
    
    Args:
        context: LiveKit job context containing room and connection information
    """
    # Create and configure the voice agent session
    voice_session = create_voice_agent_session(context)
    
    # Set up the session with all components
    await voice_session.setup_session()
    
    # Connect to the room and start the agent
    await voice_session.connect_and_start()


if __name__ == "__main__":
    # Run the voice agent with LiveKit CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
