import os
import json
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma

from embeddings import get_embeddings_model
from collections import Counter

def ask_question(question: str, persist_directory: str = "./chroma_db"):
    """
    Retrieves context from ChromaDB and passes it to Gemini LLM to answer the question.
    """
    # Ensure Google API key is set
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set your Gemini API key.")

    # Initialize Gemini model
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    # Get the embedding model used during ingestion
    embeddings = get_embeddings_model()
    
    # Connect to the existing local Chroma vector store
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    
    # Retrieve top 4 most relevant chunks
    docs = vectorstore.similarity_search(question, k=4)
    retrieved_context = "\n\n".join([doc.page_content for doc in docs])
    
    # Generate the answer and a faithfulness score (Feature 7)
    prompt = f"""
    Answer the following question based ONLY on the provided context. 
    If you don't know the answer or the context is insufficient, explicitly state that.
    Also provide a "faithfulness_score" from 0 to 100 indicating how strongly your answer is supported purely by the context (100 means fully supported).
    
    Format your response as a JSON object:
    {{
        "answer": "...",
        "faithfulness_score": 95
    }}

    <context>
    {retrieved_context}
    </context>

    Question: {question}
    """
    
    response = llm.invoke(prompt)
    try:
        content = response.content.replace('```json', '').replace('```', '')
        result = json.loads(content)
        answer = result.get("answer", "")
        faithfulness = result.get("faithfulness_score", 0)
    except:
        answer = response.content
        faithfulness = "N/A (parsing failed)"
    
    # Extract sources for citation (Feature 1) and calculate Heatmap (Feature 8)
    sources = []
    source_counts = Counter()
    
    for doc in docs:
        source_file = doc.metadata.get("source", "Unknown file")
        sources.append({
            "source": source_file,
            "page": doc.metadata.get("page", "Unknown page"),
            "content": doc.page_content
        })
        source_counts[source_file] += 1
        
    total_sources = len(docs)
    dominance_heatmap = {src: f"{int((count / total_sources) * 100)}%" for src, count in source_counts.items()}
        
    return {
        "answer": answer,
        "faithfulness_score": faithfulness,
        "sources": sources,
        "dominance_heatmap": dominance_heatmap
    }
