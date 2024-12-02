from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, Job
import os

from lovoAPIcalls import TextToSpeech
from DeepgramAPIcalls import DeepgramCall
from openAiAPIcalls import OpenAiCall
from datetime import datetime
from userOperations import User
from voice_processor import AudioExercise
from vocabulary import Vocabulary

deepgram = DeepgramCall()
openAI = OpenAiCall()
tts = TextToSpeech()
user_operations = User()
vocabulary = Vocabulary()

class Lessons():
    def __init__(self):
        self.user_data = User()
        self.test_lesson = [
        ["", 'callback'],
        ["", 'callback'],
        ["Запиши аудио-сообщение 'Where are you?'", "Where are you?"],
        ["", "I'm in {translation_receiver}."],
        ["", "Where is your family?"],
        ["", "My family is in Spain"],
        ["", "Do you have a cat?"],
        ["", "No, I don't have a cat, but I have a dog"],
        ["", "I have a laptop"],
        ["", "I have a house."],
        ["", "I have three best friends"],
        ["", "I don't have problems"],
        ["", "I don't have any friends."],
        ["", "Do you have brothers or sisters?"],
        ["", "Do you have a favourite book"],
        ["", "Yes, my favourite book is three musketeers"],
        ["Congrats, youve finished the lesson!", ""]
        ]

    async def lesson_creator(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = await user_operations.get_user_data(update)
        user_data.checkpoint = "lesson"
        user_data.audio_message_data = {'text': "", "chunk": 0, "wrong_answers_strick": 0}
        await user_operations.update_user(user_data)
        await self.send_audio_text_chunk(update, context, self.test_lesson)

    async def lesson_reminder(self, context: ContextTypes.user_data):
        chat_id = context.user_data['chat_id']
        await context.bot.send_message(chat_id=chat_id, text="Привет! Пришло время для следующего увлекательного урока.\nГотов?\nТыкай /lesson")

    async def send_audio_text_chunk(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text_to_send, user_input={}):
        user_data = await user_operations.get_user_data(update)
        print(user_data.audio_message_data)
        chunk = user_data.audio_message_data["chunk"]
        wrong_answers_starick = user_data.audio_message_data["wrong_answers_strick"]
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=text_to_send[chunk][0].format(username=user_data.first_name, translation_receiver=user_input))
        await context.bot.send_video_note(chat_id=update.effective_chat.id, video_note=open(f"static/files/video/messages/{chunk}.mp4", 'rb'), protect_content=True, \
            reply_markup=None if text_to_send[chunk][1] != 'callback' else InlineKeyboardMarkup([[InlineKeyboardButton("Дальше", callback_data="lesson_next_question")]]))
        if text_to_send[chunk][0] != '':
                await context.bot.send_message(chat_id=update.effective_chat.id, text=text_to_send[chunk][0]) 
        '''
        if text_to_send[chunk][1] != "":
            if os.path.exists("static/files/audio/generated/"+str(chunk)+".ogg"):
                audio_filename = "static/files/audio/generated/"+str(chunk)+".ogg"
            else:
                audio_filename = tts.get_audio(text_to_send[chunk][1].format(username=user_data.first_name, translation_receiver=user_input), "static/files/audio/generated/"+str(user_data.id)+".wav")
                audioExercise = AudioExercise(audio_filename)
                audio_filename  = audioExercise.wav_to_ogg(audioExercise)
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_filename, 'rb'))
            
            user_data.audio_message_data = {'text': text_to_send[chunk][1].format(username=user_data.first_name, translation_receiver=user_input), "chunk": chunk, "file": audio_filename, "wrong_answers_strick": 0}
            await user_operations.update_user(user_data)
        else:
            user_data.audio_message_data = {'text': "", "chunk": chunk, "wrong_answers_strick": 0}
            await user_operations.update_user(user_data)
        '''
        if text_to_send[chunk][1] == '':
            print('\n\n\n\n')
            print('no user input expecting, next chunk', chunk)
            user_data.audio_message_data = {'text': '', "chunk": chunk+1, "wrong_answers_strick": 0}
            await user_operations.update_user(user_data)
            await self.send_audio_text_chunk(update, context, self.test_lesson)
            return
        user_data.audio_message_data = {'text': text_to_send[chunk][1].format(username=user_data.first_name, translation_receiver=user_input['text'][1]), "chunk": chunk, "file": "static/files/audio/generated/"+str(chunk)+".ogg", "wrong_answers_strick": 0}
        if user_input != {}:
            vocabulary.add(user_data.id, user_input)
        await user_operations.update_user(user_data)
        return text_to_send

    async def audio_message_match_validation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = await user_operations.get_user_data(update)
        new_file = await context.bot.get_file(update.message.voice.file_id)
        user_audio_filepath = f"static/files/audio/from_user/{user_data.id}.ogg"
        if user_data.checkpoint == "lesson":
            chunk = user_data.audio_message_data["chunk"]
        await new_file.download_to_drive(custom_path=user_audio_filepath)
        user_audio_transcript = await deepgram.get_transcript(user_audio_filepath)
        if user_data.audio_message_data['text'] != "":
            initial_audio_transcript = user_data.audio_message_data['text']
            await vocabulary.add(user_data.id, {"text": [initial_audio_transcript]})
            repeat_checkpoints = openAI.get_difference(initial_audio_transcript, user_audio_transcript)
            if repeat_checkpoints == None:
                if user_data.checkpoint == "lesson":
                    user_data.audio_message_data = {'text': None, "chunk": chunk+1, "wrong_answers_strick": 0}
                    await user_operations.update_user(user_data)
                    await self.send_audio_text_chunk(update, context, self.test_lesson)
                    return
                elif user_data.checkpoint == "start":
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Отлично, вы произнесли 'Where")
            else:
                user_data.audio_message_data["wrong_answers_strick"] += 1
                if user_data.audio_message_data["wrong_answers_strick"] == 2:
                    user_data.audio_message_data = {'text': None, "chunk": chunk+1, "wrong_answers_strick": 0}
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Its okay if you can't handle this, lets just continue, we will return to this later")
                    await user_operations.update_user(user_data)
                    if user_data.checkpoint == "lesson":
                        await self.send_audio_text_chunk(update, context, self.test_lesson)
                        return
                lesson_audio_filepath = user_data.audio_message_data['file']
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Повтори еще раз")
                #await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(lesson_audio_filepath, 'rb'))
                await user_operations.update_user(user_data)
                return
                '''
                lesson_audio_filepath = user_data.audio_message_data['file']
                repeat_start_timing, repeat_end_timing = await deepgram.get_timings(lesson_audio_filepath, repeat_checkpoints[0], repeat_checkpoints[1])
                if repeat_start_timing == None or repeat_end_timing == None:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Повтори еще раз")
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(lesson_audio_filepath, 'rb'))
                    await user_operations.update_user(user_data)
                    return
                audioExercise = AudioExercise(lesson_audio_filepath)
                repeat_filepath = audioExercise.slice_audio(audioExercise, repeat_start_timing, repeat_end_timing)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Повтори еще раз")
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(repeat_filepath, 'rb'))
                await user_operations.update_user(user_data)
                '''
            
    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = await user_operations.get_user_data(update)
        query = update.callback_query
        if query.data == "lesson_next_question":
            chunk = user_data.audio_message_data["chunk"]
            user_data.audio_message_data = {'text': None, "chunk": chunk+1, "wrong_answers_strick": 0}
            await user_operations.update_user(user_data)
            await self.send_audio_text_chunk(update, context, self.test_lesson)




