import json
import os
from typing import Optional, Any, Dict
from redis import Redis, ConnectionError
from src.utils.logger import logger
from src.models.game_models import GameState

class RedisManager:
    """
    Manages Redis connection and game session storage.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.client = Redis.from_url(redis_url, decode_responses=True)
            self.client.ping() # Check connection
            logger.info(f"Connected to Redis at {redis_url}")
            self._initialized = True
        except ConnectionError as e:
            logger.warning(f"Could not connect to Redis at {redis_url}. Using in-memory fallback. Error: {e}")
            self.client = None
            self._memory_store = {}
            self._initialized = True

    def save_session(self, session_id: str, state: GameState) -> None:
        """
        Save the game state to Redis (or memory fallback).
        Expiration set to 1 hour.
        """
        try:
            state_json = state.json()
            if self.client:
                self.client.setex(f"game:{session_id}", 3600, state_json)
            else:
                self._memory_store[session_id] = state_json
            logger.debug(f"Saved session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise

    def get_session(self, session_id: str) -> Optional[GameState]:
        """
        Retrieve game state from Redis.
        """
        try:
            if self.client:
                data = self.client.get(f"game:{session_id}")
            else:
                data = self._memory_store.get(session_id)
                
            if not data:
                return None
                
            state_dict = json.loads(data)
            return GameState(**state_dict)
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
            
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        if self.client:
            self.client.delete(f"game:{session_id}")
        else:
            self._memory_store.pop(session_id, None)

def get_redis_manager() -> RedisManager:
    """Singleton accessor for RedisManager."""
    return RedisManager()
