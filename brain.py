import os
import openai
import pinecone
import re
from time import time,sleep
from uuid import uuid4
import utils

# Key files:
openAIKeyFile = 'key_openai.txt'
pineconeKeyFile = 'key_pinecone.txt'

#Pinecone Params
pineconeEnvironment = 'us-east1-gcp'
pineconeIndex = 'codebot'

# GPT Params
gptModel = 'text-davinci-003'
modelTemp = 0.6
tokens = 600
stop = ['USER:', 'CODEBOT:']





def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII',errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content,engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector



def gpt3_completion(prompt):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                model=gptModel,
                prompt=prompt,
                max_tokens=tokens,
                temperature=modelTemp,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            text = re.sub('[\r\n]+', '\n', text)
            text = re.sub('[\t ]+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            if not os.path.exists('gpt3_logs'):
                os.makedirs('gpt3_logs')
            utils.save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)


def load_conversation(results):
    result = list()
    for m in results['matches']:
        info = utils.load_json('cortex/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()


def init():
    global convo_length, vdb
    convo_length = 30
    openai.api_key = utils.open_file(openAIKeyFile)
    pinecone.init(api_key=utils.open_file(pineconeKeyFile), environment=pineconeEnvironment)
    vdb = pinecone.Index(pineconeIndex)

def chat(a):
    global convo_length, vdb
    payload = list()
    timestamp = time()
    timestring = utils.timestamp_to_datetime(timestamp)
    #message = '%s: %s - %s' % ('USER', timestring, a)
    message = a
    vector = gpt3_embedding(message)
    unique_id = str(uuid4())
    metadata = {'speaker': 'USER', 'time': timestamp, 'message': message, 'timestring': timestring, 'uuid': unique_id}
    utils.save_json('cortex/%s.json' % unique_id, metadata)
    payload.append((unique_id, vector))
    #### search for relevant messages, and generate a response
    results = vdb.query(vector=vector, top_k=convo_length)
    conversation = load_conversation(results)  # results should be a DICT with 'matches' which is a LIST of DICTS, with 'id'
    prompt = utils.open_file('prompt_response.txt').replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', a)
    #### generate response, vectorize, save, etc
    output = gpt3_completion(prompt)
    timestamp = time()
    timestring = utils.timestamp_to_datetime(timestamp)
    #message = '%s: %s - %s' % ('CODEBOT', timestring, output)
    message = output
    vector = gpt3_embedding(message)
    unique_id = str(uuid4())
    metadata = {'speaker': 'CODEBOT', 'time': timestamp, 'message': message, 'timestring': timestring, 'uuid': unique_id}
    utils.save_json('cortex/%s.json' % unique_id, metadata)
    payload.append((unique_id, vector))
    vdb.upsert(payload)
    print('\n\nCODEBOT: %s' % output) 

if __name__ == '__main__':
    
    init()

    while True:
        #### get user input, save it, vectorize it, save to pinecone
        a = input('\n\nUSER: ')
        if a == 'quit':
            break
        chat(a)
        