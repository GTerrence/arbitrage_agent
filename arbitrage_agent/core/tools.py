from arbitrage_agent.apps.news_articles.models import NewsArticle
from langchain.tools import tool
import json
import requests

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pgvector.django import CosineDistance

from django.conf import settings

from .constants import EMBEDDING_MODEL, EMBEDDING_SIZE


@tool
def search_internal_news(query: str) -> str:
    """
    RAG tools for searching crypto news in internal database.
    """
    def serialize_article(article: NewsArticle) -> dict:
        return {
            "title": article.title,
            "summary": article.summary,
            "url": article.url,
            "published_at": article.published_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    # Initialize embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, output_dimensionality=EMBEDDING_SIZE, api_key=settings.GEMINI_API_KEY)
    query_vector = embeddings.embed_query(query)

    # Perform Vector Search using pgvector's L2 distance operator (<->)
    results = NewsArticle.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).order_by('distance')[:3] # Get top 3 results

    if not results:
        return "No relevant news found."

    # Format the results for the LLM
    knowledge_base = [serialize_article(article) for article in results]

    return json.dumps(knowledge_base)

@tool
def get_crypto_price(ticker: str) -> str:
    """
    Useful for getting the current price of a cryptocurrency.
    Input should be a ticker like 'BTC' or 'ETH'.
    """
    url = f"https://min-api.cryptocompare.com/data/price?fsym={ticker.upper()}&tsyms=USD"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return f"The current price of {ticker} is ${data.get('USD', 'unknown')}"
        else:
            return "Could not fetch price."
    except (ConnectionError, TimeoutError, json.JSONDecodeError) as e:
        return f"Error fetching price: {e}"
