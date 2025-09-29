"""Configuration management for voice agent."""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")


class VoiceAgentConfig:
    """Configuration class for voice agent settings."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        # Backend configuration
        self.backend_url = os.getenv("GAIA_BACKEND_URL", "http://host.docker.internal:8000")
        
        # ElevenLabs configuration
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.elevenlabs_model = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_turbo_v2_5")
        
        # Request configuration
        self.request_timeout = 60.0
        
        # TTS voice settings
        self.voice_settings = {
            "stability": 0.0,
            "similarity_boost": 1.0,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.0,
        }
        
        # Text chunking configuration
        self.min_chunk_length = 15
        self.natural_boundary_min_length = 40
        self.max_buffer_length = 120
        
        # Agent instructions
        self.default_instructions = "Avoid markdowns"
    
    def validate(self) -> None:
        """Validate required configuration values."""
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")


# Global configuration instance
config = VoiceAgentConfig()