This is a chatGPT bot with long term memory using Pinecone

It also uses the Whisper API to do speech to text


## Setup

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/)
    

    You will need to create an account on [Pinecone and follow their registration procedures](https://www.pinecone.io/).

    Pinecone also has [documentation you can follow for integration with OpenAI](https://docs.pinecone.io/docs/openai) if you want to try your own.

    Documentation for the [OpenAI chatGPT API is available here.](https://platform.openai.com/docs/libraries)

2. Clone this repository

   ```bash
   $ git clone git@github.com:csymonds/codebot.git
   ```

3. Navigate into the project directory
   
   ```bash
   $ cd codebot
   ```
## Virtual environment and dependency installation
4. Virtualize (Note: Windows users will see `venv/Scripts/activate`)
   ```
   $ python -m venv venv
   $ . venv/bin/activate
   ```

5. Install the library dependencies
   ```bash
   $ pip3 install -r requirements.txt
   ```

   In addition to the library dependencies, there are some additional runtime dependencies like pytorch
   
   The below install version assumes you have CUDA 11.7 installed. 
   
   The [necessary CUDA installers are found here.](https://developer.nvidia.com/cuda-zone)
   
   Additional [PyTorch installers are found here.](https://pytorch.org/get-started/locally/)

   ```bash
   $ pip3 install pynput torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu117
   ```

6. Add keys

   Step 1: Make a copy of the example environment variables files

   ```bash
   $ cp example_key_openai.txt key_openai.txt
   $ cp example_key_pinecone.txt key_pinecone.txt
   ```

   Step 2: Copy in your key to the respective file

      Add your [OpenAI API key](https://beta.openai.com/account/api-keys) to the newly created `key_openai.txt` file
    
      Add your [Pinecone API key](https://docs.pinecone.io/docs/quickstart#2-get-and-verify-your-pinecone-api-key) to the newly created `key_pinecone.txt` file

7. Deactivate
   ```
   $ deactivate
   ```


Tips: sounddevice defaults to your default communications devices in order to record/playback 

To check/modify what those defaults are, use

   ```bash
   python -m sounddevice
   ```

PLEASE NOTE: Windows Defender will have an issue with the chat.py file because of the pynput library. It considers the use of this library to constitute a keylogger and will quarantine the file even before you run it. Therefore if you would like to run this file, once Windows Defender quarantines the file, you will need to 

1. tell Windows Defender to allow the python file and
2. Look in your Protection History, find the threat action, and tell it to restore the file

Finally: You will get a warning about model parameters missing when you run this. It is harmless, and can be suppressed by setting the `ignore_warnings` parameter to `True`