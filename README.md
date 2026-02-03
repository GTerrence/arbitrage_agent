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
    cd arbitrage_agent

2. Set up environment:
    ```bash
    cp .env.example .env
    # Add your GOOGLE_API_KEY in .env

3. Run with Docker:
    ```bash
    docker-compose up --build

4. Seed Mock Data:
    ```bash
    docker-compose exec web python manage.py seed_data

5. Test the API:
    ```bash
    curl -X POST http://localhost:8000/api/analyze/ -d '{"query": "Is ETH a good buy?"}'


## 🏗 Architecture

```mermaid
graph LR
    %% === Styling ===
    %% Clean, high-contrast palette
    classDef user fill:#ffcccc,stroke:#b30000,stroke-width:2px,color:#000,font-weight:bold;
    classDef infra fill:#d9edff,stroke:#004085,stroke-width:2px,color:#000;
    classDef storage fill:#fff3cd,stroke:#856404,stroke-width:2px,color:#000;
    classDef logic fill:#e9f5ff,stroke:#004085,stroke-width:2px,color:#000;
    classDef external fill:#f8f9fa,stroke:#6c757d,stroke-width:2px,color:#000,stroke-dasharray: 5 5;

    %% === Nodes ===
    User[User / Postman]:::user

    subgraph "Async Web Layer"
        direction LR
        API[Django API]:::infra
        Redis[(Redis Queue)]:::storage
        Worker[RQ Worker]:::infra
    end


    subgraph "AI Core (LangGraph)"
        Agent((Agent Graph)):::logic
        Tools[Tool Node]:::logic
    end

    subgraph "Knowledge Base"
        PG[(Postgres/pgvector)]:::storage
        Gemini[Gemini 2.5]:::external
        NewsAPI[External Data]:::external
    end

    %% === THE FLOW (Left to Right) ===

    %% 1. Submission
    User -- 1. POST --> API
    API -- 2. Enqueue --> Redis
    API -.->|3. Task ID| User

    %% 2. Processing Pipeline
    Redis -- 4. Pull Job --> Worker
    Worker -- 5. Invoke --> Agent

    Agent <-->|6. Loop| Gemini
    Agent -->|7. Use| Tools

    Tools <-->|8. Search| PG
    Tools <-->|9. Fetch| NewsAPI

    Worker -.->|10. Save| Redis

    %% 3. Polling (The Loop Back)
    User -- 11. GET Status --> API
    API -- 12. Check --> Redis
    Redis -.->|13. Result| API
    API -.->|14. JSON| User
