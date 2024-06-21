from flask import Flask, request, render_template, send_from_directory
import os
import wave
import json
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Load the Vosk model
model_path = "models/vosk-model-small-en-us-0.15"
if not os.path.exists(model_path):
    raise ValueError("Model path does not exist")
model = Model(model_path)

def convert_to_wav(input_path, output_path):
    ext = os.path.splitext(input_path)[1].lower()
    if ext == '.mp3':
        audio = AudioSegment.from_mp3(input_path)
    elif ext == '.mp4':
        video = VideoFileClip(input_path)
        video.audio.write_audiofile(output_path, codec='pcm_s16le')
        audio = AudioSegment.from_wav(output_path)
    elif ext == '.wav':
        audio = AudioSegment.from_wav(input_path)
    else:
        raise ValueError("Unsupported file format")
    
    # Ensure the audio is in mono and in PCM format
    audio = audio.set_channels(1)  # Convert to mono
    audio = audio.set_frame_rate(16000)  # Set sample rate to 16000
    audio.export(output_path, format="wav", parameters=["-acodec", "pcm_s16le"])  # Ensure PCM format

def recognize_speech(audio_file_path):
    try:
        wf = wave.open(audio_file_path, "rb")
    except wave.Error as e:
        raise ValueError("Invalid WAV file: " + str(e))
    
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        raise ValueError("Audio file must be WAV format mono PCM.")
    
    rec = KaldiRecognizer(model, wf.getframerate())
    final_result = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            final_result.append(res.get('text', ''))
        else:
            res = json.loads(rec.PartialResult())
            # Optionally, handle partial results here if needed
    final_result.append(json.loads(rec.FinalResult()).get('text', ''))
    return ' '.join([text for text in final_result if text])  # Filter out any empty strings

@app.route('/')
def index():
    return render_template('index.html')
    return jsonify({"message": "Hello from Flask on Render!"})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error="No file part")
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error="No selected file")
    if file:
        input_path = os.path.join("uploads", file.filename)
        file.save(input_path)
        output_path = os.path.join("uploads", "converted.wav")
        transcript_path = os.path.join("uploads", "transcript.txt")
        try:
            convert_to_wav(input_path, output_path)
            transcription_text = recognize_speech(output_path)
            
            # Save the transcript to a text file
            with open(transcript_path, 'w') as f:
                f.write(transcription_text)
                
            return render_template('index.html', transcription=transcription_text, transcript_file='transcript.txt')
        except ValueError as e:
            return render_template('index.html', error=str(e))
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
