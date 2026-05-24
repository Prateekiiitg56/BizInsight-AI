import os
import tempfile
import logging
from pdf_generator import create_pdf
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

import streamlit as st
st.set_page_config(page_title="BizInsight AI", layout="wide")
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob
from database import insert_feedback_bulk, fetch_feedback, clear_data
from openai import OpenAI

# ---------- Constants ----------

MAX_CSV_SIZE_MB = 10
REQUIRED_COLUMNS = ["review"]

# ---------- Chimera AI Client ----------

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.warning("OPENROUTER_API_KEY not found. AI Assistant features will be disabled.")
    client = None
else:
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

# ================= FUNCTIONS =================

def get_sentiment(text):
    """Safely compute sentiment polarity, returning 0.0 for invalid inputs."""
    if text is None or not isinstance(text, str) or text.strip() == "":
        return 0.0
    return TextBlob(text).sentiment.polarity


def validate_csv(df):
    """Validate uploaded CSV has required columns and valid data.
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if df.empty:
        return False, "The uploaded CSV file is empty. Please upload a file with data."

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return False, f"Missing required column(s): {', '.join(missing_cols)}. Your CSV must contain a 'review' column."

    # Drop rows where 'review' is null or empty
    valid_reviews = df["review"].dropna().astype(str).str.strip()
    non_empty_count = (valid_reviews != "").sum()
    if non_empty_count == 0:
        return False, "The 'review' column has no valid entries. Please ensure reviews are not empty."

    return True, None


def cleanup_temp_file(file_path):
    """Safely delete a temporary file if it exists."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


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

                reviews_text = "\n".join(df_ai["review"].astype(str).tolist()[:40])

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
                    logger.error(f"AI request failed: {e}")
                    st.error(f"⚠️ AI request failed. Please try again later.")


# ================= DATA UPLOAD =================

with tabs[2]:

    st.subheader("📂 Upload Customer Reviews")

    uploaded_file = st.file_uploader(
        "Upload CSV with review column",
        type="csv"
    )

    if uploaded_file:
        # File size validation
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_CSV_SIZE_MB:
            st.error(f"❌ File too large ({file_size_mb:.1f} MB). Maximum allowed size is {MAX_CSV_SIZE_MB} MB.")
        else:
            try:
                df = pd.read_csv(uploaded_file)
            except Exception as e:
                st.error(f"❌ Failed to parse CSV file: {str(e)}. Please ensure the file is a valid CSV.")
                df = None

            if df is not None:
                is_valid, error_msg = validate_csv(df)
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    st.dataframe(df, use_container_width=True)

                    # Clean review data before processing
                    df["review"] = df["review"].astype(str).str.strip()
                    df = df[df["review"] != ""]
                    df = df[df["review"].str.lower() != "nan"]

                    if df.empty:
                        st.warning("No valid reviews found after cleaning.")
                    else:
                        df["sentiment"] = df["review"].apply(get_sentiment)

                        records = list(zip(df["review"].tolist(), df["sentiment"].tolist()))
                        insert_count, skip_count = insert_feedback_bulk(records)

                        st.success(f"✅ {insert_count} reviews added successfully!")
                        if skip_count > 0:
                            st.warning(f"⚠️ {skip_count} empty or invalid reviews were skipped.")

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

    # Keyword Extraction — guard against empty review corpus

    reviews = df["review"].dropna().astype(str).str.strip()
    reviews = reviews[reviews != ""]

    if reviews.empty:
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
            plt.close(fig2)

        st.markdown("---")

        # PDF Report Generation
        if st.button("Generate PDF Report"):
            chart_path = None
            pdf_path = None
            try:
                fig_pdf, ax_pdf = plt.subplots(figsize=(4, 4))
                ax_pdf.bar(
                    ["Positive", "Negative"],
                    [positive, negative]
                )
                plt.tight_layout()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    chart_path = tmpfile.name
                    fig_pdf.savefig(chart_path)
                plt.close(fig_pdf)

                pdf_path = create_pdf(len(df), positive, negative, chart_path)

                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download Report",
                        data=pdf_file,
                        file_name="bizinsight_report.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                logger.error(f"PDF report generation failed: {e}")
                st.error("❌ Failed to generate report. Please try again.")
            finally:
                cleanup_temp_file(chart_path)
                cleanup_temp_file(pdf_path)

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

        if keyword_df.empty:
            st.info("No keywords found. Upload more reviews for keyword analysis.")
        else:
            st.dataframe(keyword_df, use_container_width=True)

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