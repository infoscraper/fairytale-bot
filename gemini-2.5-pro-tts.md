Use Gemini-TTS

Discover how to use Gemini-TTS models to synthesize single-speaker and multi-speaker speech.

Note: The size of the text field and the prompt field individually can be at most 900 bytes. While the total size of the prompt and text fields can be up to 1,800 bytes, each field must be a maximum of 900 bytes.
Note: To be able to use Gemini-TTS, aiplatform.endpoints.predict permission is required for the model endpoint. This permission can be granted with the roles/aiplatform.user role.
Before you begin

Before you can begin using Text-to-Speech, you must enable the API in the Google Cloud console by following steps:

Enable Text-to-Speech on a project.
Make sure billing is enabled for Text-to-Speech.
Set up authentication for your development environment.
Set up your Google Cloud project

Sign in to Google Cloud console
Go to the project selector page

You can either choose an existing project or create a new one. For more details about creating a project, see the Google Cloud documentation.
If you create a new project, a message appears informing you to link a billing account. If you are using a pre-existing project, make sure to enable billing

Learn how to confirm that billing is enabled for your project

Note: You must enable billing to use Text-to-Speech API, however, you won't be be charged unless you exceed the free quota. For more information about pricing, see the pricing page.
After you've selected a project and linked it to a billing account, you can enable the Text-to-Speech API. Go to the Search products and resources bar at the top of the page, and type in "speech". Select the Cloud Text-to-Speech API from the list of results.
To try Text-to-Speech without linking it to your project, choose the Try this API option. To enable the Text-to-Speech API for use with your project, click Enable.
Set up authentication for your development environment. For instructions, see Set up authentication for Text-to-Speech.
Perform synchronous single-speaker synthesis

Python
CURL


# google-cloud-texttospeech minimum version 2.29.0 is required.

import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize(prompt: str, text: str, output_filepath: str = "output.mp3"):
    """Synthesizes speech from the input text and saves it to an MP3 file.

    Args:
        prompt: Styling instructions on how to synthesize the content in
          the text field.
        text: The text to synthesize.
        output_filepath: The path to save the generated audio file.
          Defaults to "output.mp3".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)

    # Select the voice you want to use.
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="Charon",  # Example voice, adjust as needed
        model_name="gemini-2.5-pro-tts"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type.
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")
Perform synchronous multi-speaker synthesis with freeform text input

Note: Speaker aliases must consist solely of alphanumeric characters, excluding whitespace.
Python
CURL


# google-cloud-texttospeech minimum version 2.31.0 is required.

import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize_multispeaker_freeform(
    prompt: str,
    text: str,
    output_filepath: str = "output_non_turn_based.wav",
):
    """Synthesizes speech from non-turn-based input and saves it to a WAV file.

    Args:
        prompt: Styling instructions on how to synthesize the content in the
          text field.
        text: The text to synthesize, containing speaker aliases to indicate
          different speakers. Example: "Sam: Hi Bob!\nBob: Hi Sam!"
        output_filepath: The path to save the generated audio file. Defaults to
          "output_non_turn_based.wav".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)

    multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
        speaker_voice_configs=[
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker1",
                speaker_id="Kore",
            ),
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker2",
                speaker_id="Charon",
            ),
        ]
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        model_name="gemini-2.5-pro-tts",
        multi_speaker_voice_config=multi_speaker_voice_config,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")
Perform synchronous multi-speaker synthesis with structured text input

Multi-speaker with structured text input enables intelligent verbalization of text in a human-like way. For example, this kind of input is useful for addresses and dates. Freeform text input speaks the text exactly as written.

Note: The combined size of all lines of dialogue can be at most 900 bytes. While the total size of the prompt and dialogue can be up to 1,800 bytes, each prompt and dialogue field must be a maximum of 900 bytes. Speaker aliases must consist solely of alphanumeric characters, excluding whitespace.
Python
CURL


# google-cloud-texttospeech minimum version 2.31.0 is required.

import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize_multispeaker_structured(
    prompt: str,
    turns: list[texttospeech.MultiSpeakerMarkup.Turn],
    output_filepath: str = "output_turn_based.wav",
):
    """Synthesizes speech from turn-based input and saves it to a WAV file.

    Args:
        prompt: Styling instructions on how to synthesize the content in the
          text field.
        turns: A list of texttospeech.MultiSpeakerMarkup.Turn objects representing
          the dialogue turns.
        output_filepath: The path to save the generated audio file. Defaults to
          "output_turn_based.wav".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(
        multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=turns),
        prompt=prompt,
    )

    multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
        speaker_voice_configs=[
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker1",
                speaker_id="Kore",
            ),
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker2",
                speaker_id="Charon",
            ),
        ]
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        model_name="gemini-2.5-pro-tts",
        multi_speaker_voice_config=multi_speaker_voice_config,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")
Perform speech synthesis in Media Studio

You can use the Media Studio in the Google Google Cloud console to experiment with text-to-speech models. This provides a user interface for quickly generating, listening to synthesized audio and experimenting with different style instructions and parameters.

In the Google Google Cloud console, go to the Vertex AI Studio > Media Studio page.

Media Studio
Select Speech from the media drop-down.
In the text field, enter the text you want to synthesize into speech.
In the Settings pane, configure the following settings:

Model: Select the Text-to-Speech (TTS) model that you want to use, such as Gemini 2.5 Pro TTS. For more information about available models, see Text-to-Speech models.
Style instructions: Optional: Enter a text prompt that describes the selected speaking style, tone, and emotional delivery. This lets you to guide the model's performance beyond the default narration. For example: "Narrate in a calm, professional tone for a documentary.".
Language: Select the language and region of the input text. The model generates speech in the selected language and accent. For example, English (United States).
Voice: Choose a predefined voice for the narration. The list contains the available voices for the selected model and language, such as Acherner (Female).
Optional: Expand the Advanced options section to configure technical audio settings:

Audio encoding: Select the encoding for the output audio file. LINEAR16 is a lossless, uncompressed format suitable for high-quality audio processing. MULAW is also available for compressed audio output.
Audio sample rate: Select the sample rate in hertz (Hz). This determines the audio quality. Higher values like 44,100 Hz represent higher fidelity audio, equivalent to CD quality.
Speed: Adjust the speaking rate by moving the slider or entering a value. Values less than 1 slow down the speech, and values greater than 1 speed it up. The default is 1.
Volume gain (db): Adjust the volume of the output audio in decibels (dB). Positive values increase the volume, and negative values decrease it. The default is 0.
Click the send icon at the right of the text-box to generate the audio.
The generated audio appears in the media player. Click the play button to listen to the output. You can continue to adjust the settings, and generate new versions as needed.
Prompting Tips

Creating engaging and natural-sounding audio from text requires understanding the nuances of spoken language and translating them into script form. The following tips will help you craft scripts that sound authentic and capture the chosen tone.

The Three Levers of Speech Control

For the most predictable and nuanced results, ensure all three of the following components are consistent with your desired output.

Style Prompt The primary driver of the overall emotional tone and delivery. The prompt sets the context for the entire speech segment.

Example: You are an AI assistant speaking in a friendly and helpful tone.
Example: Narrate this in the calm, authoritative tone of a nature documentary narrator.
Text Content The semantic meaning of the words you are synthesizing. An evocative phrase that is emotionally consistent with the style prompt will produce much more reliable results than neutral text.

Good: A prompt for a scared tone works best with text like I think someone is in the house.
Less Effective: A prompt for a scared tone with text like The meeting is at 4 PM. will produce ambiguous results.
Markup Tags Bracketed tags like [sigh] are best used for injecting a specific, localized action or style modification, not for setting the overall tone. They work in concert with the style prompt and text content.

Markup Tag Guide

Our research shows that bracketed markup tags operate in one of three distinct modes. Understanding a tag's mode is key to using it effectively.

Mode 1: Non-Speech Sounds

The markup is replaced by an audible, non-speech vocalization (e.g., a sigh, a laugh). The tag itself is not spoken. These are excellent for adding realistic, human-like hesitations and reactions.

Tag	Behavior	Reliability	Guidance
[sigh]	Inserts a sigh sound.	High	The emotional quality of the sigh is influenced by the prompt.
[laughing]	Inserts a laugh.	High	For best results, use a specific prompt. e.g., a generic prompt may yield a laugh of shock, while "react with an amused laugh" creates a laugh of amusement.
[uhm]	Inserts a hesitation sound.	High	Useful for creating a more natural, conversational feel.
Mode 2: Style Modifiers

The markup is not spoken, but it modifies the delivery of the subsequent speech. The scope and duration of the modification can vary.

Tag	Behavior	Reliability	Guidance
[sarcasm]	Imparts a sarcastic tone on the subsequent phrase.	High	This tag is a powerful modifier. It demonstrates that abstract concepts can successfully steer the model's delivery.
[robotic]	Makes the subsequent speech sound robotic.	High	The effect can extend across an entire phrase. A supportive style prompt (e.g., "Say this in a robotic way") is still recommended for best results.
[shouting]	Increases the volume of the subsequent speech.	High	Most effective when paired with a matching style prompt (e.g., "Shout this next part") and text that implies yelling.
[whispering]	Decreases the volume of the subsequent speech.	High	Best results are achieved when the style prompt is also explicit (e.g., "now whisper this part as quietly as you can").
[extremely fast]	Increases the speed of the subsequent speech.	High	Ideal for disclaimers or fast-paced dialogue. Minimal prompt support needed.
Mode 3: Vocalized Markup (Adjectives)

The markup tag itself is spoken as a word, while also influencing the tone of the entire sentence. This behavior typically applies to emotional adjectives.

Warning: Because the tag itself is spoken, this mode is likely an undesired side effect for most use cases. Prefer using the Style Prompt to set these emotional tones instead.

Tag	Behavior	Reliability	Guidance
[scared]	The word "scared" is spoken, and the sentence adopts a scared tone.	High	Performance is highly dependent on text content. The phrase "I just heard a window break" produces a genuinely scared result. A neutral phrase produces a "spooky" but less authentic result.
[curious]	The word "curious" is spoken, and the sentence adopts a curious tone.	High	Use an inquisitive phrase to support the tag's intent.
[bored]	The word "bored" is spoken, and the sentence adopts a bored, monotone delivery.	High	Use with text that is mundane or repetitive for best effect.
Mode 4: Pacing and Pauses

These tags insert silence into the generated audio, giving you granular control over rhythm, timing, and pacing. Standard punctuation (commas, periods, semicolons) will also create natural pauses, but these tags offer more explicit control.

Tag	Behavior	Reliability	Guidance
[short pause]	Inserts a brief pause, similar to a comma (~250ms).	High	Use to separate clauses or list items for better clarity.
[medium pause]	Inserts a standard pause, similar to a sentence break (~500ms).	High	Effective for separating distinct sentences or thoughts.
[long pause]	Inserts a significant pause for dramatic effect (~1000ms+).	High	Use for dramatic timing. For example: "The answer is... [long pause] ...no." Avoid overuse, as it can sound unnatural.
Key Strategies for Reliable Results

Align All Three Levers For maximum predictability, ensure your Style Prompt, Text Content, and any Markup Tags are all semantically consistent and working toward the same goal.
Use Emotionally Rich Text Don't rely on prompts and tags alone. Give the model rich, descriptive text to work with. This is especially critical for nuanced emotions like sarcasm, fear, or excitement.
Write Specific, Detailed Prompts The more specific your style prompt, the more reliable the result. "React with an amused laugh" is better than just [laughing]. "Speak like a 1940s radio news announcer" is better than "Speak in an old-fashioned way."
Test and Verify New Tags The behavior of a new or untested tag is not always predictable. A tag you assume is a style modifier might be vocalized. Always test a new tag or prompt combination to confirm its behavior before deploying to production.

link to docs - https://cloud.google.com/text-to-speech/docs/gemini-tts