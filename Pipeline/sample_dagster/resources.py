from dagster import resource, Field, String

@resource({
    "pdf_storage": Field(str, default_value="PDFs", description="Directory to store PDF files"),
    "chromadb_path": Field(str, default_value="/chromaDB_client", description="Path to ChromaDB client storage")
})
def storage_paths(init_context):
    return {
        "pdf_storage": init_context.resource_config["pdf_storage"],
        "chromadb_path": init_context.resource_config["chromadb_path"]
    }