# BizInsight AI

BizInsight AI is an enterprise-grade customer feedback analytics platform that automates customer sentiment analysis, groups customer complaints into category-mapped topic clusters, and provides a Retrieval-Augmented Generation (RAG) assistant for querying review data.

This project was recently migrated from a legacy monolithic Streamlit application to a modern microservices architecture consisting of a Next.js 14 frontend and a FastAPI backend.

---

## Key Features

- **Automated Sentiment Analysis**: Instant processing of customer review datasets with metric tracking (Average Sentiment, analyzed review counts, risk thresholds).
- **Categorized Complaint Clustering**: Unsupervised topic modeling grouping negative reviews into business-relevant categories (Payment, Delivery, Technical, Account, Product Quality, Customer Service, etc.).
- **Retrieval-Augmented Generation (RAG) Chatbot**: A contextual question-answering assistant that responds to business queries using only the uploaded customer reviews, preventing hallucinations.
- **Standalone Guest RAG Sandbox**: A public-facing chat interface that does not require user authentication, utilizing a direct ChromaDB integration.
- **Structured Alerts**: Monitoring of risk levels, negative review spikes, and notifications.

---

## Architecture & Tech Stack

- **Frontend**: Next.js 14, React, Tailwind CSS, Lucide Icons.
- **Backend API**: FastAPI, Uvicorn, Python, SQLite.
- **Machine Learning & NLP**:
  - Sentiment Analysis: NLTK VADER.
  - Topic Clustering: BERTopic, HDBSCAN, UMAP.
  - Sentence Embeddings: Sentence-Transformers (using `all-mpnet-base-v2`).
- **Vector DB & RAG Pipeline**: LangChain, ChromaDB, OpenRouter (Gemini LLM).

---

## Directory Structure

```text
BizInsight-AI/
├── bizinsight_api/          # FastAPI backend application
│   ├── routes/              # API router files (auth, reviews, dashboard, clustering, admin)
│   ├── models/              # Database models and schemas
│   └── main.py              # Backend entry point
├── bizinsight-web/          # Next.js 14 frontend application
│   ├── src/
│   │   ├── app/             # Next.js App Router (dashboard pages, chat sandbox, landing page)
│   │   ├── components/      # UI components
│   │   └── lib/             # API client utilities
│   └── public/              # Static assets
├── rag_api/                 # Core RAG chatbot service logic
├── clustering/              # Clustering algorithms and category mapping
├── database.py              # Database initialization and connection helpers
├── sentiment.py             # NLTK VADER sentiment analyzer wrapper
├── download_model.py        # Utility to download NLTK data and models
├── sync_vectors.py          # Vector store synchronization script
└── requirements.txt         # Backend Python dependencies
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Prateekiiitg56/BizInsight-AI.git
cd BizInsight-AI
```

### 2. Set Up the Backend API

1. Navigate to the project root directory and set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the NLTK and SentenceTransformer models:
   ```bash
   python download_model.py
   ```

4. Configure the environment variables by creating a `.env` file in the root directory:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_
   ```

5. Start the FastAPI backend server:
   ```bash
   uvicorn bizinsight_api.main:app --host 0.0.0.0 --port 8001 --reload
   ```

### 3. Set Up the Frontend

1. Navigate to the `bizinsight-web` directory:
   ```bash
   cd bizinsight-web
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## CSV File Requirements

To upload review datasets, the CSV files must include at least one column labeled `review` containing the textual customer feedback.

---

## Authors & Acknowledgments

- **Prateek Singh** - AI & Software Developer
