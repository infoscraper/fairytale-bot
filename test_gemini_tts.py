"""
Test script for Gemini 2.5 Pro TTS - Fairytale Generation
Generates an MP3 file from Russian text using Gemini TTS
"""

import os
from google.api_core.client_options import ClientOptions
from google.cloud import texttospeech_v1beta1 as texttospeech
from typing import List
import shutil
import subprocess


def split_text_into_byte_chunks(source_text: str, max_bytes: int = 800) -> List[str]:
    """Split text into UTF-8 byte-limited chunks, preferring sentence boundaries.

    max_bytes should be < 900 to leave headroom for prompt and request envelope.
    """
    if not source_text:
        return []

    sentences: List[str] = []
    buffer: str = ""
    # Simple sentence split respecting Russian punctuation
    for ch in source_text:
        buffer += ch
        if ch in ".!?…\n":
            sentences.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        sentences.append(buffer.strip())

    chunks: List[str] = []
    current: str = ""
    for sent in sentences:
        if not sent:
            continue
        # If single sentence is too large, hard-split by bytes
        if len(sent.encode("utf-8")) > max_bytes:
            hard = sent
            start = 0
            while start < len(hard):
                # binary search optimal slice size under max_bytes
                lo, hi = 1, len(hard) - start
                best = 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    part = hard[start : start + mid]
                    if len(part.encode("utf-8")) <= max_bytes:
                        best = mid
                        lo = mid + 1
                    else:
                        hi = mid - 1
                chunks.append(hard[start : start + best])
                start += best
            continue

        tentative = (current + (" " if current else "") + sent).strip()
        if tentative and len(tentative.encode("utf-8")) <= max_bytes:
            current = tentative
        else:
            if current:
                chunks.append(current)
            current = sent

    if current:
        chunks.append(current)

    return chunks


def generate_fairytale_audio():
    """Generate MP3 audio file from fairytale text using Gemini TTS"""
    
    # Configuration
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "fairytale-bot-473117")
    TTS_LOCATION = "global"
    
    # API endpoint setup
    API_ENDPOINT = (
        f"{TTS_LOCATION}-texttospeech.googleapis.com"
        if TTS_LOCATION != "global"
        else "texttospeech.googleapis.com"
    )
    
    # Initialize client
    client = texttospeech.TextToSpeechClient(
        client_options=ClientOptions(api_endpoint=API_ENDPOINT)
    )
    
    # Voice configuration
    MODEL = "gemini-2.5-flash-tts"
    VOICE = "Algieba"  # Male voice
    LANGUAGE_CODE = "ru-ru"  # Russian
    
    # Prompt and text (must be under 900 bytes combined with text)
    PROMPT = "Расскажи сказку спокойным добрым голосом для ребенка. Используй интонации."
    
    # Note: Text must be under 900 bytes. Cyrillic characters use 2 bytes each.
    # Using first paragraph only for testing
    TEXT = """В волшебном лесу, где ярко светило солнце, жила маленькая девочка по имени Катюша. Каждый день она отправлялась на свою любимую ферму, где играла с кроликами и собирала красивые цветы. Но в этот день Катюша решила исследовать озеро, о котором ей рассказывали дружные лягушки.

Когда она подошла к озеру, то увидела, как на поверхности воды искрились волшебные огоньки. "Что это может быть?" — удивилась Катюша. Вдруг из воды показалась прекрасная принцесса с золотыми волосами и сияющей короной.

"Привет, Катюша! Меня зовут Элиза," — произнесла принцесса. "Это озеро волшебное, и я охраняю его. Но недавно злая ведьма заколдовала моих друзей — единорогов! Теперь они не могут прийти на поверхность. Нам нужна твоя помощь!"""
    
    # Voice selection
    voice = texttospeech.VoiceSelectionParams(
        name=VOICE,
        language_code=LANGUAGE_CODE,
        model_name=MODEL
    )
    
    # Audio configuration
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    print("🎙️  Starting synthesis with Gemini 2.5 Pro TTS...")
    print(f"📢 Voice: {VOICE}")
    print(f"🌍 Language: {LANGUAGE_CODE}")
    print(f"📝 Text length: {len(TEXT)} characters")
    
    # If text is long, split into byte-safe chunks
    chunks = split_text_into_byte_chunks(TEXT, max_bytes=800)
    if not chunks:
        print("⚠️  No text to synthesize.")
        return

    multiple_parts = len(chunks) > 1
    print(f"🔪 Will synthesize in {len(chunks)} chunk(s)")

    for idx, chunk in enumerate(chunks, start=1):
        synthesis_input = texttospeech.SynthesisInput(text=chunk, prompt=PROMPT)
        try:
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            # Save the audio to file (one or multiple parts)
            if multiple_parts:
                output_file = f"fairytale_katyusha_part{idx:02d}.mp3"
            else:
                output_file = "fairytale_katyusha.mp3"
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            print(f"✅ Wrote {output_file} ({len(response.audio_content)} bytes)")
        except Exception as e:
            print(f"❌ Error during synthesis of part {idx}: {e}")
            raise

    if multiple_parts:
        # Try to merge with ffmpeg if available
        if shutil.which("ffmpeg"):
            print("🔗 ffmpeg found. Merging parts into single file…")
            try:
                manifest_path = "parts.txt"
                with open(manifest_path, "w", encoding="utf-8") as mf:
                    for idx in range(1, len(chunks) + 1):
                        mf.write(f"file 'fairytale_katyusha_part{idx:02d}.mp3'\n")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-i",
                        manifest_path,
                        "-c",
                        "copy",
                        "fairytale_katyusha.mp3",
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                print("✅ Merged into fairytale_katyusha.mp3")
            except subprocess.CalledProcessError as e:
                print("⚠️  Failed to merge automatically via ffmpeg. You can merge manually:")
                print("   printf \"file '%s'\\n\" fairytale_katyusha_part*.mp3 > parts.txt")
                print("   ffmpeg -f concat -safe 0 -i parts.txt -c copy fairytale_katyusha.mp3")
        else:
            print("ℹ️  ffmpeg not found. To merge manually:")
            print("   brew install ffmpeg  # macOS")
            print("   printf \"file '%s'\\n\" fairytale_katyusha_part*.mp3 > parts.txt")
            print("   ffmpeg -f concat -safe 0 -i parts.txt -c copy fairytale_katyusha.mp3")


if __name__ == "__main__":
    generate_fairytale_audio()

