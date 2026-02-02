# Agentic Judge API

An AI-powered Rock-Paper-Scissors game API featuring an "Agentic Judge" that interprets user intents, validates moves against game rules (including a special "Bomb" mechanic), and generates engaging commentary using Large Language Models (LLMs).

Built with **FastAPI**, **LangGraph**, and **LangChain**.

## Features

- **Agentic Workflow**: Uses a LangGraph state machine to manage game flow (Intent -> Logic -> Response).
- **Natural Language Input**: Users can describe their move ("I'll crush you with a rock!", "Deploy the bomb!"), and the LLM interprets the intent.
- **Game Mechanics**:
  - Classic Rock, Paper, Scissors rules.
  - special **Bomb** move: Can be used only once per game; beats everything except another bomb.
  - 5 rounds per game.
- **LLM Integration**: Supports Google Gemini (via `langchain-google-genai`) and local Ollama models.
- **Session Management**: Redis-backed session storage with persistence (falls back to in-memory if Redis is unavailable).
- **Scalable Config**: Centralized configuration for models, paths, and prompts.

## Tech Stack

- **Framework**: FastAPI
- **Orchestration**: LangGraph
- **AI/LLM**: LangChain, Google Gemini (Flash/Pro)
- **Storage**: Redis (optional)
- **Language**: Python 3.10+

## Prerequisites

- Python 3.10 or higher
- [Redis](https://redis.io/) (optional, recommended for production)
- Google API Key (for Gemini models)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**:
    - **Environment Variables**: Create a `.env` file in the root directory.
      ```bash
      GOOGLE_API_KEY=your_api_key_here
      # Optional: Redis URL
      # REDIS_URL=redis://localhost:6379/0
      ```
    - **App Config**: Check `src/config/config.json` for model settings. By default, it uses `gemini-2.5-flash`.

## Running the Application

### Locally
You can run the application using the provided entry point:

```bash
python main.py
```

Or directly with Uvicorn:

```bash
uvicorn src.app:app --reload
```

The server will start at `http://0.0.0.0:8000`.

### With Docker Compose (Recommended)
The easiest way to run the full stack (API + Redis) is using Docker Compose. This handles the networking and ensures the API can communicate with the Redis container automatically.

```bash
docker-compose up --build
```

**Note on Ports**: The `docker-compose.yml` is configured to map Redis to port `6380` on your host to avoid conflicts with any local Redis service running on `6379`. The internal communication within Docker uses port `6379`.

### With Standalone Docker
1.  **Build the image**:
    ```bash
    docker build -t agentic-judge .
    ```

2.  **Run the container**:
    To connect to a local Redis on your host (Mac/Windows), use the `host.docker.internal` alias:
    ```bash
    docker run -p 8000:8000 -e REDIS_URL=redis://host.docker.internal:6379/0 agentic-judge
    ```

## Configuration Guide

The application uses a centralized configuration system managed via `src/config/config.json`.

1.  **API Keys**: Store your provider-level API keys (e.g., Google) in the `llm_models` section of `config.json`.
2.  **Node Settings**: You can configure which model and prompt files each workflow node (`intent_node`, `response_node`) uses in the `nodes` section.

## API Endpoints

### 1. Start a New Game
**POST** `/game/start`

Starts a new 5-round game session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "message": "New game started! You have 5 rounds. Make your move.",
  "state": { ... }
}
```

### 2. Make a Move
**POST** `/game/{session_id}/move`

Submit a move using natural language.

**Payload:**
```json
{
  "user_input": "I throw a rock!"
}
```

**Response:**
```json
{
  "response": "Round 1: You chose rock, Bot chose scissors. You win this round!",
  "is_game_over": false,
  "game_state": { ... }
}
```

## Project Structure

```
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── src/
│   ├── app.py              # FastAPI app application factory
│   ├── config/             # Configuration files (config.json, graph.json)
│   ├── managers/           # Resource managers (Config, Model, Redis)
│   ├── models/             # Pydantic models (Config, GameState)
│   ├── nodes/              # LangGraph nodes (Intent, Logic, Response, LLM)
│   ├── prompts/            # Jinja2 prompt templates
│   ├── routers/            # API routers
│   ├── services/           # Business logic (Workflow, GameService)
│   └── utils/              # Utilities (Logger, PromptLoader)
```
