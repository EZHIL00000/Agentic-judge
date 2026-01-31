import os
from typing import Optional, Union, Any, Dict
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

from src.managers.config_manager import get_app_config
from src.models.config_model import ChatModelParams, EmbeddingModelParams, BaseArgs
from src.utils import logger

class ModelManager:
    """
    Manages the initialization and retrieval of LangChain model instances
    based on the application configuration.
    """
    def __init__(self):
        self.config = get_app_config()
        self._instances: Dict[str, Union[BaseChatModel, Embeddings]] = {}

    def get_model(self, model_name: str) -> Union[BaseChatModel, Embeddings]:
        """
        Retrieves a loaded LangChain model instance by its name as defined in config.
        First attempts to find a chat model, then an embedding model.
        """
        if model_name in self._instances:
            return self._instances[model_name]

        # Search through providers to find the model config
        for provider_name, provider_config in self.config.llm_models.items():
            
            # Check Chat Models
            if model_name in provider_config.chat_models:
                params = provider_config.chat_models[model_name]
                instance = self._create_chat_model(provider_name, model_name, params)
                self._instances[model_name] = instance
                logger.debug(f"Created and cached chat model: {model_name} (provider: {provider_name})")
                return instance

            # Check Embedding Models
            if model_name in provider_config.embedding_models:
                params = provider_config.embedding_models[model_name]
                instance = self._create_embedding_model(provider_name, model_name, params)
                self._instances[model_name] = instance
                logger.debug(f"Created and cached embedding model: {model_name} (provider: {provider_name})")
                return instance

        logger.error(f"Model '{model_name}' not found in configuration.")
        raise ValueError(f"Model '{model_name}' not found in configuration.")

    def _resolve_api_key(self, params: BaseArgs) -> Optional[str]:
        """
        Resolves the API key:
        1. Checks for direct 'api_key' in config.
        2. Checks for 'api_key_env_var' and loads from environment.
        """
        # 1. Direct API key
        if params.api_key:
            return params.api_key
            
        # 2. Key from Environment Variable
        if params.api_key_env_var:
            api_key = os.getenv(params.api_key_env_var)
            if not api_key:
                logger.warning(f"Environment variable '{params.api_key_env_var}' for API key is not set or empty.")
            return api_key
            
        return None

    def _create_chat_model(self, provider: str, name: str, params: ChatModelParams) -> BaseChatModel:
        """Factory method for Chat Models."""
        if provider == "google":
            api_key = self._resolve_api_key(params)
            return ChatGoogleGenerativeAI(
                model=params.model_name or name, 
                google_api_key=api_key,
                temperature=params.temperature,
                max_output_tokens=params.max_tokens,
                top_p=params.top_p,
                convert_system_message_to_human=True 
            )
        
        elif provider == "ollama":
            return ChatOllama(
                model=params.model_name or name,
                base_url=params.base_url,
                temperature=params.temperature,
                top_p=params.top_p,
                **{k: v for k, v in {"num_predict": params.max_tokens}.items() if v is not None}
            )
            
        else:
            raise ValueError(f"Unsupported chat model provider: {provider}")

    def _create_embedding_model(self, provider: str, name: str, params: EmbeddingModelParams) -> Embeddings:
        """Factory method for Embedding Models."""
        if provider == "google":
            api_key = self._resolve_api_key(params)
            model_id = getattr(params, "model_name", name) 
            
            return GoogleGenerativeAIEmbeddings(
                model=model_id,
                google_api_key=api_key
            )
            
        elif provider == "ollama":
            return OllamaEmbeddings(
                model=params.model_name or name,
                base_url=params.base_url
            )
            
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

@lru_cache()
def get_model_manager() -> ModelManager:
    """Singleton accessor for ModelManager."""
    return ModelManager()
