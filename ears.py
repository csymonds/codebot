import sys
from pynput.keyboard import Key, KeyCode, Listener
import sounddevice as sd
import numpy as np
from queue import Queue
import threading
from transformers import WhisperProcessor, WhisperForConditionalGeneration

# control state of app
app_running = True

# listening state
listening=False

# push to talk key
ptt_key = 'z'

# Set the sampling rate (number of samples per second)
sr = 16000

# set a signal floor to identify "silence"
signal_floor = 0.003

# Create an output array to store the recorded audio
out = np.zeros((0, 1))

# Create a processing queue
q = Queue()

# let's track how many blocks of silence we hear
silence_count = 0

def startListening():
    global q, out, listening
     
    with sd.Stream(channels=1, callback=audio_callback, blocksize=2048, samplerate=sr):
        print("starting input stream with devices: " + str(sd.default.device))
        while listening:
            pass
        
    # send the last chunk to the processing queue
    q.put(out)
    # Signal the processing thread to stop
    q.put(None)
    # Create a new output array
    print("resetting out array")
    out = np.zeros((0, 1))
    


def on_press(key):
    global listening, startListening, ptt_key
    sys.stdout.flush()
    try:
        if listening==False and str(key.char) == ptt_key:
            #print('alphanumeric key {0} pressed'.format(
            #key.char))
            listening=True
            # Start the processing thread
            listening_thread = threading.Thread(target=startListening)
            listening_thread.start()
    except AttributeError:
        sys.stdout.flush()
        #print('special key {0} pressed'.format(
            #key))


def on_release(key):
    global listening, app_running, ptt_key
    sys.stdout.flush()
    #print('{0} release'.format(key))
    if key == Key.esc:     # Stop listener
        print("Terminating")
        app_running = False
        return False
    
    if key == KeyCode.from_char(ptt_key):
        #print("Listening stopped")
        listening=False


# Define a callback function to handle incoming audio
def audio_callback(indata, outdata, frames, time, status):
    global out, q, silence_count, signal_floor, listening

    data = indata.T.reshape(-1,)

    if status:
        print(status, file=sys.stderr)
    
    if len(out) == 0:
        out = data
    else:
        out = np.concatenate((out, data))
    

    
# Define a processing function to process the output arrays from the queue
def process_output(q):
    global listening, app_running, sr
    processor = WhisperProcessor.from_pretrained("openai/whisper-base.en")
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base.en")
    print("Model loaded")
    while app_running:
        while listening:
            # Wait for an output array to be added to the queue
            sample = q.get()
            if sample is None:
                print("no sample received, stopping")
                # If the output array is None, back to top
                break
            if len(sample) == 0:
                continue
            # Get the input features from the output array using the WhisperProcessor
            #print(sample)
            #sd.play(sample, sr)
            input_features = processor(sample, sampling_rate=sr, return_tensors="pt").input_features
            predicted_ids = model.generate(input_features)
            transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            # somehow gibberish or random noise cause it to output "you" or "You"
            if str(transcription[0].strip().lower())  != "you":
                print("**transcription result: " + str(transcription[0]))

# Start the processing thread
processing_thread = threading.Thread(target=process_output, args=(q,))
processing_thread.start()
print("processing thread started")

print("Press stream key to start listening")

with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

# Wait for the processing thread to stop
processing_thread.join()