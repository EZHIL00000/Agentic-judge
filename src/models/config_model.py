from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

class BaseArgs(BaseModel):
    """Base arguments common to all models."""
    api_key: Optional[str] = Field(None, description="Direct API key for the model")
    api_key_env_var: Optional[str] = Field(None, description="Environment variable name for the API key")
    base_url: Optional[str] = Field(None, description="Base URL for local models like Ollama")
    model_config = {"extra": "allow"}  # Allow arbitrary extra parameters

class ChatModelParams(BaseArgs):
    """Parameters specific to chat models."""
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None)
    top_p: Optional[float] = Field(None)

class EmbeddingModelParams(BaseArgs):
    """Parameters specific to embedding models."""
    dimensions: Optional[int] = Field(None)

class ProviderModels(BaseModel):
    """Configuration for a specific provider's models."""
    api_key: Optional[str] = Field(None, description="Common API key for this provider")
    chat_models: Dict[str, ChatModelParams] = Field(default_factory=dict, description="Map of chat model names to their config")
    embedding_models: Dict[str, EmbeddingModelParams] = Field(default_factory=dict, description="Map of embedding model names to their config")

class PathConfig(BaseModel):
    """Configuration for application paths."""
    prompts_base_path: str = Field(..., description="Base path for prompt templates")
    nodes_base_path: str = Field("src/nodes", description="Base path for workflow nodes")
    logs_path: str = Field("logs", description="Path to store logs")

class RedisConfig(BaseModel):
    """Configuration for Redis connection."""
    url: str = Field("redis://localhost:6379/0", description="Redis connection URL")
    session_ttl: int = Field(3600, description="Session TTL in seconds")

class AppConfig(BaseModel):
    """Main application configuration."""
    app_name: str = Field("Agentic Judge API", description="Name of the application")
    environment: str = Field("development", description="Environment (development/production)")
    version: str = Field("1.0.0", description="App version")
    
    # New hierarchical structure: Provider -> {chat_models: {...}, embedding_models: {...}}
    llm_models: Dict[str, ProviderModels] = Field(..., description="Configuration grouped by provider")
    
    paths: PathConfig
    redis: RedisConfig = Field(default_factory=RedisConfig)
    debug: bool = False
