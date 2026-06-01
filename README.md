# 📊 BizInsight AI

BizInsight AI is an AI-powered customer feedback analytics platform that helps businesses understand customer sentiment, identify key issues, track satisfaction trends, and receive intelligent improvement suggestions.

Built as a real-world business intelligence tool using Python, Streamlit, and advanced AI models.

---

## 🚀 Features

- Upload customer feedback CSV files  
- Automatic sentiment analysis  
- **Smart complaint clustering** – automatically groups negative reviews into business‑relevant categories (Payment, Delivery, Technical, Account, Product Quality, Customer Service, etc.)  
- **Website integration chatbot** – embeddable widget that answers customer questions based on your reviews. 
- Trend tracking over time  
- Top issue detection  
- AI-powered business assistant  
- Persistent data storage  
- Clean dashboard UI  

---

## 🧠 AI Capabilities

- Understands customer pain points  
- Identifies repeating issues  
- Suggests improvement actions  
- Provides business-style insights  
- **Unsupervised topic modelling** – finds hidden complaint patterns without manual labelling  

---

## 🛠 Tech Stack

- Python  
- Streamlit  
- Pandas, Matplotlib  
- Scikit-learn  
- **VADER (NLTK)** (sentiment analysis)  
- **BERTopic** + **HDBSCAN** + **UMAP** (clustering)  
- **Sentence‑Transformers** (`all-mpnet-base-v2`)  
- **LangChain** (RAG pipeline)  
- **ChromaDB** (vector database)  
- **FastAPI** (RAG backend)  
- **OpenRouter** (LLM gateway, Google Gemini)  
- SQLite  

---

## 🔍 Smart Complaint Clustering (Core Feature)

This module automatically groups customer complaints into meaningful clusters, names them (e.g., `"Payment Issues"`, `"Delivery Issues"`).

### How it works

1. **Preprocessing** – removes numbers, `#`, punctuation (keeps apostrophes). No stopword removal – preserves meaning.  
2. **Embedding** – converts reviews into vectors using a Sentence‑Transformer (`all-mpnet-base-v2` or fine‑tuned model).  
3. **Dimensionality reduction** – UMAP (5 components, cosine distance).  
4. **Clustering** – HDBSCAN (density‑based, automatically marks noise as outliers).  
5. **Topic extraction** – BERTopic extracts c‑TF‑IDF words.  
6. **Category mapping** – each cluster is compared to 11 predefined category descriptions (Payment, Delivery, Technical, Account, Product Quality, Customer Service, Shipping Damage, Subscription, Checkout, Return/Refund). If similarity ≥ threshold, the cluster gets a standard name; otherwise it receives a dynamic name generated from the two most frequent content words + suffix (`Issues` / `Error` / `Delay`).  
7. **Merge duplicates** – clusters with the same name are combined.

### How to use it in the dashboard

1. Upload a CSV with a `review` column.  
2. Go to the **Dashboard** tab and click **“Find Complaint Clusters”**.  
3. Wait for the analysis (first run loads the embedding model).  
4. Expandable clusters – each shows name, number of reviews, some complaints.

## 🧠 RAG Chatbot – Ask Your Reviews

A dedicated conversational AI that answers business questions based **only** on the uploaded customer reviews.

### How it works

1. **Vector Store – Embeddings & Storage**
Customer reviews are converted into 384‑dimensional vectors using `all-MiniLM-L6-v2` and stored in ChromaDB along with metadata (sentiment, date). The vector store is re‑synced automatically after every CSV upload. 
2. **Smart Retrieval – Finding the Right Reviews**
When a user asks a question, the backend does three things:

Sentiment filtering – if the question mentions “problem”, “issue”, etc., only negative reviews are retrieved; for “good”, “great” etc., only positive reviews are used.

Multi‑Query expansion – the LLM generates 3 rephrased versions of the question to catch more relevant reviews (improves recall).

Cross‑encoder re‑ranking – a neural model (`ms‑marco-MiniLM‑L‑6‑v2`) scores each candidate review and keeps only the top‑8 most relevant ones (improves precision).  
3. **LLM Answer – Grounded & Strict**
The top‑8 reviews are inserted into a strict prompt that instructs the LLM (Google Gemini via OpenRouter) to answer only based on the provided context. If the answer is not in the reviews, the model says “The customer reviews do not mention this information.”
4. **Conversation Memory – Follow‑up Questions**
Session‑based memory (ConversationBufferMemory) keeps the chat history. The user can ask follow‑up questions without repeating context, and the retrieval automatically incorporates sentiment‑aware filtering for each new turn.

### How to use it

1. Start the FastAPI backend (separate terminal):  
   ```bash
   python run_chatbot_api.py

## 📂 Project Structure

bizinsight-ai/
├── app.py
├── database.py
├── run_chatbot_api.py
├── sync_vectors.py
├── rag_api /
    ├── api.py
    ├── chains.py
    ├── config.py
    ├── embeddings.py
    ├── vector_store.py
├── clustering/
    ├── run_clustering.py
    ├── preprocess.py
    ├── vectorize.py
├── models/finetuned_complaint_model_final
├── data / reviews.csv
├── tests / 
    ├── product_reviews_1000.csv
    ├── test1.csv
    ├── test2.csv
    ├── test3.csv

---

## 📥 How to Run Locally

### Install dependencies

pip install -r requirements.txt

streamlit run app.py


---

### 5. **Requirements.txt** – update to match actual imports

```txt
streamlit
pandas
matplotlib
scikit-learn
nltk
sentence-transformers
langchain
langchain-community
langchain-chroma
langchain-openai
chromadb
hdbscan
umap-learn
fastapi
uvicorn
python-dotenv
openai
requests

---

## 📥 Installation & Setup

Follow these steps to set up the project locally on your machine.

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/Prateekiiitg56/BizInsight-AI.git
cd BizInsight-AI
```

### 2. Set Up a Virtual Environment
Choose **one** of the options below to isolate your project dependencies.

#### Option A: Using Standard Python (venv)
* **Create the environment:**
  ```bash
  python -m venv venv
  ```
* **Activate the environment:**
  * **Windows:**
    ```bash
    venv\Scripts\activate
    ```
  * **macOS / Linux:**
    ```bash
    source venv/bin/activate
    ```

#### Option B: Using Anaconda (conda)
* **Create and activate the environment:**
  ```bash
  conda create --name BizInsight-AI-env python=3.10 -y
  conda activate BizInsight-AI-env
  ```

### 3. Install Dependencies
Once your virtual environment is active, install the required packages:
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

1. Create a free account at [OpenRouter](https://openrouter.ai/) and get your API key.

2. Copy the example env file:
   - **macOS / Linux:**
```bash
     cp .env.example .env
```
   - **Windows:**
```bash
     copy .env.example .env
```

3. Open the `.env` file and add your API key:
```
   OPENROUTER_API_KEY=your_api_key_here
```

> ⚠️ Never share or commit your `.env` file. It is already listed in `.gitignore`.

---

### 5. Run the Application
Start the Streamlit dashboard:
```bash
streamlit run app.py
```

---

### Requirements.txt
streamlit
pandas
matplotlib
scikit-learn
nltk
bertopic
hdbscan
umap-learn
sentence-transformers
python-dotenv

## 📄 CSV Format

Your CSV file must contain a column named `review`.

---

## 📈 Example Use Cases

- E-commerce customer experience analysis  
- Service quality monitoring  
- Product feedback insights  
- Business performance improvement  
  
---

## 🏆 Why BizInsight AI?

Manually analyzing customer feedback is time-consuming and error-prone.  
BizInsight AI converts raw reviews into actionable business intelligence using AI.

---

## 📌 Future Enhancements

- Multi-business login system  
- Automated report generation (PDF)   
- Trend alert system  

---

## 👨‍💻 Author

Built by **Prateek Singh**  
BTech Student | AI & Software Development Enthusiast

---

⭐ If you like this project, consider giving it a star!
