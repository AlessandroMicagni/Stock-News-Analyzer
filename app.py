import os
from dotenv import load_dotenv
import streamlit as st
import requests
from newspaper import Article
from premai import Prem

load_dotenv()  # Load environment variables from .env file

# Retrieve API keys from environment variables
API_KEY = os.getenv("PREM_API_KEY")
PROJECT_ID = os.getenv("PREM_PROJECT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Check if API keys are retrieved successfully
if not API_KEY:
    st.error("PREM_API_KEY environment variable is not set.")
if not PROJECT_ID:
    st.error("PREM_PROJECT_ID environment variable is not set.")
if not NEWS_API_KEY:
    st.error("NEWS_API_KEY environment variable is not set.")

# Initialize Prem client
client = Prem(api_key=API_KEY)

# Function to search for financial news
def search_financial_news(company_name):
    keywords = f"{company_name} earnings OR revenue OR profit OR loss OR financial results OR stock OR shares"
    url = f"https://newsapi.org/v2/everything?q={keywords}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return articles
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

# Function to scrape news content using newspaper library
def scrape_news(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Error scraping the news: {e}"

# Function to summarize news
def summarize_news(content):
    messages = [
        {"role": "user", "content": f"Summarize this article into bullet points: {content}"}
    ]
    try:
        response = client.chat.completions.create(
            project_id=PROJECT_ID,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error summarizing the news: {e}"

# Function to aggregate summaries
def aggregate_summaries(summaries):
    messages = [
        {"role": "user", "content": f"Combine these summaries into a comprehensive financial overview: {summaries}"}
    ]
    try:
        response = client.chat.completions.create(
            project_id=PROJECT_ID,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error aggregating summaries: {e}"

# Streamlit app layout
st.title("Stock News Analyzer/Summarizer")
st.subheader("Objective: Better Investment Decisions")
st.write("""
- Scrape the latest news about a given company
- Summarize the news (list of bullet points: bad and good)
- Suggest what investment decision to take (buy/sell)
""")

# Input field for company name
company_name = st.text_input("Enter the company name:")

if st.button("Analyze News"):
    if company_name:
        st.info("Searching for financial news...")
        articles = search_financial_news(company_name)

        if not articles:
            st.warning("No relevant articles found. Try another company name.")
        else:
            st.success(f"Found {len(articles)} articles. Processing the top 3.")
            summaries = []

            for idx, article in enumerate(articles[:3]):  # Process top 3 articles
                url = article["url"]
                st.write(f"**Article {idx + 1}: {article['title']}**")
                st.write(f"Source: {article['source']['name']}")
                st.write(f"URL: {url}")

                # Scrape the article content
                st.info(f"Scraping Article {idx + 1}...")
                content = scrape_news(url)
                if "Error" in content:
                    st.error(content)
                    continue

                # Summarize the article content
                st.info(f"Summarizing Article {idx + 1}...")
                summary = summarize_news(content)
                if "Error" in summary:
                    st.error(summary)
                else:
                    st.success(f"Article {idx + 1} summarized!")
                    st.text_area(f"Summary of Article {idx + 1}", summary, height=150)
                    summaries.append(summary)

            # Aggregate summaries
            if summaries:
                st.info("Creating a comprehensive summary...")
                final_summary = aggregate_summaries(" ".join(summaries))
                if "Error" in final_summary:
                    st.error(final_summary)
                else:
                    st.success("Comprehensive summary generated!")
                    st.text_area("Final Summary", final_summary, height=200)
    else:
        st.error("Please enter a company name.")