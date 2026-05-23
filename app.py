import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob

from database import (
    clear_data,
    fetch_feedback,
    initialize_database,
    insert_feedback,
)

st.set_page_config(page_title="BizInsight AI", layout="wide")

load_dotenv()
initialize_database()


# ---------- Chimera AI Client ----------

api_key = st.secrets.get(
    "OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError(
        "OPENROUTER_API_KEY not found in Streamlit secrets or environment variables.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

st.title("📊 BizInsight AI")
st.caption("AI-powered customer intelligence platform for business growth")

if "data_cleared" in st.session_state:
    st.success("All data removed successfully.")
    del st.session_state.data_cleared

tabs = st.tabs(["📊 Dashboard", "🤖 AI Assistant",
               "📂 Data Upload", "⚙ Controls"])

# ================= FUNCTIONS =================


def get_sentiment(text):
    return TextBlob(text).sentiment.polarity


# ================= AI ASSISTANT =================

with tabs[1]:

    st.subheader("🤖 AI Business Assistant")

    question = st.text_area(
        "Ask business insights question",
        placeholder="Example: What are the major customer complaints?"
    )

    if st.button("Generate AI Insight"):

        if client is None:
            st.warning("AI features unavailable because API key is missing.")

        elif question.strip() == "":
            st.warning("Please enter a question.")

        else:

            data = fetch_feedback()

            if not data:
                st.warning("No feedback data available.")

            else:

                df_ai = pd.DataFrame(
                    data,
                    columns=["review", "sentiment", "date"]
                )

                reviews_text = "\n".join(df_ai["review"].astype(str).tolist())

                prompt = f"""
You are a business intelligence assistant.

Customer reviews:
{reviews_text}

Question:
{question}
"""

                try:

                    response = client.chat.completions.create(
                        model="tngtech/deepseek-r1t2-chimera:free",
                        messages=[
                            {
                                "role": "system",
                                "content": "You provide business intelligence insights."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.4
                    )

                    answer = response.choices[0].message.content

                    st.success("AI Insight Generated")
                    st.write(answer)

                except Exception as e:
                    st.error(f"Error generating AI response: {str(e)}")


# ================= DATA UPLOAD =================


with tabs[2]:

    st.subheader("📂 Upload Customer Reviews")

    uploaded_file = st.file_uploader(
        "Upload CSV with review column",
        type="csv"
    )

    if uploaded_file:

        df = pd.read_csv(uploaded_file)

        st.dataframe(df, use_container_width=True)

        if "review" not in df.columns:
            st.error("CSV must contain a 'review' column.")

        else:

            df = df.dropna(subset=["review"])

            df["review"] = df["review"].astype(str).str.strip()
            df = df[df["review"] != ""]

            if df.empty:

                st.warning("No valid reviews found after cleaning.")

            else:

                df["sentiment"] = df["review"].apply(get_sentiment)

                inserted_count = 0

                for _, row in df.iterrows():
                    insert_feedback(row["review"], row["sentiment"])
                    inserted_count += 1

                st.success(
                    f"{inserted_count} feedback entries successfully added!")

# ================= FETCH DATA =================

data = fetch_feedback()

if data:

    df = pd.DataFrame(
        data,
        columns=["review", "sentiment", "date"]
    )

    df["date"] = pd.to_datetime(df["date"])

    # Sentiment Counts

    positive = (df["sentiment"] > 0).sum()
    negative = (df["sentiment"] < 0).sum()
    neutral = (df["sentiment"] == 0).sum()

    total_reviews = len(df)

    # Percentages

    positive_percent = round((positive / total_reviews) * 100, 2)
    negative_percent = round((negative / total_reviews) * 100, 2)
    neutral_percent = round((neutral / total_reviews) * 100, 2)

    # Trend

    trend = df.groupby(df["date"].dt.date)["sentiment"].mean()

    # Keyword Extraction

    reviews = df["review"].dropna()

    if reviews.empty or (
        reviews.apply(lambda x: isinstance(x, str)).all() and
        reviews.str.strip().eq("").all()
    ):
        keywords = []
        keyword_counts = []

    else:

        vectorizer = CountVectorizer(
            stop_words="english",
            max_features=10
        )

        try:

            X = vectorizer.fit_transform(reviews)

            keywords = vectorizer.get_feature_names_out()
            keyword_counts = X.toarray().sum(axis=0)

        except ValueError as e:

            if "empty vocabulary" in str(e).lower():
                keywords = []
                keyword_counts = []

            else:
                raise

    keyword_df = pd.DataFrame({
        "Keyword": keywords,
        "Frequency": keyword_counts
    })

    # ================= DASHBOARD =================

    with tabs[0]:

        st.subheader("📈 Business Health Overview")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Reviews", total_reviews)
        c2.metric("Positive %", f"{positive_percent}%")
        c3.metric("Negative %", f"{negative_percent}%")
        c4.metric("Neutral %", f"{neutral_percent}%")

        st.markdown("---")

        # Trend Chart

        col1, col2 = st.columns([2, 1])

        with col1:

            st.subheader("Customer Satisfaction Trend")
            st.area_chart(trend)

        with col2:

            fig3, ax3 = plt.subplots(figsize=(3.2, 3.2))

            ax3.pie(
                [positive, negative, neutral],
                labels=["Positive", "Negative", "Neutral"],
                autopct="%1.1f%%"
            )

            st.pyplot(fig3)
            plt.close(fig3)

            st.markdown("---")

        # Histogram

        st.subheader("📊 Sentiment Score Distribution")

        col_small, _ = st.columns([1.5, 4])

        with col_small:

            fig2, ax2 = plt.subplots(figsize=(2.8, 2.1))

            ax2.hist(df["sentiment"], bins=10)

            ax2.set_xlabel("Score", fontsize=8)
            ax2.set_ylabel("Freq", fontsize=8)

            ax2.tick_params(axis='both', labelsize=7)

            st.pyplot(fig2)

        st.markdown("---")

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Feedback as CSV",
            data=csv_data,
            file_name="bizinsight_feedback.csv",
            mime="text/csv"
        )

        st.markdown("---")

        # Keywords

        st.subheader("Top Customer Issues / Keywords")

        st.dataframe(keyword_df, use_container_width=True)

    # ================= CONTROLS =================

    with tabs[3]:

        st.subheader("⚙ System Controls")

        st.warning(
            "⚠️ This action cannot be undone. All stored feedback will be permanently deleted.")

        if st.button("🗑 Clear all stored feedback"):
            st.session_state["confirm_clear"] = True

        if st.session_state.get("confirm_clear"):
            st.error("Are you sure? This will permanently delete all feedback data.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, delete everything", type="primary"):
                    clear_data()
                    st.session_state.pop("confirm_clear", None)
                    st.session_state["data_cleared"] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.pop("confirm_clear", None)
                    st.rerun()
else:
    st.info("Upload feedback to start building insights.")