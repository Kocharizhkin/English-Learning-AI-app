from deepgram import Deepgram
import asyncio, json

class DeepgramCall():

    # Your Deepgram API Key

    # Location of the file you want to transcribe. Should include filename and extension.
    # Example of a local file: ../../Audio/life-moves-pretty-fast.wav
    # Example of a remote file: https://static.deepgram.com/examples/interview_speech-analytics.wav

    # Mimetype for the file you want to transcribe
    # Include this line only if transcribing a local file
    # Example: audio/wav

    async def main(self, FILE):
        DEEPGRAM_API_KEY = '***'
        MIMETYPE = 'audio/ogg'
        # Initialize the Deepgram SDK
        deepgram = Deepgram(DEEPGRAM_API_KEY)

        # Check whether requested file is local or remote, and prepare source
        if FILE.startswith('http'):
            # file is remote
            # Set the source
            source = {
            'url': FILE
            }
        else:
            # file is local
            # Open the audio file
            audio = open(FILE, 'rb')

            # Set the source
            source = {
            'buffer': audio,
            'mimetype': MIMETYPE
            }

        # Send the audio to Deepgram and get the response
        response = await asyncio.create_task(
            deepgram.transcription.prerecorded(
            source,
            {
                'smart_format': True,
                'model': 'nova',
            }
            )
        )

        # Write the response to the console
        return response

    # Write only the transcript to the console
    #print(response["results"]["channels"][0]["alternatives"][0]["transcript"])
    async def get_transcript(self, file):
        try:
            # If running in a Jupyter notebook, Jupyter is already running an event loop, so run main with this line instead:
            #await main()
            responce = await self.main(file)
            return responce["results"]['channels'][0]['alternatives'][0]['transcript']
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            line_number = exception_traceback.tb_lineno
            print(f'line {line_number}: {exception_type} - {e}')

    async def get_timings(self, file, first_word, last_word):
        try:
            # If running in a Jupyter notebook, Jupyter is already running an event loop, so run main with this line instead:
            #await main()
            responce = await self.main(file)
            words_info = responce["results"]['channels'][0]['alternatives'][0]['words']
            for i in words_info:
                print(i)
                if i['word'] == first_word or i['punctuated_word'] == first_word:
                    start_timing = float(i['start'])
                elif i['word'] == last_word or i['punctuated_word'] == last_word:
                    end_timing = float(i['end'])
                else:
                    start_timing = float(words_info[0]['start'])
                    end_timing = float(words_info[-1]['end'])
            return start_timing, end_timing
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            line_number = exception_traceback.tb_lineno
            print(f'line {line_number}: {exception_type} - {e}')
