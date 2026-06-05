import os
import tempfile
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("backend")

# Load environment variables
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn

from pydantic import BaseModel
from typing import Optional
from loader import load_pdf
from chunker import chunk_documents
from embeddings import get_embeddings_model
from store import store_chunks
from retriever import ask_question
from s3_utils import upload_to_s3
from scholar_features import (
    generate_quiz, summarize_document, compare_documents, 
    generate_flashcards, find_research_gaps
)

app = FastAPI(title="ScholarMind API")

# Initialize the embedding model globally
logger.info("Initializing embedding model globally...")
embeddings = get_embeddings_model()
persist_directory = "./chroma_db"
logger.info("Embedding model initialized.")

class QuestionRequest(BaseModel):
    question: str

class QuizRequest(BaseModel):
    topic: str
    difficulty: str = "medium"

class SummarizeRequest(BaseModel):
    filename: str
    level: str = "executive" # "executive", "structured", "eli5"

class CompareRequest(BaseModel):
    file1: str
    file2: str
    topic: str

class TopicRequest(BaseModel):
    topic: str

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    logger.info(f"Received request to upload file: {file.filename}")
    if not file.filename.endswith(".pdf"):
        logger.error(f"Invalid file type uploaded: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(await file.read())
        tmp_file_path = tmp_file.name

    try:
        logger.info(f"Loading PDF document: {file.filename}")
        # 1. Load the PDF
        documents = load_pdf(tmp_file_path)

        # Replace temp file path in metadata with the original filename
        for doc in documents:
            doc.metadata["source"] = file.filename

        logger.info(f"Chunking {len(documents)} pages from {file.filename}")
        # 2. Chunking
        chunks = chunk_documents(documents)

        logger.info(f"Embedding and storing {len(chunks)} chunks in ChromaDB")
        # 3. Embed & Store in Chroma
        vectorstore = store_chunks(chunks, embeddings, persist_directory)
        
        logger.info(f"Successfully processed {file.filename}")
        return {
            "message": "Successfully ingested PDF.",
            "filename": file.filename,
            "total_pages": len(documents),
            "chunks_created": len(chunks)
        }

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temp file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            logger.debug(f"Removed temporary file: {tmp_file_path}")

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to ScholarMind API."}

@app.post("/ask/")
def ask_pdf(request: QuestionRequest):
    logger.info(f"Received question: {request.question}")
    try:
        result = ask_question(request.question, persist_directory)
        logger.info("Successfully generated answer for question")
        return {
            "question": request.question, 
            "answer": result["answer"],
            "faithfulness_score": result["faithfulness_score"], # Feature 7
            "citations": result["sources"],                     # Feature 1
            "dominance_heatmap": result["dominance_heatmap"]    # Feature 8
        }
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_quiz/")
def api_generate_quiz(request: QuizRequest):
    logger.info(f"Received request to generate {request.difficulty} quiz on topic: {request.topic}")
    try:
        return generate_quiz(request.topic, request.difficulty, persist_directory)
    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize/")
def api_summarize(request: SummarizeRequest):
    logger.info(f"Received request to summarize {request.filename} at {request.level} level")
    try:
        return summarize_document(request.filename, request.level, persist_directory)
    except Exception as e:
        logger.error(f"Error summarizing document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare/")
def api_compare(request: CompareRequest):
    logger.info(f"Received request to compare {request.file1} and {request.file2} on {request.topic}")
    try:
        return compare_documents(request.file1, request.file2, request.topic, persist_directory)
    except Exception as e:
        logger.error(f"Error comparing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_flashcards/")
def api_flashcards(request: TopicRequest):
    logger.info(f"Received request to generate flashcards on topic: {request.topic}")
    try:
        return generate_flashcards(request.topic, persist_directory)
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/find_research_gaps/")
def api_research_gaps(request: TopicRequest):
    logger.info(f"Received request to find research gaps on topic: {request.topic}")
    try:
        return find_research_gaps(request.topic, persist_directory)
    except Exception as e:
        logger.error(f"Error finding research gaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
