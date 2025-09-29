"""
Configuration settings for Fairytale Bot
"""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"  # Model for story generation - better for text output
    
    # ElevenLabs Text-to-Speech
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "XB0fDUnXU5powFXDhCwa"  # Charlotte - excellent for children's stories
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"  # Supports Russian
    ELEVENLABS_STABILITY: float = 0.75  # Voice stability (0.0-1.0)
    ELEVENLABS_SIMILARITY_BOOST: float = 0.85  # Voice similarity (0.0-1.0)
    ELEVENLABS_STYLE: float = 0.2  # Voice style exaggeration (0.0-1.0)
    ELEVENLABS_USE_SPEAKER_BOOST: bool = True  # Enhance speaker clarity
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    BOT_ROLE: str = "poller"  # poller | disabled
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in .env


# Global settings instance
settings = Settings()
