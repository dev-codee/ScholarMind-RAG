from langchain_community.vectorstores import Chroma

def store_chunks(chunks, embeddings, persist_directory="./chroma_db"):
    """Stores embedded document chunks in a local Chroma vector database."""
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    return vectorstore
