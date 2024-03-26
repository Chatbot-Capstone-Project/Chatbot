import json
import pandas as pd
from bs4 import BeautifulSoup
from prefect import task, flow, Flow
from urllib.parse import urljoin, urlparse
import os 
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.csv_loader import CSVLoader
import chromadb
from chromadb.utils import embedding_functions
from prefect_dask import DaskTaskRunner


with open('url_mapping.json', 'r', encoding='utf-8') as file:
    url_mapping = json.load(file)

@task(log_prints=True)
def fetch_data_from_urls(sitemap_url = "https://www.newhaven.edu/sitemap.xml"):
    # Fetch the sitemap content
    response = requests.get(sitemap_url)
    # Keywords to filter URLs
    keywords = [
        "data-science",
        "Artificial",
        "intelligence",
        "faq",
        "tagliatela",
        "international",
        "immigration",
        "visa",
        "international-services",
        "course",
        "bursars",
        "one-stop",
        "registrar",
        "career",
        "technical-support",
        "library",
        "counseling"

    ]
    # Parse the sitemap content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'xml')
    # Find all URLs in the sitemap
    urls = [element.text for element in soup.find_all('loc')]
    # Filter URLs based on keywords
    urls = [url for url in urls if any(keyword.lower() in url.lower() for keyword in keywords)]
    # Separate PDF and PHP URLs
    pdf_urls = [url for url in urls if url.lower().endswith('.pdf')]
    php_urls = [url for url in urls if url.lower().endswith('.php')]
    return pdf_urls, php_urls

@task(log_prints=True)
def download_pdf(url, folder="PDFs"):
    """
    Downloads a single PDF file from a URL.
    """
    if not os.path.isdir(folder):
        os.makedirs(folder)

    try:
        response = requests.get(url, stream=True)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            filename = os.path.join(folder, url.split('/')[-1] or "downloaded_pdf.pdf")

            with open(filename, 'wb') as file:
                file.write(response.content)
            print(f"Successfully downloaded {url}")
        else:
            print(f"Failed to download {url} - Response code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")


@task(log_prints=True)
def loadPDFData():
    pdf_data = []
    cwd = os.getcwd()
    for pdf in os.listdir('PDFs'):
        pdf_path = os.path.join(cwd, 'PDFs')
        pdf = os.path.join(pdf_path,pdf)
        loader = PyPDFLoader(pdf)
        pages = loader.load_and_split()
        for page in pages:
            # print (page.metadata['source'])
            source = page.metadata['source'].split('\\')[-1]
            # print(source)
            page.metadata['source'] = url_mapping.get(source, 'Unknown')
        pdf_data.extend(pages)
    print("PDF Data Loaded successfully")
    return pdf_data


@task(log_prints=True)
def split_data_chunks(final_data):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap  = 0,
    )
    docs_chunks = text_splitter.split_documents(final_data)
    print("Splitting Data Done Successfully")
    return docs_chunks

@task
def store_in_chromadb(page_content, metadata, collection, id):
    collection.add(documents=[page_content], metadatas=[metadata], ids=[str(id)])

@task
def load_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    return loader.load()

@Flow
def collecting_data_to_list_flow(folder_path="PDFs"):
    files = os.listdir(folder_path)
    pdf_files = [file for file in files if file.endswith('.pdf')]
    data_list = []
    for pdf in pdf_files:
        pdf_path = os.path.join(folder_path, pdf)
        #print(f"Attempting to load: {pdf_path}")
        data = load_pdf(pdf_path)
        data_list.append(data)
    return data_list

@Flow
def store_documents_in_chromaDB_flow(folder_path, db_path="/db1"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    if chroma_client.count_collections() > 0:
        chroma_client.delete_collection(name="chatbot_data")
    
    collection = chroma_client.create_collection(name="chatbot_data", embedding_function=sentence_transformer_ef)
    data_list = collecting_data_to_list_flow(folder_path=folder_path)
    
    for i, data in enumerate(data_list):
        docs = split_data_chunks(data)
        for doc in docs:
            store_in_chromadb(doc.page_content, doc.metadata, collection, id=i)


#Run the tasks
@flow(log_prints=True, task_runner=DaskTaskRunner)
def data_flow():
    # Define the Prefect flow
    pdf_urls,php_urls = fetch_data_from_urls("https://www.newhaven.edu/sitemap.xml")
    print("PHP URLs:",len(php_urls))
    print("PDF URLs:",len(pdf_urls))

    # download pdf's from urls
    for url in pdf_urls:
        download_pdf(url, folder="PDFs")


# Run the flow
if __name__ == "__main__":
    data_flow()

    db_path = r'C:\Users\ssetr\Desktop\Capstone\New folder\db1'
    folder_path = r'C:\Users\ssetr\Desktop\Capstone\New folder\PDFs'

    flow = store_documents_in_chromaDB_flow(folder_path, db_path)
    flow.run(executor=DaskTaskRunner())