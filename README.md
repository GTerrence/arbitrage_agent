# AI Arbitrage Agent (RAG + LangGraph)

A scalable, event-driven AI agent that analyzes internal market news to detect crypto arbitrage opportunities. Built with **Django**, **Celery/RQ**, **LangGraph**, and **PostgreSQL (pgvector)**.

## 🏗 Architecture
[ Insert Diagram Here ]

## 🚀 Key Features
- **ReAct Agent Workflow:** Uses LangGraph to cyclically reason, search, and check prices.
- **RAG Implementation:** Custom embedding pipeline using Gemini-Flash and Postgres `pgvector`.
- **Async Event-Driven:** Decoupled inference logic using Redis queues to prevent HTTP blocking.
- **Fault Tolerance:** Agent state is persisted; worker crashes do not lose conversation history.

## 🛠 Tech Stack
- **Backend:** Django Rest Framework, Celery/Django-RQ
- **AI Core:** LangChain, LangGraph, Gemini 1.5 Flash
- **Database:** PostgreSQL (with `vector` extension)
- **Infrastructure:** Docker Compose, Redis

## ⚡️ Quick Start
1. Clone the repo:
   ```bash
   git clone [https://github.com/GTerrence/arbitrage_agent.git](https://github.com/GTerrence/arbitrage_agent.git)
   ```
2. Set up environment:
    ```
    bash
    cp .env.example .env
    # Add your GOOGLE_API_KEY in .env
    ```
3. Run with Docker:
    ```
    bash
    docker-compose up --build
    ```
4. Seed Mock Data:
    ```
    bash
    docker-compose exec web python manage.py seed_data
    ```
5. Test the API:
    ```
    bash
    ---
    curl -X POST http://localhost:8000/api/analyze/ -d '{"query": "Is ETH a good buy?"}'
    ```
