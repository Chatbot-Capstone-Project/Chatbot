from flask import Flask, render_template, request, jsonify
from langchain.document_loaders import PyPDFLoader, OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.question_answering import load_qa_chain


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('chat.html')

callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])


def extract_pdf_and_prepare_docs():
    folder_path = "PDFs/"
    files = os.listdir(folder_path)
    pdf_files = [file for file in files if file.endswith('.pdf')]
    data_list=[]
    for pdf in pdf_files:
        pdf_path = folder_path+pdf
        loader = PyPDFLoader(pdf_path)
        data = loader.load()
        data_list.append(data)
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs=[]
    for data in data_list:
        doc=text_splitter.split_documents(data)
        docs.extend(doc)
    return docs


docs = extract_pdf_and_prepare_docs()


def create_LLM_Llama2_chain():
	model_name_or_path = "TheBloke/Llama-2-13B-chat-GGUF"
	model_basename = "llama-2-13b-chat.Q5_K_M.gguf"
    model_path = hf_hub_download(repo_id=model_name_or_path, filename=model_basename)
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

    chain=load_qa_chain(llm, chain_type="stuff")

    return chain


chain = create_LLM_Llama2_chain()


def get_sentence_transformers_model():
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return model


model = get_sentence_transformers_model()


def prepare_doc_embeddings(docs):
    doc_embeddings = embed_docs(docs)
    return doc_embeddings


def embed_docs(docs, model):
    embedded_docs=[model.encode(doc.page_content) for doc in docs]
    return embedded_docs


doc_embeddings = embed_docs(docs,model)




def custom_top3_similarity_search(query, docs, model, doc_embeddings):
    query_embedding = model.encode([query])
    similarities = cosine_similarity(query_embedding, doc_embeddings)
    top_n_indices = np.argsort(similarities[0])[::-1][:3]
    top_docs = [docs[index] for index in top_n_indices]
    return top_docs

def generate_chatbot_response(query,chain,top_docs):
    simialr_docs=top_docs
    result = chain.run(input_documents=simialr_docs, question=query)
    return result







@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.form['message']
    top_docs = custom_top3_similarity_search(user_message,docs,model,doc_embeddings)
    response = generate_chatbot_response(user_message,chain,top_docs)
    return jsonify({'message': response})



if __name__ == "__main__":
    app.run(debug=True)
