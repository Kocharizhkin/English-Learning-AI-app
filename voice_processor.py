from pydub import AudioSegment
import os

class AudioExercise():
    def __init__(self, filepath):
        if "ogg" in filepath:
            self.file = AudioSegment.from_file(filepath, format="ogg")
        if "wav" in filepath:
            self.file = AudioSegment.from_file(filepath, format="wav")
        self.filepath = filepath

    def slice_audio(self, audio, start_timing, end_timing):
        start_timing = int(start_timing * 1000)
        end_timing = int(end_timing * 1000)
        audio.file = audio.file[start_timing:end_timing]

        audio.filepath = audio.filepath.replace("generated", "sliced")
        if os.path.exists(audio.filepath):
            try:
                os.remove(audio.filepath)
                print(f"{audio.filepath} has been deleted.")
            except Exception as e:
                print(f"Error deleting {audio.filepath}. Reason: {e}")
        print(audio.filepath)
        str(audio.filepath)
        audio.file.export(audio.filepath, format='ogg', codec='libopus')
        return audio.filepath

    def wav_to_ogg(self, audio):
        audio.filepath = audio.filepath.replace("wav","ogg")
        audio.file.export(audio.filepath, format='ogg', codec='libopus')
        return audio.filepath