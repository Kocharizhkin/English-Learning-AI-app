import openai
import base64

class OpenAiCall():
    openai.organization = "org-***"
    openai.api_key = "***"

    def get_difference(self, exercise_phrase, user_answer):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are a professional english teacher with a 15 years of experience. \
                Right now you are at the middle of the lesson where your student aka user trying to accomplish \
                the perfect pronunciation of the phrase '{exercise_phrase}', \
                Please check his answer and repeat the part of the phrase which he should try to pronounce again, \
                or just say 'next' if everything is fine, \
                but do not add anything else to the answer, just part of the phrase. Also do not forget about the context, \
                student should remember the minimum meaningful construction."},
                {"role": "user", "content": user_answer},
            ]
        )
        response = response = response.choices[0].message.content
        if response[0] == "'":
            response = response[1:]
        if response[-1] == "'":
            response = response[:-1]
        response = response.split(" ")
        if "Next" in response or "next" in response:
            return None
        print(response)
        first_word = response[0].lower()
        last_word = response[-1].lower()
        return [first_word, last_word]


    async def get_context(self, word_or_prase):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a professional english teacher with a 15 years of experience. \
                Right now you are at the middle of the lesson where your student aka user trying to learn new words, so be as much specific as possible and dont write useless words.\
                You need to give user the example ussage of the word in different context but dont write anything else, 2-3 examples is the only information user whant from you"},
                {"role": "user", "content": word_or_prase},
            ]
        )
        response = response = response.choices[0].message.content

        return response

    async def chat(self, user_message, summary):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Given the summary of previous conversation with user, please provide a friendly response to the user's message. summary: {summary}"},
                {"role": "user", "content": user_message},
            ]
        )
        response = response.choices[0].message.content


        return response
    
    async def summarise(self, summary, new_info):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": f'Given the current summary: "{summary}", and the latest message: "{new_info}", update the summary to \
                    incorporate the information from the latest message. Ensure that user-related information such as names, ages, \
                    and other personal details present in the summary are retained and emphasized in the updated summary.'
                }   
            ]
        )
        response = response = response.choices[0].message.content
        return response
    
    async def generate_image(self, prompt, filename):
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json"
        )

        image_data = response.data[0].b64_json

        # Assuming the filename includes the path where the file should be saved
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(image_data))