from dagster import asset, repository, Output, resource, op, Field, String, ResourceDefinition
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer


@asset
def manage_folders(context):
    import shutil
    folders = ['PDFs', 'chromaDB_client']

    for folder in folders:
        # Check if the folder exists
        if os.path.exists(folder):
            # Remove the folder and all its contents
            shutil.rmtree(folder)
            context.log.info(f"Deleted folder: {folder}")

        # Recreate the folder
        os.makedirs(folder)
        context.log.info(f"Created folder: {folder}")

@asset
def webscrap(context):
    sitemap_url = "https://www.newhaven.edu/sitemap.xml"
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'xml')
    #keywords = ["data-science"]
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
        "counseling",
        "career"

    ]
    urls = [element.text for element in soup.find_all('loc')]
    pdf_urls = [url for url in urls if url.lower().endswith('.pdf') and any(keyword.lower() in url.lower() for keyword in keywords)]
    php_urls = [url for url in urls if url.lower().endswith('.php') and any(keyword.lower() in url.lower() for keyword in keywords)]
    context.log.info(f"Found {len(pdf_urls)} PDF URLs and {len(php_urls)} PHP URLs.")
    return pdf_urls, php_urls

@asset
def download_pdfs(context, webscrap, manage_folders):
    pdf_urls = webscrap[0]
    for url in pdf_urls:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                filename = os.path.join('PDFs', os.path.basename(urlparse(url).path))
                with open(filename, 'wb') as file:
                    file.write(response.content)
            context.log.info(f"Successfully downloaded {url}")
        except Exception as e:
            context.log.error(f"Error downloading {url}: {e}")

@asset
def convert_php_to_pdf(context, webscrap):
    php_urls = webscrap[1]
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    for i, url in enumerate(php_urls):
        driver.get(url)
        webpage_text = driver.find_element(by="xpath", value="//body").text
        output_pdf_path = os.path.join('PDFs', f"converted_php{i}.pdf")
        pdf = FPDF()
        pdf.add_page()
        # relative path for the font file
        #font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSansCondensed.ttf')
        font_path = 'C:/Users/praveena/Desktop/sample_dagster/fonts/DejaVuSansCondensed.ttf'
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.set_font('DejaVu', '', 14)        
        for line in webpage_text.split('\n'):
            pdf.cell(200, 10, txt=line, ln=True)
        pdf.output(output_pdf_path)
        context.log.info(f"Text saved as PDF: {output_pdf_path}")
    driver.quit()

@asset
def collect_data(context, download_pdfs, convert_php_to_pdf):
    folder_path = 'PDFs'
    files = os.listdir(folder_path)
    pdf_files = [file for file in files if file.endswith('.pdf')]
    data_list = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs = []
    for pdf in pdf_files:
        pdf_path = os.path.join(folder_path, pdf)
        loader = PyPDFLoader(pdf_path)
        data = loader.load()
        data_list.append(data)
    for data in data_list:
        doc = text_splitter.split_documents(data)
        docs.extend(doc)
    context.log.info(f"Collected and split text from {len(pdf_files)} PDFs into {len(docs)} documents.")
    return docs

@asset
def store_in_chroma_db(context, collect_data):
    docs = collect_data
    db_path = 'chromaDB_client'  #path to your ChromaDB client
    chroma_client = chromadb.PersistentClient(path=db_path)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Check if collection exists and delete if it does
    #if chroma_client.count_collections() > 0:
        #chroma_client.delete_collection(name="chatbot_data")
    
    # Create a new collection
    collection = chroma_client.create_collection(name="chatbot_data", embedding_function=sentence_transformer_ef)
    
    # Batch insert documents into the collection
    batch_size = 100  # Define your batch size
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i + batch_size]
        collection.add(documents=[d.page_content for d in batch_docs],
                       metadatas=[d.metadata for d in batch_docs],
                       ids=[str(i) for i, _ in enumerate(batch_docs, start=i)])
    context.log.info("Stored documents in ChromaDB.")

