import feedparser
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from agents.models import NewsArticle
from dateutil import parser


def fetch_and_store_news(batch_size: int = 20, commit: bool = True):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    feed = feedparser.parse(url)

    print(f"Found {len(feed.entries)} articles...")
    new_articles = []
    current_article_urls = set(NewsArticle.objects.values_list('url', flat=True))

    for entry in feed.entries[:batch_size]:
        if entry.link in current_article_urls:
            continue

        print(f"Processing: {entry.title}")

        # Embedding
        text_to_embed = f"{entry.title} {entry.summary}"
        vector = embeddings.embed_query(text_to_embed)

        new_articles.append(NewsArticle(
            title=entry.title,
            summary=entry.summary,
            url=entry.link,
            published_at=parser.parse(entry.published),
            embedding=vector
        ))
    if commit:
        NewsArticle.objects.bulk_create(new_articles, batch_size=100)
    print("Successfully ingested news!")
