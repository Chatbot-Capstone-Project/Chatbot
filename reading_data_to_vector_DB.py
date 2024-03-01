import os
import chromadb
from chromadb.utils import embedding_functions

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


def collecting_data_to_list(folder_path="PDFs"):
    files = os.listdir(folder_path)
    pdf_files = [file for file in files if file.endswith('.pdf')]
    data_list = []
    for pdf in pdf_files:
        pdf_path = folder_path + pdf
        loader = PyPDFLoader(pdf_path)
        data = loader.load()
        data_list.append(data)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs = []
    for data in data_list:
        doc = text_splitter.split_documents(data)
        docs.extend(doc)
    return docs


def store_documenmts_in_chromaDB(folder_path,db_path='/chromaDB_client'):
    chroma_client = chromadb.PersistentClient(path=db_path)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    if chroma_client.count_collections()>0:
        chroma_client.delete_collection(name="chatbot_data")
    collection = chroma_client.create_collection(name="chatbot_data", embedding_function=sentence_transformer_ef)
    docs = collecting_data_to_list(folder_path=folder_path)
    collection.add(documents=[d.page_content for d in docs],
                   metadatas=[d.metadata for d in docs],
                   ids=[str(i) for i, d in enumerate(docs)]
                   )


if __name__ == "__main__":
    db_path = '/Users/konishbharathrajjonnalagadda/Desktop/UNH/capstone/chromaDB_client'
    folder_path = '/Users/konishbharathrajjonnalagadda/Desktop/UNH/capstone/PDFs/'
    store_documenmts_in_chromaDB(folder_path,db_path)

