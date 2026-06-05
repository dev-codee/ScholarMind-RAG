from langchain_community.document_loaders import PyPDFLoader

def load_pdf(file_path: str):
    """Loads a PDF file and returns its documents."""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents
