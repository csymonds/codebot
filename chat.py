import sys
import warnings
import brain
import utils
import keyboard
import sounddevice as sd
import numpy as np
from queue import Queue
import threading
from transformers import WhisperProcessor, WhisperForConditionalGeneration

# control state of app
app_running = True
ignore_warnings = False

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
        #print("starting input stream with devices: " + str(sd.default.device))
        while listening:
            pass
        
    # send the last chunk to the processing queue
    q.put(out)
    # Signal the processing thread to stop
    q.put(None)
    # Create a new output array
    #print("resetting out array")
    out = np.zeros((0, 1))
    


def on_key_event(key):
    global listening, startListening, ptt_key, app_running
    sys.stdout.flush()
    if (listening==False and key.name == ptt_key and key.event_type == keyboard.KEY_DOWN):
        listening=True
        listening_thread = threading.Thread(target=startListening)
        listening_thread.start()

    if (key.name == ptt_key and key.event_type == keyboard.KEY_UP):
        listening=False
    elif (key.name == 'esc' and key.event_type == keyboard.KEY_UP):
        app_running=False


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
    print("\nHold " + ptt_key + " key to talk to CodeBot")
    print("Press ESC any time to quit\n\nUSER: ")
    while app_running:
        while listening:
            # Wait for an output array to be added to the queue
            sample = q.get()
            if sample is None:
                # If the output array is None, back to top
                break
            if len(sample) == 0:
                continue
            # Get the input features from the output array using the WhisperProcessor
            #sd.play(sample, sr)
            input_features = processor(sample, sampling_rate=sr, return_tensors="pt").input_features
            predicted_ids = model.generate(input_features)
            transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            # somehow gibberish or random noise cause it to output "you" or "You"
            if str(transcription[0].strip().lower())  != "you":
                print(str(transcription[0]))
                brain.chat(str(transcription[0]))
                print("\nUSER: ")

# suppress warning from transformers
if ignore_warnings:
    warnings.filterwarnings("ignore")

#clear the screen
utils.clear()

# Start the processing thread
processing_thread = threading.Thread(target=process_output, args=(q,))
processing_thread.start()
#print("processing thread started")

brain.init()
print("Welcome to CodeBot!")

keyboard.hook(on_key_event, suppress=False)

keyboard.wait('esc')

# Wait for the processing thread to stop
processing_thread.join()