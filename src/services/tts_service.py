"""
ElevenLabs Text-to-Speech service for generating high-quality audio from stories
"""
import asyncio
import logging
from typing import Optional
from io import BytesIO

from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

from ..core.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Service for converting text to speech using ElevenLabs"""

    def __init__(self):
        """Initialize ElevenLabs Text-to-Speech client"""
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ElevenLabs client"""
        try:
            if settings.ELEVENLABS_API_KEY:
                self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
                logger.info("✅ ElevenLabs TTS client initialized successfully")
            else:
                logger.warning("⚠️ ELEVENLABS_API_KEY not set. TTS will not be available.")
                self.client = None
        except Exception as e:
            logger.error(f"❌ Error initializing ElevenLabs TTS client: {e}")
            self.client = None

    def list_voices(self):
        """List available ElevenLabs voices (limited by API permissions)"""
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return []
        
        # Use default voices since API key may not have voices_read permission
        default_voices = [
            {"voice_id": "XB0fDUnXU5powFXDhCwa", "name": "Charlotte", "description": "Молодая женщина, отлично для детских сказок"},
            {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "Надежный женский голос"},
            {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "description": "Детский женский голос"},
            {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "description": "Дружелюбный женский голос"},
            {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "description": "Теплый мужской голос"},
            {"voice_id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "description": "Эмоциональный женский голос"},
        ]
        
        logger.info(f"📋 Using {len(default_voices)} default voices")
        for voice in default_voices:
            logger.info(f"🎙️ Voice: {voice['name']} (ID: {voice['voice_id']})")
        
        return default_voices

    async def generate_audio_for_story(
        self,
        story_text: str,
        child_name: str,
        child_age: int,
        mood: str = "cheerful",
        voice_id: Optional[str] = None
    ) -> Optional[BytesIO]:
        """
        Generate audio for a story with child-specific personalization
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return None

        # Choose voice: use provided voice_id or select based on child's age
        if voice_id is None:
            voice_id = self._get_child_appropriate_voice(child_age)
        
        # Create personalized intro
        intro_text = f"Привет, {child_name}! Специально для тебя - новая сказка!"
        full_text = f"{intro_text}\n\n{story_text}"
        
        try:
            logger.info(f"🎙️ Generating audio for {child_name} (age {child_age}, mood: {mood})")
            
            # Get emotion-based voice settings
            emotion_settings = self._get_emotion_settings(mood)
            
            voice_settings = VoiceSettings(
                stability=emotion_settings["stability"],
                similarity_boost=emotion_settings["similarity_boost"],
                style=emotion_settings["style"],
                use_speaker_boost=settings.ELEVENLABS_USE_SPEAKER_BOOST
            )
            
            audio_bytes = self.client.text_to_speech.convert(
                text=full_text,
                voice_id=voice_id,
                voice_settings=voice_settings,
                model_id=settings.ELEVENLABS_MODEL_ID
            )
            
            # Convert generator to bytes
            audio_data = b"".join(audio_bytes)
            audio_buffer = BytesIO(audio_data)
            audio_buffer.seek(0)
            
            logger.info(f"✅ Audio generated successfully for {child_name}: {len(audio_data)} bytes")
            return audio_buffer
            
        except Exception as e:
            error_str = str(e)
            if "quota_exceeded" in error_str:
                logger.warning(f"⚠️ ElevenLabs quota exceeded for {child_name}")
            elif "unauthorized" in error_str.lower():
                logger.error(f"❌ ElevenLabs API key unauthorized")
            else:
                logger.error(f"❌ Error generating story audio: {e}")
            return None

    async def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None
    ) -> Optional[BytesIO]:
        """
        Generate basic audio from text
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return None

        voice_id = voice_id or settings.ELEVENLABS_VOICE_ID
        
        try:
            logger.info(f"🎙️ Generating audio with voice {voice_id}")
            
            voice_settings = VoiceSettings(
                stability=settings.ELEVENLABS_STABILITY,
                similarity_boost=settings.ELEVENLABS_SIMILARITY_BOOST,
                style=settings.ELEVENLABS_STYLE,
                use_speaker_boost=settings.ELEVENLABS_USE_SPEAKER_BOOST
            )
            
            audio_bytes = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                voice_settings=voice_settings,
                model_id=settings.ELEVENLABS_MODEL_ID
            )
            
            # Convert generator to bytes
            audio_data = b"".join(audio_bytes)
            audio_buffer = BytesIO(audio_data)
            audio_buffer.seek(0)
            
            logger.info(f"✅ Audio generated successfully: {len(audio_data)} bytes")
            return audio_buffer
            
        except Exception as e:
            logger.error(f"❌ Error generating audio: {e}")
            return None

    def _get_child_appropriate_voice(self, child_age: int) -> str:
        """
        Select appropriate voice based on child's age
        """
        # Для детей 2-8 лет используем более мягкие голоса
        if child_age <= 4:
            # Очень маленькие дети - самый мягкий голос
            return settings.ELEVENLABS_VOICE_ID  # Bella по умолчанию
        elif child_age <= 6:
            # Дошкольники - дружелюбный голос
            return settings.ELEVENLABS_VOICE_ID
        else:
            # Школьники - чуть более взрослый голос
            return settings.ELEVENLABS_VOICE_ID

    def _get_emotion_settings(self, mood: str) -> dict:
        """
        Get voice settings based on story mood
        """
        emotion_configs = {
            "cheerful": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.3
            },
            "calm": {
                "stability": 0.8,
                "similarity_boost": 0.9,
                "style": 0.1
            },
            "excited": {
                "stability": 0.6,
                "similarity_boost": 0.7,
                "style": 0.4
            },
            "mysterious": {
                "stability": 0.9,
                "similarity_boost": 0.85,
                "style": 0.2
            }
        }
        
        return emotion_configs.get(mood, emotion_configs["cheerful"])