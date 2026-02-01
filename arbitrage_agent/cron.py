import os
import django
from rq import cron

# Setup Django environment to allow importing models in tasks
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arbitrage_agent.settings")
django.setup()

from arbitrage_agent.apps.news_articles.utils import fetch_and_store_news

# Register the cron job
cron.register(
    fetch_and_store_news,
    cron="0 * * * *",  # Run at the start of every hour
    kwargs={'batch_size': 20, 'commit': True},
    queue_name="default",
)
