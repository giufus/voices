from threading import Thread
from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel
from datetime import datetime
from elevenlabs.client import ElevenLabs
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import os
import re

class MySettings(BaseModel):
    eleven_lab_apikey: str
    eleven_lab_voice_id: str
    eleven_lab_system_prompt: str


@plugin
def settings_model():
    return MySettings

def has_cyrillic(text):
    # Regular expression to match Cyrillic characters
    cyrillic_pattern = re.compile('[\u0400-\u04FF]+')
    
    # Check if any Cyrillic character is present in the text
    return bool(cyrillic_pattern.search(text))

def _process(text, filename, cat):
    try:
        language = detect(text)
    except LangDetectException:
        print("Error: Language detection failed. Defaulting to Italian.")
        language = 'it'
    
    try:
        settings = cat.mad_hatter.get_plugin().load_settings()
        eleven_lab_voice_id = settings.get("eleven_lab_voice_id")
        eleven_lab_apikey = settings.get("eleven_lab_apikey")
        client = ElevenLabs(api_key=eleven_lab_apikey)
    
        audio_iterator = client.text_to_speech.convert(
            voice_id=f"{eleven_lab_voice_id}",
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
        )
        
        # Save the audio bytes to a file
        with open(filename, 'wb') as audio_file:
            for audio_bytes in audio_iterator:
                audio_file.write(audio_bytes)

        # Generate the audio player HTML and send it as a chat message
        mycroft_audio_player = "<audio controls autoplay><source src='" + filename + "' type='audio/mp3'>Your browser does not support the audio element.</audio>"
        cat.send_ws_message(content=mycroft_audio_player, msg_type='chat')

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        #logging.error(f"Error occurred: {str(e)}")


@hook
def agent_prompt_prefix(prefix, cat):
    """Hook the main prompt prefix. """
    # Load the settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    prefix = settings.get("eleven_lab_system_prompt")
    return prefix


# Hook function that runs before sending a message
@hook
def before_cat_sends_message(final_output, cat):
    # Get the current date and time
    current_datetime = datetime.now()
    # Format the date and time to use as part of the filename
    formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")
    # Specify the folder path
    folder_path = "/admin/assets/voice"

    # Check if the folder exists, create it if not
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Construct the output file name with the formatted date and time
    output_filename = os.path.join(folder_path, f"voice_{formatted_datetime}.wav")

    # Get the message sent by LLM
    message = final_output["content"]
    
    tts_tread = Thread(target=_process, args=(message, output_filename, cat))
    tts_tread.start()

    # Return the final output text, leaving Mimic3 to build the audio file in the background
    return final_output
