"""
Text-to-Speech service for generating audio from stories.
Supports ElevenLabs and Gemini TTS (Google Cloud Text-to-Speech).
"""
import asyncio
import logging
from typing import Optional, List
from io import BytesIO
import shutil
import subprocess
import os

from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

from google.api_core.client_options import ClientOptions
from google.cloud import texttospeech_v1beta1 as texttospeech

from ..core.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Service for converting text to speech using configured provider."""

    def __init__(self):
        self.client = None
        self.gemini_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize provider clients based on configuration"""
        # ElevenLabs
        try:
            if settings.ELEVENLABS_API_KEY:
                self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
                logger.info("✅ ElevenLabs TTS client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing ElevenLabs TTS client: {e}")
            self.client = None

        # Gemini TTS
        try:
            # Ensure Google credentials are available even without Procfile
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if not creds_path and creds_json:
                temp_path = "/tmp/gsa.json"
                try:
                    import json
                    import base64
                    
                    # Try to decode as Base64 first (for Dokploy compatibility)
                    try:
                        if not creds_json.strip().startswith('{'):
                            # Looks like Base64, try to decode
                            decoded_json = base64.b64decode(creds_json).decode('utf-8')
                            logger.info("🔓 Decoded Base64 credentials")
                            creds_json = decoded_json
                    except Exception:
                        # Not Base64, continue with original
                        pass
                    
                    # Validate and format JSON
                    if isinstance(creds_json, str):
                        # Try to parse as JSON to validate
                        creds_data = json.loads(creds_json)
                    else:
                        creds_data = creds_json
                    
                    # Write formatted JSON
                    with open(temp_path, "w", encoding="utf-8") as f:
                        json.dump(creds_data, f, indent=2)
                    
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
                    logger.info("🔐 Wrote Google credentials JSON to /tmp/gsa.json for Gemini TTS")
                except json.JSONDecodeError as json_err:
                    logger.error(f"❌ Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {json_err}")
                    logger.error(f"JSON content preview: {creds_json[:100]}...")
                    logger.error(f"JSON content (raw): {repr(creds_json[:200])}")
                except Exception as write_err:
                    logger.warning(f"⚠️ Could not write GOOGLE_APPLICATION_CREDENTIALS_JSON: {write_err}")

            api_endpoint = "texttospeech.googleapis.com"
            self.gemini_client = texttospeech.TextToSpeechClient(
                client_options=ClientOptions(api_endpoint=api_endpoint)
            )
            logger.info("✅ Gemini TTS client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Gemini TTS client not available: {e}")
            self.gemini_client = None

    def list_voices(self):
        """List available ElevenLabs voices (limited by API permissions)"""
        if not self.client:
            logger.info("TTS disabled: ElevenLabs client not initialized")
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
        # Use print to guarantee visibility even if logger filters out module logs in prod
        print(f"🔧 TTS_PROVIDER setting: '{settings.TTS_PROVIDER}'")
        if settings.TTS_PROVIDER == "gemini":
            logger.info("🎙️ Using Gemini TTS provider for story generation")
            if not self.gemini_client:
                print("⚠️ Gemini client is not initialized — will return None")
            return await self._gemini_generate_long_audio(
                text=f"Привет, {child_name}! Специально для тебя - новая сказка!\n\n{story_text}",
                prompt="Расскажи сказку спокойным добрым голосом для ребенка. Используй интонации.",
                output_basename="story"
            )

        # Default: ElevenLabs
        if not self.client:
            print("TTS disabled: ElevenLabs client not initialized (falling back to None)")
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
            lower = error_str.lower()
            if "quota_exceeded" in lower:
                logger.info(f"TTS skipped: ElevenLabs quota exceeded for {child_name}")
            elif "401" in lower or "unauthorized" in lower:
                logger.info("TTS skipped: ElevenLabs unauthorized (401).")
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
        if settings.TTS_PROVIDER == "gemini":
            logger.info("🎙️ Using Gemini TTS provider for basic synthesis")
            return await self._gemini_generate_long_audio(
                text=text,
                prompt="Скажи это спокойным, добрым голосом для ребенка.",
                output_basename="tts"
            )

        if not self.client:
            logger.info("TTS disabled: ElevenLabs client not initialized")
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
            msg = str(e).lower()
            if "401" in msg or "unauthorized" in msg:
                logger.info("TTS skipped: ElevenLabs unauthorized (401).")
            else:
                logger.error(f"❌ Error generating audio: {e}")
            return None

    # ---------- Gemini TTS ----------
    def _split_text_into_byte_chunks(self, source_text: str, max_bytes: int) -> List[str]:
        if not source_text:
            return []
        sentences: List[str] = []
        buf = ""
        for ch in source_text:
            buf += ch
            if ch in ".!?…\n":
                sentences.append(buf.strip())
                buf = ""
        if buf.strip():
            sentences.append(buf.strip())

        chunks: List[str] = []
        cur = ""
        for s in sentences:
            if len(s.encode("utf-8")) > max_bytes:
                start = 0
                while start < len(s):
                    lo, hi = 1, len(s) - start
                    best = 1
                    while lo <= hi:
                        mid = (lo + hi) // 2
                        part = s[start : start + mid]
                        if len(part.encode("utf-8")) <= max_bytes:
                            best = mid
                            lo = mid + 1
                        else:
                            hi = mid - 1
                    chunks.append(s[start : start + best])
                    start += best
                continue

            tentative = (cur + (" " if cur else "") + s).strip()
            if tentative and len(tentative.encode("utf-8")) <= max_bytes:
                cur = tentative
            else:
                if cur:
                    chunks.append(cur)
                cur = s
        if cur:
            chunks.append(cur)
        return chunks

    async def _gemini_generate_long_audio(self, text: str, prompt: str, output_basename: str) -> Optional[BytesIO]:
        logger.info(f"🎙️ _gemini_generate_long_audio: Starting, text length: {len(text)}")
        if not self.gemini_client:
            logger.warning("⚠️ TTS disabled: Gemini client not initialized")
            return None

        model = settings.GEMINI_TTS_MODEL
        voice_name = settings.GEMINI_TTS_VOICE
        language_code = settings.GEMINI_TTS_LANGUAGE
        max_bytes = settings.GEMINI_TTS_MAX_BYTES_PER_CHUNK

        logger.info(f"🔧 Gemini TTS config: model={model}, voice={voice_name}, language={language_code}")

        voice = texttospeech.VoiceSelectionParams(
            name=voice_name,
            language_code=language_code,
            model_name=model,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        logger.info(f"📝 Splitting text into chunks (max_bytes={max_bytes})...")
        chunks = self._split_text_into_byte_chunks(text, max_bytes=max_bytes)
        logger.info(f"✅ Text split into {len(chunks)} chunks")
        if not chunks:
            logger.warning("⚠️ No chunks after splitting")
            return None

        # Use temporary directory for files
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="gemini_tts_")
        logger.info(f"📁 Using temp directory: {temp_dir}")
        
        part_paths: List[str] = []
        try:
            for idx, chunk in enumerate(chunks, start=1):
                logger.info(f"🎤 Generating audio for chunk {idx}/{len(chunks)} (length: {len(chunk)} chars)...")
                synthesis_input = texttospeech.SynthesisInput(text=chunk, prompt=prompt)
                
                # Run synchronous API call in thread pool to avoid blocking event loop
                def _synthesize_sync():
                    return self.gemini_client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config,
                    )
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, _synthesize_sync)
                
                logger.info(f"✅ Chunk {idx} synthesized successfully, audio size: {len(response.audio_content)} bytes")
                part_path = os.path.join(temp_dir, f"{output_basename}_part{idx:02d}.mp3")
                with open(part_path, "wb") as f:
                    f.write(response.audio_content)
                part_paths.append(part_path)
                logger.info(f"💾 Saved chunk {idx} to {part_path}")


            logger.info(f"✅ All {len(part_paths)} chunks generated successfully")

            # Merge if multiple parts
            if len(part_paths) == 1:
                logger.info("📦 Single chunk, no merge needed")
                with open(part_paths[0], "rb") as f:
                    data = f.read()
                buf = BytesIO(data)
                buf.seek(0)
                logger.info(f"✅ Returning audio buffer: {len(data)} bytes")
                return buf

            logger.info(f"🔗 Merging {len(part_paths)} chunks with ffmpeg...")
            if shutil.which("ffmpeg"):
                manifest = os.path.join(temp_dir, "parts.txt")
                with open(manifest, "w", encoding="utf-8") as mf:
                    for p in part_paths:
                        mf.write(f"file '{p}'\n")
                out_path = os.path.join(temp_dir, f"{output_basename}.mp3")
                try:
                    # Run ffmpeg in executor to avoid blocking
                    def _run_ffmpeg():
                        return subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-f",
                                "concat",
                                "-safe",
                                "0",
                                "-i",
                                manifest,
                                "-c",
                                "copy",
                                out_path,
                            ],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                    
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, _run_ffmpeg)
                    logger.info(f"✅ Audio merged successfully: {out_path}")
                    with open(out_path, "rb") as f:
                        data = f.read()
                    buf = BytesIO(data)
                    buf.seek(0)
                    logger.info(f"✅ Returning merged audio buffer: {len(data)} bytes")
                    return buf
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ ffmpeg merge failed: {e}")
                except Exception as e:
                    logger.error(f"❌ Error during merge: {e}", exc_info=True)
            else:
                logger.warning("⚠️ ffmpeg not available, cannot merge chunks")

            # Fallback: return first part only if no merge available
            logger.warning("⚠️ Returning first chunk only as fallback")
            with open(part_paths[0], "rb") as f:
                data = f.read()
            buf = BytesIO(data)
            buf.seek(0)
            logger.info(f"✅ Returning first chunk buffer: {len(data)} bytes")
            return buf
            
        except Exception as e:
            logger.error(f"❌ Error in _gemini_generate_long_audio: {e}", exc_info=True)
            return None
        finally:
            # Clean up temporary files
            try:
                import shutil as shutil_module
                if os.path.exists(temp_dir):
                    shutil_module.rmtree(temp_dir)
                    logger.info(f"🧹 Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up temp directory: {e}")

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