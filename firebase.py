import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

# Initialize the Firebase admin SDK
cred = credentials.Certificate('***')
firebase_admin.initialize_app(cred, {
    'databaseURL': '***'
})

class Firebase():

    def add(self, message, user_id):
        # Create a reference to the 'messages' node in your Realtime Database
        messages_ref = db.reference(f'chat/{user_id}')

        # Create a new message entry
        new_message_ref = messages_ref.push()
        new_message_ref.set({
            'message': message,
            'userId': user_id,
            'timestamp': datetime.now().isoformat(),  # Storing the current timestamp in ISO 8601 format
            'isBot': True
        })