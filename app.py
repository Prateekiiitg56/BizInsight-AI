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
    st.caption("CSV must contain a column named **review**. Other columns are ignored.")

    uploaded_file = st.file_uploader("Upload CSV with 'review' column", type="csv")

    if uploaded_file:

        #Check 1: The CSV file should be readable and parseable
        try:
            df_upload = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Could not parse the CSV file: {e}")
            st.stop()

        #Check 2: The CSV file should not be completely empty
        if df_upload.empty:
            st.error("❌ The uploaded file is empty. Please upload a CSV with at least one row of data.")
            st.stop()

        #Check 3: normalise column names (to trim accidental whitespace)
        df_upload.columns = df_upload.columns.str.strip()

        #Check 4: 'review' column must exist
        if "review" not in df_upload.columns:
            st.error(
                "❌ A **'review'** column is required but was not found.\n\n"
                f"Columns detected in your file: `{list(df_upload.columns)}`\n\n"
                "💡 Rename the correct column to **review** and re-upload."
            )
            st.stop()

        # Check 5: review column must have usable text data (not just empty or blank)
        df_upload["review"] = df_upload["review"].astype(str).str.strip()
        df_valid = df_upload[df_upload["review"].str.len() > 0].copy()

        if df_valid.empty:
            st.error("❌ The **'review'** column exists but every row is empty or blank. Please check your data.")
            st.stop()

        st.dataframe(df_valid[["review"]], use_container_width=True)

        # ── Sentiment & insert ─────────────────────────────────────────
        df_valid["sentiment"] = df_valid["review"].apply(get_sentiment)

        for _, row in df_valid.iterrows():
            insert_feedback(row["review"], row["sentiment"])

        st.success(f"🎉 {len(df_valid)} review(s) successfully saved to the database!")


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
