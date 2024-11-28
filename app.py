import streamlit as st
import requests
from newspaper import Article
from premai import Prem
import nltk
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

nltk.download('punkt', quiet=True)

# Retrieve API keys from Streamlit secrets
API_KEY = st.secrets["PREM_API_KEY"]
PROJECT_ID = st.secrets["PREM_PROJECT_ID"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# Initialize Prem client
client = Prem(api_key=API_KEY)

# Function to search for financial news
def search_financial_news(company_name, company_ticker):
    keywords = f'"{company_name}" OR {company_ticker} AND (earnings OR revenue OR profit OR loss OR "financial results" OR stock OR shares)'
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')  # Last 7 days
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={keywords}&"
        f"from={from_date}&"
        f"sortBy=publishedAt&"
        f"language=en&"
        f"apiKey={NEWS_API_KEY}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return articles
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

# Function to scrape news content using BeautifulSoup
def scrape_news(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([para.get_text() for para in paragraphs])
        if not text or len(text) < 200:
            return "Error: Article content is too short or unavailable."
        return text
    except Exception as e:
        return f"Error scraping the news: {e}"

# Function to summarize news with sentiment analysis
def summarize_news(content):
    messages = [
        {
            "role": "user",
            "content": (
                "Please read the following article and do the following:\n"
                "1. Summarize the key financial points, highlighting any significant positive or negative information about the company's performance.\n"
                "2. Analyze the overall sentiment of the article (positive, negative, or neutral) regarding the company's financial outlook.\n\n"
                f"Article Content:\n{content}"
            ),
        }
    ]
    try:
        response = client.chat.completions.create(
            project_id=PROJECT_ID,
            messages=messages,
            temperature=0.7,
            max_tokens=700,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error summarizing the news: {e}"

# Function to aggregate summaries and sentiments
def aggregate_summaries(summaries):
    combined_summaries = "\n\n".join(summaries)
    messages = [
        {
            "role": "user",
            "content": (
                "Based on the following summaries and sentiment analyses of recent news articles about the company, "
                "provide an overall analysis of the company's current financial situation. Highlight key positive and negative factors that may influence investment decisions. "
                "Do not provide any direct investment advice.\n\n"
                f"{combined_summaries}"
            ),
        }
    ]
    try:
        response = client.chat.completions.create(
            project_id=PROJECT_ID,
            messages=messages,
            temperature=0.7,
            max_tokens=700,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error aggregating summaries: {e}"

# Streamlit app layout
st.title("Stock News Analyzer/Summarizer")
st.subheader("Objective: Better Investment Decisions")
st.write("""
- Scrape the latest news about a given company
- Summarize the news with key financial points and sentiment analysis
- Provide an overall analysis of the company's financial situation
""")

# Input fields for company name and ticker symbol
company_name = st.text_input("Enter the company name:")
company_ticker = st.text_input("Enter the company ticker symbol:")

if st.button("Analyze News"):
    if company_name and company_ticker:
        st.info("Searching for financial news...")
        articles = search_financial_news(company_name, company_ticker)

        if not articles:
            st.warning("No relevant articles found. Try another company name or ticker symbol.")
        else:
            st.success(f"Found {len(articles)} articles. Processing the top 3.")
            summaries = []

            for idx, article in enumerate(articles[:3]):  # Process top 3 articles
                url = article["url"]
                st.write(f"**Article {idx + 1}: {article['title']}**")
                st.write(f"Source: {article['source']['name']}")
                st.write(f"Published at: {article['publishedAt']}")
                st.write(f"URL: {url}")

                # Scrape the article content
                st.info(f"Scraping Article {idx + 1}...")
                content = scrape_news(url)
                if "Error" in content:
                    st.error(content)
                    continue

                # Summarize the article content with sentiment analysis
                st.info(f"Summarizing Article {idx + 1}...")
                summary = summarize_news(content)
                if "Error" in summary:
                    st.error(summary)
                else:
                    st.success(f"Article {idx + 1} summarized!")
                    st.text_area(f"Summary and Sentiment of Article {idx + 1}", summary, height=200)
                    summaries.append(summary)

            # Aggregate summaries
            if summaries:
                st.info("Creating a comprehensive analysis...")
                final_summary = aggregate_summaries(summaries)
                if "Error" in final_summary:
                    st.error(final_summary)
                else:
                    st.success("Comprehensive analysis generated!")
                    st.subheader("Overall Financial Analysis")
                    st.write(final_summary)
    else:
        st.error("Please enter both the company name and ticker symbol.")

# Disclaimer
st.write("---")
st.write("**Disclaimer:** This analysis is for informational purposes only and should not be construed as financial advice. Please conduct your own research and consult with a professional advisor before making any investment decisions.")
