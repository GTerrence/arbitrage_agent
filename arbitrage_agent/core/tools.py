from arbitrage_agent.apps.news_articles.models import NewsArticle
from langchain.tools import tool
import json

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pgvector.django import CosineDistance

from .constants import EMBEDDING_MODEL, EMBEDDING_SIZE


@tool
def search_internal_news(query: str) -> str:
    """
    RAG tools for searching crypto news in internal database.
    """
    # Initialize embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, output_dimensionality=EMBEDDING_SIZE)
    query_vector = embeddings.embed_query(query)

    # Perform Vector Search using pgvector's L2 distance operator (<->)
    results = NewsArticle.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).order_by('distance')[:3] # Get top 3 results

    if not results:
        return "No relevant news found."

    # Format the results for the LLM
    knowledge_base = []
    for article in results:
        knowledge_base.append({
            "title": article.title,
            "summary": article.summary,
            "url": article.url,
            "published_at": article.published_at
        })

    return json.dumps(knowledge_base)
