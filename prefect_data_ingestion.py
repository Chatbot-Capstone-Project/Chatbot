import json
import pandas as pd
from bs4 import BeautifulSoup
from prefect import task, flow
from urllib.parse import urljoin, urlparse
import os 
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.csv_loader import CSVLoader

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
import nltk



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
def loadCSVData(file_path):
    loader = CSVLoader(file_path=file_path,encoding='latin1')
    data = loader.load()
    return data

@task(log_prints=True)
def split_data_chunks(final_data):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1200,
        chunk_overlap  = 200,
        length_function = len,
    )
    docs_chunks = text_splitter.split_documents(final_data)
    print("Splitting Data Done Successfully")
    return docs_chunks

#PREPROCESSING PIPELINE

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# @task(log_prints=True)
def preprocess(text):
    text = str(text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    normalized_tokens = [token.lower() for token in tokens 
                     if token.isalnum() 
                     and token.lower() not in stop_words]
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) 
                     for token in normalized_tokens]
    lemetized_text= ' '.join(lemmatized_tokens)
    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(token) 
                      for token in normalized_tokens]
    stemmed_text = ' '.join(stemmed_tokens)
    return lemetized_text,stemmed_text

@task(log_prints=True)
def preprocess_all_docs(docs):
    lem_docs=[]
    stem_docs=[]
    for doc in docs:
        lem,stem = preprocess(doc)
        lem_docs.append(lem)
        stem_docs.append(stem)
    return lem_docs,stem_docs

#Run the tasks
@flow(log_prints=True)
def data_flow():
    # Define the Prefect flow
    pdf_urls,php_urls = fetch_data_from_urls("https://www.newhaven.edu/sitemap.xml")
    print("PHP URLs:",len(php_urls))
    print("PDF URLs:",len(pdf_urls))

    # download pdf's from urls
    for url in pdf_urls:
        download_pdf(url, folder="PDFs")

    # loading pdf data
    pdf_data = loadPDFData()

    #loading csv data
    csv_file_path = 'FAQ/MSDS_FAQ.csv'
    csv_data = loadCSVData(csv_file_path)

    #assigning pdf & csv data to final_data list
    final_data = []
    final_data.extend(pdf_data)
    final_data.extend(csv_data)

    data = split_data_chunks(final_data)

    lemetized_data,stemmed_data=preprocess_all_docs(data)

    data_df = pd.DataFrame({'Lemmatized': lemetized_data, 'Stemmed': stemmed_data})
    return data_df



# Run the flow
if __name__ == "__main__":
    data_flow()