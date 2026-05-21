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

api_key = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("⚠️ OPENROUTER_API_KEY environment variable not set. Please create a .env file with your API key.")
    st.stop()

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
    """Safely compute sentiment polarity, returning 0.0 for invalid inputs."""
    if text is None or not isinstance(text, str) or text.strip() == "":
        return 0.0
    return TextBlob(text).sentiment.polarity


def ask_ai(question, reviews):
    """Send a question to the AI model with error handling for API failures."""
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
        logger.error(f"AI request failed: {e}")
        return "⚠️ AI request failed. Please try again later."


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


# ================= DATA UPLOAD =================

with tabs[2]:
    st.subheader("📂 Upload Customer Reviews")

    uploaded_file = st.file_uploader("Upload CSV with review column", type="csv")

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
                    st.dataframe(df)

                    # Clean review data before processing
                    df["review"] = df["review"].astype(str).str.strip()
                    df = df[df["review"] != ""]
                    df = df[df["review"].str.lower() != "nan"]

                    df["sentiment"] = df["review"].apply(get_sentiment)

                    records = list(zip(df["review"].tolist(), df["sentiment"].tolist()))
                    insert_count, skip_count = insert_feedback_bulk(records)

                    st.success(f"✅ {insert_count} reviews added successfully!")
                    if skip_count > 0:
                        st.warning(f"⚠️ {skip_count} empty or invalid reviews were skipped.")


# ================= LOAD STORED DATA =================

data = fetch_feedback()

if data:
    df = pd.DataFrame(data, columns=["review", "sentiment", "date"])
    df["date"] = pd.to_datetime(df["date"])

    positive = (df["sentiment"] > 0).sum()
    negative = (df["sentiment"] < 0).sum()

    trend = df.groupby(df["date"].dt.date)["sentiment"].mean()

    # Safe keyword extraction — guard against empty review corpus
    keywords = []
    valid_reviews = df["review"].dropna().astype(str).str.strip()
    valid_reviews = valid_reviews[valid_reviews != ""]
    if len(valid_reviews) > 0:
        try:
            vectorizer = CountVectorizer(stop_words="english", max_features=10)
            X = vectorizer.fit_transform(valid_reviews)
            keywords = vectorizer.get_feature_names_out()
        except ValueError:
            keywords = []

    # ================= DASHBOARD =================

    with tabs[0]:
        st.subheader("📈 Business Health Overview")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", len(df))
        c2.metric("Positive", positive)
        c3.metric("Negative", negative)

        st.markdown("---")

        # Create chart (displayed in dashboard, saved to temp file only when PDF is requested)
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.bar(
            ["Positive", "Negative"],
            [positive, negative]
        )
        plt.tight_layout()

        if st.button("Generate PDF Report"):
            chart_path = None
            pdf_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    chart_path = tmpfile.name
                    fig.savefig(chart_path)

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

        # Dashboard visuals
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Customer Satisfaction Trend")
            st.line_chart(trend)

        with col2:
            st.pyplot(fig)
            plt.close(fig)  # Prevent matplotlib memory leak
            st.markdown("---")

        st.subheader("Top Customer Issues")
        if len(keywords) > 0:
            st.write(list(keywords))
        else:
            st.info("No keywords found. Upload more reviews for keyword analysis.")


    # ================= AI ASSISTANT =================

    with tabs[1]:
        st.subheader("🤖 AI Business Consultant")
        st.write("Ask questions about customer experience and improvement strategy.")

        user_q = st.text_input("Type your business question here")

        if user_q:
            with st.spinner("Analyzing feedback..."):
                result = ask_ai(user_q, df["review"].tolist())
                if result.startswith("⚠️"):
                    st.error(result)
                else:
                    st.success(result)


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
