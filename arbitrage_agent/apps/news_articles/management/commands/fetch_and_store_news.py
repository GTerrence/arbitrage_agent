from django.core.management.base import BaseCommand, CommandParser

from arbitrage_agent.apps.news_articles.utils import fetch_and_store_news


class Command(BaseCommand):
    help = 'Fetches news from RSS and stores them'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--batch-size',
            type=int,
            default=20,
            help='Number of articles to fetch and store in one batch'
        )

    def handle(self, *args, **options):
        # The command just triggers the logic
        fetch_and_store_news(batch_size=options['batch_size'])
        self.stdout.write(self.style.SUCCESS('Command initiated successfully'))
