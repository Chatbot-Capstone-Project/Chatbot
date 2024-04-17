from dagster import repository
from assets import webscrap, download_pdfs, convert_php_to_pdf, collect_data, store_in_chroma_db

@repository
def my_etl_repository():
    return [webscrap, download_pdfs, convert_php_to_pdf, collect_data, store_in_chroma_db]
