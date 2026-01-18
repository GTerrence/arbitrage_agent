import logging
import feedparser
from dateutil import parser
from django.conf import settings
from django.db import IntegrityError, DatabaseError
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from arbitrage_agent.core.constants import EMBEDDING_MODEL, EMBEDDING_SIZE
from arbitrage_agent.apps.news_articles.models import NewsArticle

logger = logging.getLogger(__name__)


def fetch_and_store_news(batch_size: int = 20, commit: bool = True):
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=settings.GEMINI_API_KEY, output_dimensionality=EMBEDDING_SIZE)
    except ValueError as e:
        logger.error(f"Invalid configuration for embeddings: {e}")
        return
    except Exception as e: # Catching broader init errors (like connection during validation if applicable)
        logger.exception("Failed to initialize GoogleGenerativeAIEmbeddings.")
        return

    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
             # bozo_exception can be anything, often SAXParseException or similar encoding errors
            logger.warning(f"Feed parsing warning: {feed.bozo_exception}")
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to parse RSS feed from {url}: {e}")
        return

    logger.info(f"Found {len(feed.entries)} articles in feed.")

    # Filter out existing articles efficiently
    entries_to_process = feed.entries[:batch_size]
    if not entries_to_process:
        logger.info("No entries to process.")
        return

    feed_urls = [entry.link for entry in entries_to_process]
    existing_urls = set(NewsArticle.objects.filter(url__in=feed_urls).values_list('url', flat=True))

    new_articles = []

    for entry in entries_to_process:
        if entry.link in existing_urls:
            continue

        logger.info(f"Processing: {entry.title}")

        try:
            published_at = parser.parse(entry.published)
        except (ValueError, TypeError, parser.ParserError) as e:
            logger.error(f"Failed to parse date '{entry.published}' for article '{entry.title}': {e}")
            continue

        new_articles.append(NewsArticle(
            title=entry.title,
            summary=entry.summary,
            url=entry.link,
            published_at=published_at
        ))

    # Embedding
    text_to_embed = [f"{article.title} {article.summary}" for article in new_articles]
    try:
        vectors = embeddings.embed_documents(text_to_embed)
    except (ValueError, IndexError) as e:
        # embedding models often raise ValueError for empty inputs or inputs > context window
        logger.error(f"Failed to embed article: {e}")
        return
    except Exception as e:
        # We still catch generic here because external API calls can raise diverse socket/timeout errors
        # and we don't want to crash the whole batch for one network blip.
        # ensuring we log the specific type helps.
        logger.error(f"Unexpected API error embedding: {type(e).__name__} - {e}")
        return

    for article, vector in zip(new_articles, vectors):
        article.embedding = vector

    if commit and new_articles:
        try:
            NewsArticle.objects.bulk_create(new_articles, batch_size=100)
            logger.info(f"Successfully ingested {len(new_articles)} news articles!")
        except IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
        except DatabaseError as e:
            logger.error(f"Database error during bulk create: {e}")
    elif not new_articles:
        logger.info("No new articles to ingest.")
