# 🤖 Wikipedia RAG ChatBot

A Retrieval-Augmented Generation (RAG) chatbot that scrapes Wikipedia using BeautifulSoup, vectorizes the content with HuggingFace sentence transformers, and allows users to chat with a personalized bot using Cohere's language model — all through an interactive Streamlit UI.

---

## 🔍 Features

- ✅ Scrape live Wikipedia pages (infobox + article content)
- 🧠 Vectorize text using Sentence Transformers
- 📚 Store embeddings in FAISS for fast retrieval
- 💬 Ask contextual questions using LangChain's RAG pipeline
- ☁️ Upload scraped text to AWS S3
- 🧹 Clear memory and vector store with one click

---

## 🚀 Tech Stack

| Component     | Description                           |
|---------------|---------------------------------------|
| Streamlit     | UI frontend                           |
| BeautifulSoup | Wikipedia web scraper (no Scrapy)     |
| LangChain     | Orchestration + RAG pipeline          |
| FAISS         | Vector similarity search              |
| Cohere        | LLM backend (command-r-plus)          |
| HuggingFace   | Sentence embeddings (MiniLM)          |
| AWS S3        | Stores scraped text backup            |

---

## 🔧 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/personalities_wikipedia.git
cd personalities_wikipedia

## 🔄 RAG System Flow

```mermaid
flowchart TD
    A[🧑 User Inputs Name] --> B[🌐 Wikipedia Scraper (BeautifulSoup)]
    B --> C[📄 Extracted Article + Infobox Text]
    C --> D[🔤 Sentence Embeddings (MiniLM - HuggingFace)]
    D --> E[🧠 FAISS Vector Store]
    E --> F[🔍 Retriever (Top-k Matches)]

    F --> G[📜 Prompt Template + Context]
    G --> H[🧠 Cohere LLM (command-r-plus)]
    H --> I[💬 Final Answer Generated]
    I --> J[📺 Response Rendered in Streamlit UI]


