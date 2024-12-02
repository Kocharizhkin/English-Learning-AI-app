import nlpcloud
import re
import time 
from openAiAPIcalls import OpenAiCall
from lovoAPIcalls import TextToSpeech
from voice_processor import AudioExercise
from userOperations import User
from vocabulary import Vocabulary

vocabulary = Vocabulary()
user_operations = User()
openAI = OpenAiCall()
tts = TextToSpeech()

class Translate():

    async def from_eng_to_rus(self, text_to_translate):
        client = nlpcloud.Client("nllb-200-3-3b", "***")
        # Returns a json object.
        response = client.translation(text_to_translate, source='eng_Latn', target='rus_Cyrl')
        return response["translation_text"]

    async def from_rus_to_eng(self, text_to_translate):
        client = nlpcloud.Client("nllb-200-3-3b", "***")
        # Returns a json object.
        response = client.translation(text_to_translate, source='rus_Cyrl', target='eng_Latn')
        return response["translation_text"]

    async def language_detector(self, text_to_detect): 
        if not bool(re.search('[\u0400-\u04FF]', text_to_detect)): # bool: True if the string contains Cyrillic symbols, False otherwise.
            translated = await self.from_eng_to_rus(text_to_detect)
            return translated
        else:
            translated = await self.from_rus_to_eng(text_to_detect)
            return translated
