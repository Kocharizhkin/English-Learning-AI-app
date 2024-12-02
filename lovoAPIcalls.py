import requests
import json

class TextToSpeech():

    def get_audio(self, text, filename):
        self.payload = { "speed": 1, "text": text,  "speaker": "63b407b6241a82001d51b99b"}
        self.headers = {
            "accept": "application/json",
            "X-API-KEY": "***",
        }

        response = requests.post("https://api.genny.lovo.ai/api/v1/tts/sync", json=self.payload, headers=self.headers)

        response = response.json()

        print("\n\n\n\n")
        print(response)
        print("\n\n\n\n")
        print("\n\n\n\n")
        print(response["data"][0])
        print("\n\n\n\n")
        url = response["data"][0]["urls"][0]

        self.download_file(url, filename)

        return filename

    def download_file(self, url, local_filename):
        # Stream the content, useful for large files
        response = requests.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    f.write(chunk)
        return local_filename
