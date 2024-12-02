import asyncpg
from openAiAPIcalls import OpenAiCall
from datetime import datetime

# Assuming your OpenAiCall's summarise function can be awaited.
openAI = OpenAiCall()

class ChatWithGPT():

    async def get_or_create_summary_id(self, user_id):
        # Establish a connection to the database
        conn = await asyncpg.connect(
            user='ege_bot', 
            password='ege_bot', 
            database='ege_bot', 
            host='localhost'
        )
        # Check if a summary_id exists for the given user_id
        row = await conn.fetchrow(
            "SELECT summary_id FROM messages WHERE user_id = $1 AND from_bot = FALSE LIMIT 1;",
            user_id
        )
        if row:
            summary_id = row['summary_id']
        else:
            # If no summary_id exists for the user, find the last summary_id and increment it
            summary_id = await conn.fetchval(
                "SELECT COALESCE(MAX(id), 0) + 1 FROM summaries;"
            )
            await conn.execute(
                "INSERT INTO summaries (id) VALUES ($1);",
                summary_id
            )

        # Close the connection
        await conn.close()

        return summary_id

    async def add_to_db(self, user_id, text, from_bot):
        # Get or create the summary_id for the user
        summary_id = await self.get_or_create_summary_id(user_id)

        # Establish a connection to the database
        conn = await asyncpg.connect(
            user='ege_bot', 
            password='ege_bot', 
            database='ege_bot', 
            host='localhost'
        )

        # SQL query to insert the message into the messages table
        try:
            await conn.execute(
                "INSERT INTO messages (user_id, message, time, summary_id, from_bot) VALUES ($1, $2, NOW(), $3, $4);",
                user_id, text, summary_id, from_bot
            )
            result = True
        except Exception as e:
            print(f"Error: {e}")
            result = False
        finally:
            await conn.close()

        return result

    async def create_summary(self, user_id):
        # Establish a connection to the database
        conn = await asyncpg.connect(
            user='ege_bot', 
            password='ege_bot', 
            database='ege_bot', 
            host='localhost'
        )

        # Retrieve the last message for the specified user_id
        message = await conn.fetchval(
            "SELECT message FROM messages WHERE user_id = $1 AND from_bot = FALSE ORDER BY time DESC LIMIT 1;",
            user_id
        )

        # Retrieve the summary for this user
        summary_id = await self.get_or_create_summary_id(user_id)
        summary = await conn.fetchval(
            "SELECT text FROM summaries WHERE id = $1;",
            summary_id
        )
        summary = summary if summary else ""

        # Call the placeholder function with the message and summary
        updated_summary = await openAI.summarise(summary, message)

        # Update the summary field in the summaries table
        await conn.execute(
            "UPDATE summaries SET text = $1 WHERE id = $2;",
            updated_summary, summary_id
        )

        # Close the connection
        await conn.close()

        return updated_summary
    
    async def get_summary(self, user_id):
        # Establish a connection to the database
        conn = await asyncpg.connect(
            user='ege_bot', 
            password='ege_bot', 
            database='ege_bot', 
            host='localhost'
        )

        # Retrieve the summary for this user
        summary_id = await self.get_or_create_summary_id(user_id)
        summary = await conn.fetchval(
            "SELECT text FROM summaries WHERE id = $1;",
            summary_id
        )
        summary = summary if summary else ""

        # Close the connection
        await conn.close()

        return summary
    
    async def get_messages_history(self, user_id):
        conn = await asyncpg.connect(
            user='ege_bot', 
            password='ege_bot', 
            database='ege_bot', 
            host='localhost'
        )

        messages = await conn.fetch(
            "SELECT * FROM messages WHERE user_id = $1 ORDER BY time DESC;",
            user_id
        )

        messages = [dict(row) for row in messages]

        for row in messages:
            row['time'] = row['time'].strftime("%Y-%m-%d, %H:%M:%S").replace(',', '')

        return messages

