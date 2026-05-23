import os
import tempfile
from pdf_generator import create_pdf
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

try:
    api_key = st.secrets.get("OPENROUTER_API_KEY") or api_key
except Exception:
    pass

client = None

if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

st.title("📊 BizInsight AI")
st.caption("AI-powered customer intelligence platform for business growth")

if "data_cleared" in st.session_state:
    st.success("All data removed successfully.")
    del st.session_state.data_cleared

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
    try:
        response = client.chat.completions.create(
            model="tngtech/deepseek-r1t2-chimera:free",
            messages=[
                {"role": "system", "content": "You provide business intelligence insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: Could not get a response from the AI. Please check your API key or try again later. (Details: {str(e)})"

# ================= DATA UPLOAD =================

with tabs[2]:
    st.subheader("📂 Upload Customer Reviews")

    uploaded_file = st.file_uploader("Upload CSV with review column", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df, width='stretch')
        if "review" not in df.columns:
            st.error("CSV must contain a 'review' column.")
        else:
            df = df.dropna(subset=["review"])

            df["review"] = df["review"].astype(str).str.strip()
            df = df[df["review"] != ""]

            if df.empty:
                st.warning("No valid reviews found after cleaning. Nothing to process.")
            else:
                df["sentiment"] = df["review"].apply(get_sentiment)

                inserted_count = 0

                
                for _, row in df.iterrows():
                    insert_feedback(row["review"], row["sentiment"])
                    inserted_count += 1

                st.success(f"{inserted_count} feedback entries successfully added!")


# ================= LOAD STORED DATA =================

data = fetch_feedback()

if data:
    df = pd.DataFrame(data, columns=["review", "sentiment", "date"])
    df["date"] = pd.to_datetime(df["date"])

    positive = (df["sentiment"] > 0).sum()
    negative = (df["sentiment"] < 0).sum()

    trend = df.groupby(df["date"].dt.date)["sentiment"].mean()

    reviews = df["review"].dropna()

    if reviews.empty or (
        reviews.apply(lambda x: isinstance(x, str)).all() and 
        reviews.str.strip().eq("").all()
    ):
        keywords = []
    else:
        vectorizer = CountVectorizer(stop_words="english", max_features=10)
        try:
            X = vectorizer.fit_transform(reviews)
            keywords = vectorizer.get_feature_names_out()
        except ValueError as e:
            if "empty vocabulary" in str(e).lower():
                keywords = []
            else:
                raise

    # ================= DASHBOARD =================

    with tabs[0]:
        st.subheader("📈 Business Health Overview")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", len(df))
        c2.metric("Positive", positive)
        c3.metric("Negative", negative)

        st.markdown("---")
        # Create chart first
        fig, ax = plt.subplots(figsize=(4,4))

        ax.bar(
            ["Positive", "Negative"],
            [positive, negative]
        )

        plt.tight_layout()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            chart_path = tmpfile.name

            fig.savefig(chart_path)
        if st.button("Generate PDF Report"):

            # THEN create PDF
            pdf_path = create_pdf(len(df), positive, negative, chart_path)

            # Download button
            with open(pdf_path, "rb") as pdf_file:

                st.download_button(
                label="Download Report",
                data=pdf_file,
                file_name="bizinsight_report.pdf",
                mime="application/pdf"
            )

            # Dashboard visuals
        col1, col2 = st.columns([2,1])

        with col1:
            st.subheader("Customer Satisfaction Trend")
            st.line_chart(trend)

        with col2:
            st.pyplot(fig)
            plt.close(fig)  # Fix: prevents matplotlib memory leak
            st.markdown("---")

        st.subheader("Top Customer Issues")
        st.write(list(keywords))


    # ================= AI ASSISTANT =================

    with tabs[1]:
        st.subheader("🤖 AI Business Consultant")
        st.write("Ask questions about customer experience and improvement strategy.")

        user_q = st.text_input("Type your business question here")

        if user_q:
            if client is None:
                st.warning("AI Assistant is unavailable. Please add your OPENROUTER_API_KEY.")
            else:
                with st.spinner("Analyzing feedback..."):
                    st.success(ask_ai(user_q, df["review"].tolist()))


    # ================= CONTROLS =================

    with tabs[3]:
        st.subheader("⚙ System Controls")

        if st.button("🗑 Clear all stored feedback"):
            clear_data()
            st.session_state.data_cleared = True
            st.rerun()

        st.warning("This action cannot be undone.")

else:
    st.info("Upload feedback to start building insights.")
