import os
import json
from functools import lru_cache
from typing import Optional
from pathlib import Path
from pydantic import ValidationError
from dotenv import load_dotenv
from src.models.config_model import AppConfig

# Load environment variables
load_dotenv()

class ConfigManager:
    """Singleton class to manage application configuration."""
    _instance = None
    _config: Optional[AppConfig] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """
        Explicitly initializes and loads the configuration.
        Should be called at application startup.
        """
        if self._initialized:
            return

        config_path = os.getenv("CONFIG_PATH")
        if not config_path:
            raise ValueError("CONFIG_PATH environment variable is not set")

        # Resolve absolute path
        abs_config_path = Path(config_path).resolve()
        
        if not abs_config_path.exists():
            raise FileNotFoundError(f"Config file not found at: {abs_config_path}")

        try:
            with open(abs_config_path, "r") as f:
                config_data = json.load(f)
            
            # Validate against the Pydantic model
            self._config = AppConfig(**config_data)
            self._initialized = True
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except ValidationError as e:
            raise ValueError(f"Config validation error: {e}")
        except Exception as e:
            raise Exception(f"Failed to load config: {e}")

    def get_config(self) -> AppConfig:
        """
        Returns the loaded configuration.
        """
        if not self._initialized or self._config is None:
            # Auto-initialize if not done yet, though explicit initialize() is preferred
            self.initialize()
            
        if self._config is None:
             raise RuntimeError("Config not loaded successfully")
             
        return self._config

@lru_cache()
def get_config_manager() -> ConfigManager:
    """Returns the singleton instance of ConfigManager."""
    return ConfigManager()

def get_app_config() -> AppConfig:
    """Helper to get the actual config object directly."""
    return get_config_manager().get_config()
