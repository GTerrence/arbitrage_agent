from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from arbitrage_agent.apps.news_articles.models import NewsArticle
from arbitrage_agent.core.constants import EMBEDDING_MODEL, EMBEDDING_SIZE


class Command(BaseCommand):
    help = "Seeds the database with 10 meaningful mock news articles related to crypto and finance, "
    "using REAL embeddings."

    def handle(self, *args: Any, **options: Any) -> None:
        if not getattr(settings, "GEMINI_API_KEY", None):
            self.stdout.write(
                self.style.ERROR("GEMINI_API_KEY is not set in settings. Cannot generate real embeddings.")
            )
            return

        self.stdout.write("Initializing Embedding Model...")
        try:
            embeddings_model = GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                output_dimensionality=EMBEDDING_SIZE,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize embeddings: {e}"))
            return

        # Fixed set of realistic articles
        articles_data = [
            {
                "title": "Bitcoin Surges Past $100k as Institutional Adoption Grows",
                "summary": (
                    "Bitcoin has reached a new all-time high of over $100,000 driven by massive inflows from "
                    "institutional investors and the approval of new spot ETFs globally. Analysts predict continued "
                    "momentum as major banks announce custody services."
                ),
                "url": "https://www.coindesk.com/markets/2026/02/01/bitcoin-breaks-100k-milestone/",
            },
            {
                "title": "Ethereum's Latest Upgrade Promises to Slash Gas Fees by 90%",
                "summary": (
                    "The Ethereum foundation has successfully deployed the 'Dencun' upgrade, introducing "
                    "proto-danksharding. This major technical shift is expected to reduce transaction costs on "
                    "Layer 2 networks by nearly 90%, making DeFi more accessible."
                ),
                "url": "https://www.coindesk.com/tech/2026/01/28/ethereum-dencun-upgrade-live/",
            },
            {
                "title": "SEC Approves First Spot Solana ETF in Historic Ruling",
                "summary": (
                    "In a surprise move, the SEC has approved the first spot Solana ETF, paving the way for "
                    "broader institutional access to the high-speed blockchain's native token. SOL prices jumped "
                    "15% immediately following the announcement."
                ),
                "url": "https://www.coindesk.com/policy/2026/01/25/sec-approves-solana-etf/",
            },
            {
                "title": "Federal Reserve Announcement Sparks Crypto Market Rally",
                "summary": (
                    "The Federal Reserve's decision to pause interest rate hikes has ignited a rally across risk "
                    "assets, with the total crypto market cap reclaiming the $3 trillion mark. Investors view the "
                    "pivot as a bullish signal for digital assets."
                ),
                "url": "https://www.coindesk.com/markets/2026/01/20/fed-rate-pause-bullish-crypto/",
            },
            {
                "title": "DeFi Giant Uniswap Launches V5 with Cross-Chain Liquidity",
                "summary": (
                    "Uniswap Labs has unveiled Uniswap V5, featuring native cross-chain swaps and an automated "
                    "liquidity management engine. The update aims to unify fragmented liquidity across Ethereum, "
                    "Arbitrum, Optimism, and Base."
                ),
                "url": "https://www.coindesk.com/business/2026/01/15/uniswap-v5-launch/",
            },
            {
                "title": "MicroStrategy Acquires Additional 10,000 BTC",
                "summary": (
                    "MicroStrategy continues its aggressive Bitcoin accumulation strategy, purchasing another "
                    "10,000 BTC at an average price of $95,000. Michael Saylor reaffirmed the company's "
                    "commitment to Bitcoin as a primary treasury reserve asset."
                ),
                "url": "https://www.coindesk.com/business/2026/01/10/microstrategy-buys-more-bitcoin/",
            },
            {
                "title": "Japan Implements Framework for Stablecoin Adoptions",
                "summary": (
                    "Japan's FSA has implemented a new regulatory framework allowing banks and registered "
                    "exchange providers to issue stablecoins. The move is expected to boost web3 adoption in "
                    "the world's third-largest economy."
                ),
                "url": "https://www.coindesk.com/policy/2026/01/05/japan-stablecoin-rules-live/",
            },
            {
                "title": "BlackRock Tokenizes $10B Real Estate Fund on Ethereum",
                "summary": (
                    "Asset management titan BlackRock has tokenized a $10 billion real estate fund on the "
                    "Ethereum blockchain, allowing for 24/7 trading and fractional ownership. This marks a "
                    "significant milestone in the RWA (Real World Assets) sector."
                ),
                "url": "https://www.coindesk.com/business/2026/01/02/blackrock-tokenizes-real-estate-fund/",
            },
            {
                "title": "Arbitrage Opportunities Rise as DEX Volumes Overtake CEXs",
                "summary": (
                    "For the first time in history, monthly trading volume on decentralized exchanges (DEXs) "
                    "has surpassed centralized exchanges (CEXs). This shift has created lucrative arbitrage "
                    "opportunities between on-chain pools and traditional order books."
                ),
                "url": "https://www.coindesk.com/markets/2025/12/28/dex-volume-flips-cex/",
            },
            {
                "title": "Ripple Wins Final Appeal Against SEC, XRP Relisted Everywhere",
                "summary": (
                    "The multi-year legal battle between Ripple and the SEC has concluded with a decisive "
                    "victory for Ripple. Major US exchanges have immediately relisted XRP, leading to a massive "
                    "surge in trading volume and price."
                ),
                "url": "https://www.coindesk.com/policy/2025/12/20/ripple-wins-sec-appeal-final/",
            }
        ]

        texts_to_embed = [f"{item['title']} {item['summary']}" for item in articles_data]

        self.stdout.write(f"Generating embeddings for {len(texts_to_embed)} articles using Gemini...")
        try:
            vectors = embeddings_model.embed_documents(texts_to_embed)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating embeddings: {e}"))
            return

        new_articles = []
        for i, item in enumerate(articles_data):
            # Stagger publish times
            published_at = timezone.now() - timedelta(days=(len(articles_data) - i))

            new_articles.append(NewsArticle(
                title=item["title"],
                summary=item["summary"],
                url=item["url"],
                published_at=published_at,
                embedding=vectors[i]
            ))

        self.stdout.write("Saving articles to database...")
        NewsArticle.objects.bulk_create(
            new_articles,
            update_conflicts=True,
            unique_fields=['url'],
            update_fields=['title', 'summary', 'published_at', 'embedding']
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded/updated {len(new_articles)} meaningful articles.")
        )
