import os

from dotenv import load_dotenv
load_dotenv()

import logging
import hashlib
import uuid
import re
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from forecasting import forecast_sentiment

from email_alerts import send_negative_alert

load_dotenv()
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


import streamlit as st
st.set_page_config(page_title="BizInsight AI", layout="wide")
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer

from textblob import TextBlob
from database import insert_feedback, fetch_feedback, clear_data
from openai import OpenAI

from database import insert_feedback, fetch_feedback, clear_data

from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIError,
)

from sentiment import analyze

# ---------- Chimera AI Client ----------
from textblob import TextBlob
from database import (
    insert_feedback,
    fetch_feedback,
    clear_data,
)
from database import insert_feedback, fetch_feedback, clear_data
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from clustering.run_clustering import run_pipeline
from clustering.vectorize import load_model

from database import (
    get_workspace_feedback,
    initialize_database,
    insert_feedback,
    insert_feedback_bulk,
    fetch_feedback,
    fetch_all_feedback,
    fetch_all_users,
    clear_data,
    delete_user
)
from auth import is_logged_in, get_current_user, logout, show_auth_page, show_setup_wizard
from database import no_users_exist


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
if "messages" not in st.session_state:
    st.session_state.messages=[]

tabs = st.tabs(["📊 Dashboard", "🤖 AI Assistant", "📂 Data Upload", "⚙ Controls"])


# ================= FUNCTIONS =================

# --- Email Alert State ---
if "alert_email" not in st.session_state:
    st.session_state.alert_email = current_user.get("email", "")


# ─── OpenAI Client ───────────────────────────────────────────────────────────


def get_sentiment(text):
    return TextBlob(text).sentiment.polarity


# ================= AI ASSISTANT =================

# ================= AI ASSISTANT =================

with tabs[1]:

    st.subheader("🤖 AI Business Assistant")

    # Show previous messages

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.write(message["content"])
    st.empty()

    # Chat input at bottom

    question = st.chat_input(
        "Ask business insights question"
    )
    st.components.v1.html(
    """
    <script>
        const input = parent.document.querySelector('textarea');
        if (input) {
            input.focus();
        }
    </script>
    """,
    height=0,
)


    if question:
        with st.chat_message("user"):
         st.write(question)

        # Save user message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        if client is None:
            st.warning("AI features unavailable because API key is missing.")

        else:

            data = fetch_feedback()

            if not data:
                st.warning("No feedback data available.")

            else:

                df_ai = pd.DataFrame(
                    data,
                    columns=["review", "sentiment", "date"]
                )

                reviews_text = "\n".join(
                    df_ai["review"].astype(str).tolist()
                )

                prompt = f"""
You are a business intelligence assistant.

def send_alert_email(recipient_email, subject, body):
    """Sends an email alert regarding sentiment spikes."""
    try:
        sender_email = st.secrets["email_credentials"]["sender_email"]
        password = st.secrets["email_credentials"]["app_password"]
    except (KeyError, FileNotFoundError):
        st.error("Email credentials not found in secrets. Cannot send alert.")
        return False

    if not recipient_email:
        st.warning("Alert email recipient not set. Skipping email notification.")
        return False

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        st.success(f"Negative sentiment alert sent to {recipient_email}!")
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def clean_text_for_sentiment(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'#', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def ask_ai(question, reviews):
    context = "\n".join(reviews[:40])

    prompt = f"""You are a business intelligence assistant.


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

                MAX_REVIEWS_FOR_AI = 200
                total_reviews_count = len(df_ai)
                sampled_reviews = df_ai["review"].astype(str).tolist()[:MAX_REVIEWS_FOR_AI]
                reviews_text = "\n".join(sampled_reviews)

                prompt = f"""
You are a business intelligence assistant.
Analysing a sample of {len(sampled_reviews)} most recent reviews (out of {total_reviews_count} total).

Customer reviews:
{reviews_text}

Question:
{question}
"""


                try:

                    response = client.chat.completions.create(
                        model="openai/gpt-3.5-turbo",
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

                    # Save assistant response

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )
                    st.rerun()

                    # Show assistant response

                     

                except Exception as e:
                    st.error(f"Error generating AI response: {str(e)}")

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

        return response.choices[0].message.content

    except AuthenticationError:
        return "Authentication failed."

    except RateLimitError:
        return "Rate limit exceeded."

    except APITimeoutError:
        return "Request timed out."

    except APIConnectionError:
        return "Connection error."

    except APIError:
        return "AI service unavailable."

    except Exception as e:
        return f"Error generating AI response: {str(e)}"
    
def make_pdf(df, trend, keywords):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("BizInsight AI Report", styles["Title"]))
    content.append(Paragraph("Generated: " + str(datetime.now().strftime("%Y-%m-%d %H:%M")), styles["Normal"]))
    content.append(Paragraph("Total Reviews: " + str(len(df)), styles["Normal"]))
    content.append(Paragraph("Positive: " + str((df["sentiment"] > 0).sum()), styles["Normal"]))
    content.append(Paragraph("Negative: " + str((df["sentiment"] < 0).sum()), styles["Normal"]))

    fig1, ax1 = plt.subplots()
    ax1.plot(trend.index, trend.values)
    ax1.set_title("Sentiment Trend")
    img1 = io.BytesIO()
    fig1.savefig(img1, format="png")
    plt.close(fig1)
    img1.seek(0)
    content.append(Image(img1, width=400, height=200))

    fig2, ax2 = plt.subplots()
    ax2.bar(["Positive", "Negative"], [(df["sentiment"] > 0).sum(), (df["sentiment"] < 0).sum()])
    ax2.set_title("Positive vs Negative")
    img2 = io.BytesIO()
    fig2.savefig(img2, format="png")
    plt.close(fig2)
    img2.seek(0)
    content.append(Image(img2, width=400, height=200))

    content.append(Paragraph("Top Keywords: " + ", ".join(keywords), styles["Normal"]))
    pdf.build(content)
    buffer.seek(0)
    return buffer.read()


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


        if "date" not in df.columns:
            st.error("CSV must contain a 'date' column.")
            st.stop()
        df["date"] = pd.to_datetime(df["date"])
        st.dataframe(df, width='stretch')
        if "review" not in df.columns:
            st.error("CSV must contain a 'review' column.")

        else:

            df = df.dropna(subset=["review"])
            df["review"] = df["review"].astype(str).str.strip()
            df = df[df["review"] != ""]

            if df.empty:

                st.warning("No valid reviews found after cleaning.")

            else:
                with st.spinner("Analyzing sentiment..."):
                    df["sentiment"] = df["review"].apply(get_sentiment)
        if st.session_state.get("last_upload_hash") != file_hash:
            df = None
            encodings_to_try = ['utf-8', 'utf-16', 'latin1', 'cp1252']

            for encoding in encodings_to_try:
                try:
                    uploaded_file.seek(0) # Always reset file pointer before reading
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
            
            if df is None:
                st.error("Unable to read CSV file. Please ensure it is not corrupted and uses a standard encoding such as UTF-8 or Latin-1.")
            else:
                st.dataframe(df, use_container_width=True)

                for _, row in df.iterrows():
                    insert_feedback(
                        row["review"],
                        row["sentiment"],
                        row["date"].strftime("%Y-%m-%d")
                    )
                    inserted_count += 1
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
                        reviews_data = list(zip(df["review"], df["sentiment"]))
                        insert_feedback_bulk(reviews_data, user_id=current_user["id"])
                        st.session_state["last_upload_hash"] = file_hash
                        st.success(f"{len(df)} feedback entries successfully added!")

                        # Check for negative sentiment spike and send alert
                        new_negative_percent = round((df[df["sentiment"] < 0].shape[0] / df.shape[0]) * 100, 2)
                        if new_negative_percent > 30: # Threshold for alert
                            subject = "BizInsight AI Alert: Negative Sentiment Spike Detected"
                            body = (
                                f"Hello,\n\nA recent data upload has shown a significant spike in negative sentiment.\n\n"
                                f"Negative Sentiment in new batch: {new_negative_percent}%\n\n"
                                f"Please log in to the BizInsight AI dashboard to analyze the feedback and take appropriate action.\n\n"
                                f"Regards,\nThe BizInsight AI Team"
                            )
                            send_alert_email(st.session_state.alert_email, subject, body)

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

                st.success(f"{inserted_count} feedback entries successfully added!")

# ================= FETCH DATA =================

data = fetch_feedback()

if data:

    df = pd.DataFrame(
        data,
        columns=["review", "sentiment", "date"]
    )


if current_user["workspace_type"] == "corporate":

    data = get_workspace_feedback(
        current_user["workspace_id"]
    )

else:

    data = fetch_feedback(
        user_id=current_user["id"]
    )

df = pd.DataFrame(data, columns=["review", "sentiment", "date"])

if not df.empty:

    df["date"] = pd.to_datetime(df["date"])

    # Sentiment Counts

    positive = (df["sentiment"] > 0).sum()
    negative = (df["sentiment"] < 0).sum()
    neutral = (df["sentiment"] == 0).sum()

    total_reviews = len(df)

    # Percentages


    # These are now safe from ZeroDivisionError because total_reviews > 0

    positive_percent = round((positive / total_reviews) * 100, 2)
    negative_percent = round((negative / total_reviews) * 100, 2)
    neutral_percent = round((neutral / total_reviews) * 100, 2)

    # Trend

    # Existing sentiment trend
    trend = df.groupby(df["date"].dt.date)["sentiment"].mean()

    # Keyword Extraction

    # Keywords

    # =========================================
    # NEGATIVE REVIEW SPIKE DETECTION
    # =========================================

    # Only negative reviews
    negative_df = df[df["sentiment"] < 0]

    # Daily negative review counts
    negative_trend = (
        negative_df
        .groupby(negative_df["date"].dt.date)
        .size()
    )

    # Rolling statistics
    rolling_mean = negative_trend.rolling(window=3).mean()

    rolling_std = negative_trend.rolling(window=3).std()

    # Threshold-based anomaly detection
    
    anomalies = negative_trend[
        negative_trend > (rolling_mean + rolling_std)
    ]

    # =========================================


    reviews = df["review"].dropna()

    if reviews.empty or (

        reviews.apply(lambda x: isinstance(x, str)).all() and
        reviews.str.strip().eq("").all()

        reviews.apply(lambda x: isinstance(x, str)).all()
        and reviews.str.strip().eq("").all()

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



            keyword_df = pd.DataFrame({
                "Keyword": keywords,
                "Frequency": keyword_counts
            })


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



        if not anomalies.empty:
            st.error(
                f"⚠️ {len(anomalies)} negative sentiment spike(s) detected!"
            )

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", len(df))
        c2.metric("Positive", positive)
        c3.metric("Negative", negative)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Reviews", total_reviews)
        c2.metric("Positive %", f"{positive_percent}%")
        c3.metric("Negative %", f"{negative_percent}%")
        c4.metric("Neutral %", f"{neutral_percent}%")

        st.markdown("---")

        # Trend Chart


        col1, col2 = st.columns([2,1])

        with col1:

            st.subheader("Customer Satisfaction Trend")
            st.area_chart(trend)

        with col2:



            fig3, ax3 = plt.subplots(figsize=(3.2, 3.2))


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

            st.pyplot(fig3)
            plt.close(fig3)

            st.markdown("---")

        # Histogram

        st.subheader("📊 Sentiment Score Distribution")

        col_small, _ = st.columns([1.5, 4])

        with col_small:
            fig2, ax2 = plt.subplots(figsize=(2.8, 2.1))
            try:
                ax2.hist(df["sentiment"], bins=10)
                
                ax2.set_xlabel("Score", fontsize=8)
                
                ax2.set_ylabel("Freq", fontsize=8)
                
                ax2.tick_params(axis='both', labelsize=7)
                
                st.pyplot(fig2)
            finally:
                # Ensure matplotlib resources are always released
                plt.close(fig2)
            fig, ax = plt.subplots()
            ax.pie([positive, negative, neutral], labels=["Positive","Negative","Neutral"], autopct="%1.1f%%")
            st.pyplot(fig)
            plt.close(fig)

        st.subheader("📊 Sentiment Distribution")
        fig2, ax2 = plt.subplots()
        ax2.hist(df["sentiment"], bins=20)
        ax2.set_xlabel("Sentiment Score")
        ax2.set_ylabel("Frequency")
        st.pyplot(fig2)
        plt.close(fig2)

        with col1:
            st.subheader("Negative Review Spike Detection")
            
            fig2, ax2 = plt.subplots(figsize=(10,4))
            
            # Main negative trend line
            ax2.plot(
                negative_trend.index,
                negative_trend.values,
                marker="o"
            )
            
            # Highlight anomalies
            ax2.scatter(
                anomalies.index,
                anomalies.values,
                color="red",
                s=220,
                marker="X",
                label="Anomaly"
            )
            
            ax2.legend()
            
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Negative Reviews")
            ax2.set_title("Anomaly Detection in Negative Reviews")
            
            st.pyplot(fig2)

        with col2:
            st.pyplot(fig)
            plt.close(fig)  # Fix: prevents matplotlib memory leak
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
            st.pyplot(fig3)
            plt.close(fig3)

        st.markdown("---")
        st.markdown("---")
        st.subheader("📈 Future Sentiment Forecast")

        forecast_days = st.selectbox(
            "Select Forecast Horizon",
            [7, 14, 30]
        )

        try:

            forecast_df = forecast_sentiment(
                df,
                forecast_days
            )

            st.line_chart(
                forecast_df.set_index("date")
            )

            current_sentiment = round(
                df["sentiment"].mean(),
                3
            )

            future_sentiment = round(
                forecast_df["predicted_sentiment"].mean(),
                3
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Current Avg Sentiment",
                current_sentiment
            )

            col2.metric(
                f"{forecast_days}-Day Forecast",
                future_sentiment,
                round(
                    future_sentiment - current_sentiment,
                    3
                )
            )

            if future_sentiment < -0.2:
                st.error(
                    "⚠️ Forecast suggests future customer dissatisfaction."
                )

            elif future_sentiment > 0.2:
                st.success(
                    "✅ Forecast suggests improving customer sentiment."
                )

            else:
                st.info(
                    "ℹ️ Forecast suggests stable customer sentiment."
                )

        except ValueError as e:
            st.warning(str(e))
        
        pdf_file = make_pdf(df, trend, list(keywords))
        st.download_button("Download PDF Report", pdf_file, file_name="report.pdf", mime="application/pdf")


        st.subheader("📊 Sentiment Score Distribution")

        col_small, _ = st.columns([1.5, 4])

        with col_small:

            fig2, ax2 = plt.subplots(figsize=(2.8, 2.1))

            ax2.hist(df["sentiment"], bins=10)

            ax2.set_xlabel("Score", fontsize=8)
            ax2.set_ylabel("Freq", fontsize=8)

            ax2.tick_params(axis='both', labelsize=7)

            st.pyplot(fig2)

        # Keywords

        st.markdown("---")

        # Keywords

        st.subheader("Top Customer Issues / Keywords")



    # ================= DYNAMIC KEYWORD EXTRACTION & FILTERING =================
        col_filter, _ = st.columns([1, 3])
        with col_filter:
            sentiment_filter = st.selectbox(
                "Select Sentiment Category for Keywords",
                ["All Reviews", "Positive Reviews", "Neutral Reviews", "Negative Reviews"]
            )

        # Filter the dataframe dynamically based on selection
        if sentiment_filter == "Positive Reviews":
            filtered_df = df[df["sentiment"] > 0.1]
        elif sentiment_filter == "Negative Reviews":
            filtered_df = df[df["sentiment"] < -0.1]
        elif sentiment_filter == "Neutral Reviews":
            filtered_df = df[(df["sentiment"] >= -0.1) & (df["sentiment"] <= 0.1)]
        else:
            filtered_df = df.copy()

        reviews = filtered_df["review"].dropna()

        if reviews.empty or reviews.str.strip().eq("").all():
            keywords = []
            keyword_counts = []

        else:
            vectorizer = CountVectorizer(stop_words="english", max_features=10)

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

        keyword_df = pd.DataFrame({"Keyword": keywords, "Frequency": keyword_counts}).sort_values(by="Frequency", ascending=False).reset_index(drop=True)
        # Sort by frequency, but keep the numbering intact regardless of its position in the dataframe
    
        st.dataframe(keyword_df, use_container_width=True)


        st.dataframe(keyword_df, use_container_width=True)

    # ================= CONTROLS =================

    with tabs[3]:


        st.subheader("⚙ System Controls")

        st.subheader("⚙ System Controls")
        
        st.markdown("---")
        st.subheader("📧 Email Alerts")
        st.session_state.alert_email = st.text_input(
            "Recipient email for alerts",
            value=st.session_state.alert_email,
            placeholder="Enter your email to receive alerts"
        )
        st.info("Alerts for negative sentiment spikes will be sent to this email.")
        st.markdown("---")

        st.warning("⚠️ Clearing data permanently deletes all your stored reviews. This cannot be undone.")

        if "confirm_clear" not in st.session_state:
            st.session_state["confirm_clear"] = False

        if not st.session_state["confirm_clear"]:
            if st.button("🗑️ Clear my feedback data"):
                st.session_state["confirm_clear"] = True
                st.rerun()
        else:
            st.error("Are you sure? All your reviews will be permanently deleted.")
            col1, col2 = st.columns(2)
            if col1.button("✅ Yes, delete everything"):
                clear_data(user_id=current_user["id"])
                st.session_state["confirm_clear"] = False
                st.session_state.pop("last_upload_hash", None)
                st.success("All your data has been removed.")
                st.rerun()
            if col2.button("❌ Cancel"):
                st.session_state["confirm_clear"] = False
                st.rerun()

#else:
#    st.info("Upload feedback to start building insights.")


        if st.button("🗑 Clear all stored feedback"):

            clear_data()

            st.session_state.data_cleared = True
            st.rerun()

        st.warning("This action cannot be undone.")


else:
    st.info("Upload feedback to start building insights.")

        if not all_feedback:
            st.info("No feedback in the system yet.")
        else:
            df_all = pd.DataFrame(all_feedback, columns=["review", "sentiment", "date", "uploaded_by"])
            st.dataframe(df_all, use_container_width=True)

