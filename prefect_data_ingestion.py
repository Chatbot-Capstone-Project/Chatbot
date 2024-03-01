import json
from bs4 import BeautifulSoup
from prefect import task, flow
from urllib.parse import urljoin, urlparse
import os 
import requests
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.csv_loader import CSVLoader


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
            print (page.metadata['source'])
            source = page.metadata['source'].split('\\')[-1]
            print(source)
            page.metadata['source'] = url_mapping.get(source, 'Unknown')
        pdf_data.extend(pages)
    print("PDF Data Loaded successfully")
    return pdf_data

# @task(log_prints=True)
# def loadCSVData(file_path):
#     loader = CSVLoader(file_path=file_path,encoding='latin1')
#     data = loader.load()
#     return data

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


#Run the tasks
@flow(log_prints=True)
def data_flow():
    # Define the Prefect flow
    pdf_urls,php_urls = fetch_data_from_urls()

    print("PHP URLs:",len(php_urls))
    print("PDF URLs:",len(pdf_urls))

    # download pdf's from urls
    for url in pdf_urls:
        download_pdf(url, folder="PDFs")

    # loading pdf data
    pdf_data = loadPDFData()

    #assigning pdf data to final_data list
    final_data = []
    final_data.extend(pdf_data)

    data = split_data_chunks(final_data)
    return data

# Run the flow
if __name__ == "__main__":
    data_flow()