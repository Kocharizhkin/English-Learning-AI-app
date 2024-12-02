from quart import Quart, request, jsonify
from quart_cors import cors
import re
import string
import asyncio
import hashlib
from datetime import datetime
import os
from db_connection import db_operations
from vocabulary import Vocabulary
from userOperations import User
from lovoAPIcalls import TextToSpeech
from openAiAPIcalls import OpenAiCall
from translator import Translate
from chat import ChatWithGPT
from calendarProgress import ProgressInCalendar
from firebase import Firebase

db_operations = db_operations()
vocabulary = Vocabulary()
user_operations = User()
tts = TextToSpeech()
openAI = OpenAiCall()
translate = Translate()
chat = ChatWithGPT()
performance = ProgressInCalendar()
firebase = Firebase()

app = Quart(__name__)
app = cors(app, allow_origin="*")

@app.route('/chat', methods=['POST'])
async def handle_chat():
    data = await request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 400

    user_message = data.get('message')
    user_id = data.get('user')

    if user_message is None:
        return jsonify({'error': 'Message is required'}), 400
    if user_id is None:
        return jsonify({'error': 'User_id is required'}), 400
    
    summary = await chat.get_summary(user_id)
    print("Got summary")
    # Respond to the user immediately
    response = await openAI.chat(user_message, summary)  # Assuming this call is fast
    print("Got responce")
    # Defer database addition and summary creation
    asyncio.create_task(handle_post_chat(user_id, user_message, response))
    print("Task created")
    firebase.add(response, user_id)
    return jsonify({'message': 'Response sent'}), 200

async def handle_post_chat(user_id, user_message, response):
    success = await chat.add_to_db(user_id, user_message, from_bot=False)  # Make sure this is async
    if success:
        print("Message added successfully!")
    else:
        print("Failed to add the message.")

    summary = await chat.create_summary(user_id)  # This should be async too

    success = await chat.add_to_db(user_id, response, from_bot=True)

    print(f"Updated Summary: {summary}")

@app.route('/chat/<int:user_id>', methods=['GET'])
async def get_messages_history(user_id):

    messages = await chat.get_messages_history(user_id)

    print(messages)

    return jsonify(messages), 200








@app.route('/signup', methods=['POST'])
async def signup():
    data = await request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    new_user = User(email=email, password=password)

    session = await new_user.get_session()
    await new_user.add_user(session, new_user)

    return jsonify({'message': 'User created successfully'}), 200

@app.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    session = await user_operations.get_session()
    user_exists, user = await user_operations.check_credentials(session, email=email, hashed_password=password)
    if user_exists:
        return jsonify({'message': 'Logged in successfully', 'user_info': await user.to_dict()}), 200
    else:
        return jsonify({'error': 'Password or login is incorrect'}), 400
    
@app.route('/user/<int:user_id>', methods=['PUT'])
async def update_user(user_id):
    data = await request.json

    # 2. Create an instance of the User class
    updated_user = User(
        id=user_id,
        email=data['email'],
        password="",  # you should not store the password in plaintext
        level=data.get('level', 0),  # use the default if 'level' is not provided
        last_lesson_id=data.get('last_lesson_id', 0),
        fullname=data['fullName'],
        username=data['username'],
        profilepicurl=data['profilePicUrl']
    )
    await user_operations.update_user(updated_user)
    return jsonify({'message': 'Updated successfully'}), 200

@app.route('/performance/<int:user_id>', methods=['GET'])
async def get_performance(user_id):
    session = await performance.get_session()
    entries = await performance.get(session, user_id)
    return jsonify(entries)








@app.route('/vocabulary', methods=['POST'])
async def add_entry():
    data = await request.json
    user_id = data['user_id']
    phrase = data['phrase']
    translation = data.get('translation')  # This can be optional

    if translation == None:
        translation = await translate.language_detector(phrase)

    if bool(re.search('[\u0400-\u04FF]', phrase)): # bool: True if the string contains Cyrillic symbols, False otherwise.
        phrase, translation = translation, phrase

    # Get hash based filepath
    hash_value = phrase.replace(" ", "").lower()
    hash_value = hash_value.translate(str.maketrans('', '', string.punctuation))
    hash_value = hashlib.md5(hash_value.encode()).hexdigest()  # Create a hash from the phrase
    image_filepath = f"static/files/pictures/vocabulary/{hash_value}.png"
    try:
        await openAI.generate_image(phrase, image_filepath)
    except:
        image_filepath = "static/files/pictures/vocabulary/playButton.png"

    session = await vocabulary.get_session()
    result = await vocabulary.add_entry(session, user_id, phrase, translation, image_filepath)
    return jsonify(result), 201

@app.route('/vocabulary/<int:user_id>', methods=['GET'])
async def get_entries(user_id):
    session = await vocabulary.get_session()
    entries = await vocabulary.get_entries_by_user_id(session, user_id)
    print(entries)
    return jsonify(entries)

@app.route('/vocabulary/<int:entry_id>', methods=['DELETE'])
async def delete_entry(entry_id):
    session = await vocabulary.get_session()
    success = await vocabulary.delete_entry(session, entry_id)
    if success:
        return jsonify({'message': 'Deleted successfully'}), 200
    else:
        return jsonify({'message': 'Entry not found'}), 404
    




@app.route('/translate', methods=['POST'])
async def handle_translate():
    data = await request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 400
    user_message = data.get('text')
    if user_message is None:
        return jsonify({'error': 'text is required'}), 400
    response = await translate.language_detector(user_message)

    return jsonify({'translation': response})

@app.route('/get_audio', methods=['POST'])
async def get_audio_endpoint():
    phrase = (await request.form).get('phrase')  # Change 'text' to 'phrase'
    hash_value = hashlib.md5(phrase.encode()).hexdigest()  # Create a hash from the phrase
    filepath = f"static/files/audio/vocabulary/{hash_value}.wav"

    if not os.path.exists(filepath):
        tts.get_audio(phrase, filepath)  # Assuming this function saves the audio file

    # Construct the URL of the audio file
    file_url = f"https://englishcringe.com/api/{filepath}"

    return jsonify({'audioUrl': file_url})

if __name__ == "__main__":
    # Run the app on port 80
    app.run(host='0.0.0.0', port=5000, debug=True)