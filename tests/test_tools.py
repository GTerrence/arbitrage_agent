import json
from unittest.mock import MagicMock, patch
from django.test import TestCase
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
        article_1 = MagicMock()
        article_1.title = "Bitcoin hits $100k"
        article_1.summary = "Bitcoin surely hit a new all time high."
        article_1.url = "https://coindesk.com/btc-100k"
        article_1.published_at = "2024-12-25T12:00:00Z"

        article_2 = MagicMock()
        article_2.title = "Ethereum Merge 2.0"
        article_2.summary = "New upgrades coming to ETH."
        article_2.url = "https://coindesk.com/eth-merge"
        article_2.published_at = "2024-12-26T12:00:00Z"

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
        self.assertEqual(data[0]['published_at'], "2024-12-25T12:00:00Z")
        self.assertEqual(data[1]['title'], "Ethereum Merge 2.0")
