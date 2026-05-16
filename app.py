import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
st.set_page_config(page_title="BizInsight AI", layout="wide")

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob
from database import insert_feedback, fetch_feedback, clear_data
from openai import OpenAI

# ---------- Chimera AI Client ----------

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set. Please create a .env file with your API key.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

st.title("📊 BizInsight AI")
st.caption("AI-powered customer intelligence platform for business growth")

tabs = st.tabs(["📊 Dashboard", "🤖 AI Assistant", "📂 Data Upload", "⚙ Controls"])

# ---------- Core Functions ----------

def get_sentiment(text):
    return TextBlob(text).sentiment.polarity


def ask_ai(question, reviews):
    context = "\n".join(reviews[:40])

    prompt = f"""
You are a professional business analyst.

Customer feedback:
{context}

Analyze patterns, root problems and give improvement suggestions.

Question:
{question}
"""

    response = client.chat.completions.create(
        model="tngtech/deepseek-r1t2-chimera:free",
        messages=[
            {"role": "system", "content": "You provide business intelligence insights."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content


# ================= DATA UPLOAD =================

with tabs[2]:
    st.subheader("📂 Upload Customer Reviews")

    uploaded_file = st.file_uploader("Upload CSV with review column", type="csv")

    MAX_ROWS = 5000

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        row_count = len(df)

        if row_count > MAX_ROWS:
            st.error(f"Uploaded CSV contains {row_count} rows. Maximum allowed is {MAX_ROWS}.")
            st.stop()
        st.dataframe(df, use_container_width=True)

        df["sentiment"] = df["review"].apply(get_sentiment)

        for _, row in df.iterrows():
            insert_feedback(row["review"], row["sentiment"])

        st.success("Feedback successfully added!")


# ================= LOAD STORED DATA =================

data = fetch_feedback()

if data:
    df = pd.DataFrame(data, columns=["review", "sentiment", "date"])
    df["date"] = pd.to_datetime(df["date"])

    positive = (df["sentiment"] > 0).sum()
    negative = (df["sentiment"] < 0).sum()

    trend = df.groupby(df["date"].dt.date)["sentiment"].mean()

    vectorizer = CountVectorizer(stop_words="english", max_features=10)
    X = vectorizer.fit_transform(df["review"])
    keywords = vectorizer.get_feature_names_out()

    # ================= DASHBOARD =================

    with tabs[0]:
        st.subheader("📈 Business Health Overview")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", len(df))
        c2.metric("Positive", positive)
        c3.metric("Negative", negative)

        st.markdown("---")

        col1, col2 = st.columns([2,1])

        with col1:
            st.subheader("Customer Satisfaction Trend")
            st.line_chart(trend)

        with col2:
            fig, ax = plt.subplots()
            ax.bar(["Positive", "Negative"], [positive, negative])
            st.pyplot(fig)

        st.markdown("---")

        st.subheader("Top Customer Issues")
        st.write(list(keywords))


    # ================= AI ASSISTANT =================

    with tabs[1]:
        st.subheader("🤖 AI Business Consultant")
        st.write("Ask questions about customer experience and improvement strategy.")

        user_q = st.text_input("Type your business question here")

        if user_q:
            with st.spinner("Analyzing feedback..."):
                st.success(ask_ai(user_q, df["review"].tolist()))


    # ================= CONTROLS =================

    with tabs[3]:
        st.subheader("⚙ System Controls")

        if st.button("🗑 Clear all stored feedback"):
            clear_data()
            st.success("All data removed successfully.")

        st.warning("This action cannot be undone.")

else:
    st.info("Upload feedback to start building insights.")
