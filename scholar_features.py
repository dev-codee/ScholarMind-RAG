import os
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from embeddings import get_embeddings_model

def get_llm():
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    # Use JSON mode if possible, but standard prompting with json instruction works too
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

def generate_quiz(topic: str, difficulty: str, persist_directory: str = "./chroma_db"):
    llm = get_llm()
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=get_embeddings_model())
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
    
    docs = retriever.invoke(topic)
    context = "\n\n".join([d.page_content for d in docs])
    
    prompt = f"""
    Based on the following document context, generate a quiz about "{topic}" at a {difficulty} difficulty level.
    Include a mix of multiple-choice (MCQs), true/false, and short answer questions.
    Return ONLY a valid JSON object with the following structure:
    {{
        "quiz": [
            {{ "type": "MCQ", "question": "...", "options": ["A", "B", "C", "D"], "answer": "...", "explanation": "..." }},
            {{ "type": "True/False", "question": "...", "answer": "...", "explanation": "..." }},
            {{ "type": "Short Answer", "question": "...", "answer": "...", "explanation": "..." }}
        ]
    }}
    
    Context:
    {context}
    """
    response = llm.invoke(prompt)
    try:
        content = response.content.replace('```json', '').replace('```', '')
        return json.loads(content)
    except:
        return {"error": "Failed to parse JSON response"}

def summarize_document(filename: str, level: str, persist_directory: str = "./chroma_db"):
    llm = get_llm()
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=get_embeddings_model())
    # Retrieve chunks specific to the filename
    docs = vectorstore.similarity_search("summary", k=15, filter={"source": filename})
    context = "\n\n".join([d.page_content for d in docs])
    
    level_instruction = ""
    if level == "executive":
        level_instruction = "Provide a one-paragraph executive summary."
    elif level == "structured":
        level_instruction = "Provide a structured section-by-section breakdown."
    elif level == "eli5":
        level_instruction = "Provide a simplified ELI5 (Explain Like I'm 5) version."
        
    prompt = f"""
    Based on the following excerpts from {filename}, summarize the content.
    {level_instruction}
    
    Context:
    {context}
    """
    response = llm.invoke(prompt)
    return {"summary": response.content, "level": level, "filename": filename}

def compare_documents(file1: str, file2: str, topic: str, persist_directory: str = "./chroma_db"):
    llm = get_llm()
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=get_embeddings_model())
    
    docs1 = vectorstore.similarity_search(topic, k=6, filter={"source": file1})
    docs2 = vectorstore.similarity_search(topic, k=6, filter={"source": file2})
    
    context1 = "\n".join([d.page_content for d in docs1])
    context2 = "\n".join([d.page_content for d in docs2])
    
    prompt = f"""
    Compare the following two documents on the topic of "{topic}".
    Document 1 ({file1}):
    {context1}
    
    Document 2 ({file2}):
    {context2}
    
    Identify:
    1. Where they agree (Similarities)
    2. Where they contradict each other (Differences)
    3. What each covers that the other doesn't (Unique points)
    
    Return a structured JSON:
    {{
        "similarities": ["..."],
        "contradictions": ["..."],
        "unique_to_file1": ["..."],
        "unique_to_file2": ["..."]
    }}
    """
    response = llm.invoke(prompt)
    try:
        content = response.content.replace('```json', '').replace('```', '')
        return json.loads(content)
    except:
        return {"error": "Failed to parse JSON response"}

def generate_flashcards(topic: str, persist_directory: str = "./chroma_db"):
    llm = get_llm()
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=get_embeddings_model())
    docs = vectorstore.similarity_search(topic, k=10)
    context = "\n\n".join([d.page_content for d in docs])
    
    prompt = f"""
    Extract key concepts, definitions, and important facts from the context below and create Anki-style flashcards.
    Return ONLY a valid JSON array of objects:
    [
        {{"front": "Concept/Question", "back": "Definition/Fact"}}
    ]
    
    Context:
    {context}
    """
    response = llm.invoke(prompt)
    try:
        content = response.content.replace('```json', '').replace('```', '')
        return json.loads(content)
    except:
        return {"error": "Failed to parse JSON response"}

def find_research_gaps(topic: str, persist_directory: str = "./chroma_db"):
    llm = get_llm()
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=get_embeddings_model())
    docs = vectorstore.similarity_search(topic, k=20)
    context = "\n\n".join([d.page_content for d in docs])
    
    prompt = f"""
    Analyze the following research context related to "{topic}" and identify the research gaps.
    What are the questions that none of the texts fully answer? 
    Where is future research needed?
    Return a detailed JSON:
    {{
        "research_gaps": [
            {{"gap": "...", "why_its_missing": "...", "future_direction": "..."}}
        ]
    }}
    
    Context:
    {context}
    """
    response = llm.invoke(prompt)
    try:
        content = response.content.replace('```json', '').replace('```', '')
        return json.loads(content)
    except:
        return {"error": "Failed to parse JSON response"}
