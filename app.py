from collections import deque

import chromadb
from flask import Flask, render_template, request, jsonify
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.question_answering import load_qa_chain

app = Flask(__name__)
db_path = '/Users/konishbharathrajjonnalagadda/Desktop/UNH/capstone/chromaDB_client'
chroma_client = chromadb.PersistentClient(path=db_path)
collection = chroma_client.get_collection(name="chatbot_data")
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
current_history = []


class SentenceQueue:
    def __init__(self, max_length):
        self.queue = deque(maxlen=max_length)

    def add_sentence(self, sentence):
        self.queue.append(sentence)

    def display_queue(self):
        for sentence in self.queue:
            print(sentence)

    def combine_sentences(self):
        combined_sentence = " ".join(self.queue)
        return combined_sentence

    def clear_queue(self):
        self.queue.clear()


sentence_queue = SentenceQueue(10)


class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata if metadata is not None else {}


def create_LLM_Llama2_chain():
    model_path = '/Users/konishbharathrajjonnalagadda/Desktop/UNH/capstone/model/llama-2-13b-chat.Q5_K_M.gguf'
    n_gpu_layers = 1  # Set low since no GPU is used, adjust based on your system's performance.
    n_batch = 1  # Significantly reduced for CPU processing to minimize memory usage.

    # Loading model,
    llm = LlamaCpp(
        model_path=model_path,
        max_tokens=256,
        n_gpu_layers=n_gpu_layers,
        n_batch=n_batch,
        callback_manager=callback_manager,
        n_ctx=1024,
        verbose=True,
    )

    chain = load_qa_chain(llm, chain_type="stuff")

    return chain


chain = create_LLM_Llama2_chain()


@app.route('/')
def home():
    return render_template('chat.html')


callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])


def generate_chatbot_response(query, chain, collection):
    results = collection.query(
        query_texts=[query],
        n_results=3)
    simialr_docs = [Document(page_content=text) for text in results['documents']]
    result = chain.run(input_documents=simialr_docs, question=query)
    return result


@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.form['message']
    sentence_queue.add_sentence(user_message)
    query = sentence_queue.combine_sentences()
    response = generate_chatbot_response(query, chain, collection)
    current_history.append(('human message : ' + user_message, 'AI message : ' + response))
    sentence_queue.add_sentence(response)
    return jsonify({'message': response})



if __name__ == "__main__":
    app.run(debug=True)
    print(current_history)

