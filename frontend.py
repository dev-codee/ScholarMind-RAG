import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("frontend")

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(page_title="ScholarMind", page_icon="🧠", layout="wide")

# Backend API URL
API_URL = "http://localhost:8000"

# --- SIDEBAR: Navigation & Upload ---
with st.sidebar:
    st.title("🧠 ScholarMind")
    st.markdown("Your Intelligent Document Assistant")
    
    st.header("1. Upload Documents")
    uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
    if st.button("Ingest Documents") and uploaded_files:
        with st.spinner("Ingesting and encoding documents..."):
            for file in uploaded_files:
                try:
                    logger.info(f"Uploading file: {file.name}")
                    files = {"file": (file.name, file, "application/pdf")}
                    res = requests.post(f"{API_URL}/upload/", files=files)
                    if res.status_code == 200:
                        st.success(f"Successfully ingested {file.name}!")
                        logger.info(f"Successfully ingested {file.name}")
                    else:
                        st.error(f"Failed to ingest {file.name}: {res.text}")
                        logger.error(f"Failed to ingest {file.name}. Status code: {res.status_code}, Response: {res.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error while uploading {file.name}. Is the backend running?")
                    logger.error(f"Connection error uploading {file.name}: {e}", exc_info=True)

    st.divider()
    st.header("2. Choose Feature")
    feature = st.radio("Navigation", [
        "Chat with Citations", 
        "Quiz Generator", 
        "Smart Summarizer", 
        "Compare Documents", 
        "Flashcards", 
        "Research Gaps"
    ])

# --- MAIN PAGE AREA ---

st.title(feature)

# 1. Chat with Citations
if feature == "Chat with Citations":
    st.markdown("Ask anything. Get answers with exact citations and faithfulness scoring.")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])
            if "citations" in chat and chat["citations"]:
                with st.expander("View Citations & Metrics"):
                    st.metric("Faithfulness Score", f'{chat.get("faithfulness_score", "N/A")}')
                    st.write("**Dominance Heatmap:**", chat.get("dominance_heatmap", {}))
                    for idx, cit in enumerate(chat["citations"]):
                        st.info(f"**Source {idx+1}:** {cit['source']} (Page {cit['page']})\n\n> {cit['content']}")

    question = st.chat_input("Ask a question about your documents...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    logger.info(f"Asking question: {question}")
                    response = requests.post(f"{API_URL}/ask/", json={"question": question})
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("answer", "No answer generated.")
                        citations = data.get("citations", [])
                        st.markdown(answer)
                        
                        with st.expander("View Citations & Metrics"):
                            st.metric("Faithfulness Score", f'{data.get("faithfulness_score", "N/A")}/100')
                            st.write("**Dominance Heatmap:**", data.get("dominance_heatmap", {}))
                            for idx, cit in enumerate(citations):
                                st.info(f"**Source {idx+1}:** {cit['source']} (Page {cit['page']})\n\n> {cit['content']}")
                        
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": answer, 
                            "citations": citations,
                            "faithfulness_score": data.get("faithfulness_score"),
                            "dominance_heatmap": data.get("dominance_heatmap")
                        })
                        logger.info("Question answered successfully.")
                    else:
                        st.error("Error connecting to backend.")
                        logger.error(f"Backend returned error. Status code: {response.status_code}, Response: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error("Connection error. Ensure the backend is running.")
                    logger.error(f"Connection error asking question: {e}", exc_info=True)

# 2. Quiz Generator
elif feature == "Quiz Generator":
    topic = st.text_input("Topic to generate quiz on:", placeholder="e.g. Machine Learning, Renaissance...")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    
    if st.button("Generate Quiz"):
        with st.spinner(f"Generating a {difficulty} quiz on '{topic}'..."):
            try:
                logger.info(f"Generating {difficulty} quiz for topic: {topic}")
                res = requests.post(f"{API_URL}/generate_quiz/", json={"topic": topic, "difficulty": difficulty})
                if res.status_code == 200:
                    data = res.json()
                    if "quiz" in data:
                        for i, q in enumerate(data["quiz"]):
                            st.subheader(f"Q{i+1}: {q.get('question')} ({q.get('type')})")
                            if q.get('type') == 'MCQ' and 'options' in q:
                                for opt in q['options']:
                                    st.write(f"- {opt}")
                            with st.expander("Show Answer"):
                                st.success(f"**Answer:** {q.get('answer')}")
                                st.write(f"**Explanation:** {q.get('explanation')}")
                        logger.info("Quiz generated successfully.")
                    else:
                        st.json(data)
                        logger.warning(f"Unexpected response format: {data}")
                else:
                    st.error("Error generating quiz.")
                    logger.error(f"Failed to generate quiz. Status code: {res.status_code}, Response: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error("Connection error. Ensure the backend is running.")
                logger.error(f"Connection error generating quiz: {e}", exc_info=True)

# 3. Summarizer
elif feature == "Smart Summarizer":
    filename = st.text_input("Filename to summarize (e.g. 'paper.pdf')")
    level = st.radio("Summary Level", ["executive", "structured", "eli5"])
    
    if st.button("Summarize"):
        with st.spinner(f"Generating {level} summary..."):
            try:
                logger.info(f"Generating {level} summary for {filename}")
                res = requests.post(f"{API_URL}/summarize/", json={"filename": filename, "level": level})
                if res.status_code == 200:
                    st.write(res.json().get("summary", "No summary found."))
                    logger.info("Summary generated successfully.")
                else:
                    st.error("Error generating summary")
                    logger.error(f"Failed to generate summary. Status code: {res.status_code}, Response: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error("Connection error. Ensure the backend is running.")
                logger.error(f"Connection error generating summary: {e}", exc_info=True)

# 4. Compare Documents
elif feature == "Compare Documents":
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.text_input("Document 1 Filename (e.g. 'paper1.pdf')")
    with col2:
        file2 = st.text_input("Document 2 Filename (e.g. 'paper2.pdf')")
    
    topic = st.text_input("Comparison Topic")
    
    if st.button("Compare"):
        with st.spinner("Analyzing documents..."):
            try:
                logger.info(f"Comparing docs {file1} and {file2} on topic: {topic}")
                res = requests.post(f"{API_URL}/compare/", json={"file1": file1, "file2": file2, "topic": topic})
                if res.status_code == 200:
                    st.json(res.json())
                    logger.info("Documents compared successfully.")
                else:
                    st.error("Error comparing docs.")
                    logger.error(f"Failed to compare docs. Status code: {res.status_code}, Response: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error("Connection error. Ensure the backend is running.")
                logger.error(f"Connection error comparing docs: {e}", exc_info=True)

# 5. Flashcards
elif feature == "Flashcards":
    topic = st.text_input("Topic to generate flashcards on:")
    
    if st.button("Generate Cards"):
        with st.spinner("Extracting definitions and concepts..."):
            try:
                logger.info(f"Generating flashcards for topic: {topic}")
                res = requests.post(f"{API_URL}/generate_flashcards/", json={"topic": topic})
                if res.status_code == 200:
                    cards = res.json()
                    if isinstance(cards, list):
                        for idx, card in enumerate(cards):
                            with st.expander(f"Card {idx+1}: {card.get('front')}"):
                                st.write(card.get('back'))
                        logger.info("Flashcards generated successfully.")
                    else:
                        st.json(cards)
                        logger.warning(f"Unexpected response format: {cards}")
                else:
                    st.error("Error generating flashcards.")
                    logger.error(f"Failed to generate flashcards. Status code: {res.status_code}")
            except requests.exceptions.RequestException as e:
                st.error("Connection error. Ensure the backend is running.")
                logger.error(f"Connection error generating flashcards: {e}", exc_info=True)

# 6. Research Gaps
elif feature == "Research Gaps":
    topic = st.text_input("Topic to identify research gaps in:")
    
    if st.button("Analyze Gaps"):
        with st.spinner("Finding missing answers & future trajectories..."):
            try:
                logger.info(f"Identifying research gaps for topic: {topic}")
                res = requests.post(f"{API_URL}/find_research_gaps/", json={"topic": topic})
                if res.status_code == 200:
                    data = res.json()
                    if "research_gaps" in data:
                        for gap in data["research_gaps"]:
                            st.warning(f"**Missing Link:** {gap.get('gap')}")
                            st.write(f"**Why it's missing:** {gap.get('why_its_missing')}")
                            st.info(f"**Future Direction:** {gap.get('future_direction')}")
                            st.divider()
                        logger.info("Research gaps identified successfully.")
                    else:
                        st.json(data)
                        logger.warning(f"Unexpected response format: {data}")
                else:
                    st.error("Error finding research gaps.")
                    logger.error(f"Failed to find research gaps. Status code: {res.status_code}")
            except requests.exceptions.RequestException as e:
                st.error("Connection error. Ensure the backend is running.")
                logger.error(f"Connection error finding research gaps: {e}", exc_info=True)
