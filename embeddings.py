import os
from langchain_cohere import CohereEmbeddings

def get_embeddings_model():
    """Initializes and returns the cloud embedding model."""
    if "COHERE_API_KEY" not in os.environ:
        raise ValueError("COHERE_API_KEY is missing! Please get a free key from dashboard.cohere.com and add it to your .env file.")
        
    # Cohere provides a generous, fast, and free cloud embedding API
    return CohereEmbeddings(
        cohere_api_key=os.environ["COHERE_API_KEY"], 
        model="embed-english-light-v3.0"
    )
