import json
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.utils import timezone
from arbitrage_agent.apps.news_articles.models import NewsArticle
from arbitrage_agent.core.tools import search_internal_news

class SearchInternalNewsToolTest(TestCase):

    @patch('arbitrage_agent.core.tools.GoogleGenerativeAIEmbeddings')
    @patch('arbitrage_agent.core.tools.NewsArticle')
    def test_search_internal_news_success(self, mock_news_article: MagicMock, mock_embeddings_cls: MagicMock):
        """Test search_internal_news returns formatted JSON when articles are found."""

        # Mock Embeddings
        mock_embedding_instance = mock_embeddings_cls.return_value
        mock_embedding_instance.embed_query.return_value = [0.1] * 768

        # Mock Database Results
        mock_qs = MagicMock()
        mock_news_article.objects.annotate.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs

        # Create dummy articles
        created = timezone.now()
        article_1, article_2 = NewsArticle.objects.bulk_create([
            NewsArticle(
                title="Bitcoin hits $100k",
                summary="Bitcoin surely hit a new all time high.",
                url="https://coindesk.com/btc-100k",
                published_at=created
            ),
            NewsArticle(
                title="Ethereum Merge 2.0",
                summary="New upgrades coming to ETH.",
                url="https://coindesk.com/eth-merge",
                published_at=created
            )
        ])
        mock_qs.__getitem__.return_value = [article_1, article_2]

        # Run the tool
        result = search_internal_news.invoke({"query": "crypto news"})
        mock_embeddings_cls.assert_called_once()
        mock_embedding_instance.embed_query.assert_called_with("crypto news")

        data = json.loads(result)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], "Bitcoin hits $100k")
        self.assertEqual(data[0]['summary'], "Bitcoin surely hit a new all time high.")
        self.assertEqual(data[0]['url'], "https://coindesk.com/btc-100k")
        self.assertEqual(data[0]['published_at'], created.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(data[1]['title'], "Ethereum Merge 2.0")
