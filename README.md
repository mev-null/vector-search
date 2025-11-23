# NASA APOD Vector Search API

A vector search API designed to search for images using natural language from NASA's vast [Astronomy Picture of the Day (APOD)](https://apod.nasa.gov/apod/astropix.html) archive. It enables semantic (contextual) searching of relevant images using natural language queries such as "beautiful blue nebula" or "photo where Saturn's rings are clearly visible."

## Features

  * **Natural Language Search**: Searches for images by understanding the intent of the sentence, not just through keywords.
  * **High-Speed Similarity Search**: Utilizes `pgvector` to rapidly identify highly similar images from high-dimensional vector data.
  * **Containerized Environment**: Docker Compose allows anyone to easily reproduce and launch the environment without worrying about dependencies.
  * **Scalable Design**: Built with FastAPI and SQLAlchemy to maintain a clean and highly maintainable codebase.

-----

## 🛠️ Tech Stack

| Category | Tech | Purpose |
| :--- | :--- | :--- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/) | High-performance asynchronous API server, strict data type validation. |
| **Database** | [PostgreSQL](https://www.postgresql.org/), [pgvector](https://github.com/pgvector/pgvector) | Reliable relational DB, vector data storage, and similarity search. |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) | Mapping between Python objects and DB tables, secure DB operations. |
| **DB Migration** | [Alembic](https://alembic.sqlalchemy.org/en/latest/) | Database schema version control. |
| **Infrastructure** | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/) | Application containerization, ensuring development environment reproducibility. |
| **ML Model** | [Sentence-Transformers](https://www.sbert.net/) | To convert text data into vectors (Embeddings). |

-----

## System Architecture and Data Flow

This API processes user requests in the following steps:

1.  **Receive Request**: The user POSTs the text they want to search (e.g., "A photo of the Earth from space") to the FastAPI endpoint.
2.  **Text Vectorization**: The received text is converted into high-dimensional vector data that captures its meaning using the `sentence-transformers` model.
3.  **Database Search**: The system queries PostgreSQL (pgvector) via SQLAlchemy for the vectors with the highest similarity to the converted vector. `pgvector` performs calculations such as cosine similarity at high speed.
4.  **Return Results**: FastAPI receives the search results (APOD image URL, description, date, etc.) and returns them to the user in JSON format.

-----

## 🚀 Getting Started

### 1\. Prerequisites

  * [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) must be installed.
  * You must have obtained a [NASA API Key](https://api.nasa.gov/).

### 2\. Environment Setup

Create a `.env` file in the project root and add the following content:

```env
# PostgreSQL Database Settings
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# NASA API Key
NASA_API_KEY=YOUR_NASA_API_KEY_HERE
```

### 3\. Launch and Initialization

Execute the following commands in order:

```bash
# 1. Build and start Docker containers in the background
docker-compose up -d --build

# 2. Create database tables (first time only)
docker-compose exec app alembic upgrade head

# 3. Fetch initial data from NASA APOD and insert it into the DB
# (Defaults to the past 100 days. Can be changed in api/scripts/load_data.py)
python api/scripts/load_data.py
```

The API server will now be running at `http://localhost:8000`.
