
from dagster import repository
from .assets import webscrap, download_pdfs, convert_php_to_pdf, collect_data, store_in_chroma_db
from .resources import storage_paths  

@repository
def my_etl_repository():
    return {
        'assets': [
            webscrap,
            download_pdfs,
            convert_php_to_pdf,
            collect_data,
            store_in_chroma_db,
            generate_QA_pairs,
        ],
        'resources': {
            'storage_paths': storage_paths,
        },
    }