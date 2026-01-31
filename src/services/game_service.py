from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from src.models.game_models import GameState
from src.managers.redis_manager import get_redis_manager
from src.services.workflow import get_workflow
from src.utils.logger import logger

class GameService:
    """Service to handle game logic and workflow execution."""
    
    def __init__(self):
        self.redis_manager = get_redis_manager()
        self.workflow = get_workflow()

    async def start_new_game(self) -> GameState:
        """Creates a new game session."""
        session_id = str(uuid.uuid4())
        
        initial_state = GameState(
            session_id=session_id,
            round_number=1,
            user_score=0,
            bot_score=0,
            user_bomb_used=False,
            bot_bomb_used=False
        )
        
        self.redis_manager.save_session(session_id, initial_state)
        logger.info(f"Started new game session: {session_id}")
        return initial_state

    async def get_game_status(self, session_id: str) -> Optional[GameState]:
        """Retrieves current game status."""
        return self.redis_manager.get_session(session_id)

    async def process_move(self, session_id: str, user_input: str) -> Optional[GameState]:
        """
        Processes a user's move for a given session.
        Returns updated state or None if session not found.
        """
        # 1. Retrieve current state
        current_state = self.redis_manager.get_session(session_id)
        if not current_state:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        if current_state.is_game_over:
            logger.info(f"Game already over for session: {session_id}")
            return current_state

        # 2. Update state with new input
        # Note: We create a dict for the workflow input
        # We need to preserve the existing state context
        
        # Determine next round number if previous round finished
        # If this is the start of a round, we use current round_number
        # Logic: If round_result is set, we advance round number?
        # Actually, let's look at the workflow inputs.
        # The workflow expects 'user_input' and current state context.
        
        if current_state.round_result:
             # Previous round completed, advance
             if not current_state.is_game_over:
                 current_state.round_number += 1
                 current_state.round_result = None
                 current_state.user_move = None
                 current_state.bot_move = None
                 current_state.validation = None
                 current_state.intent = None
        
        current_state.user_input = user_input
        
        # 3. Run Workflow
        logger.info(f"Invoking workflow for session {session_id}, round {current_state.round_number}")
        
        try:
            # LangGraph usually accepts a dict or object. 
            # Since we fixed nodes to handle pydantic, passing the object should work if LangGraph supports it.
            # However, standard practice is passing a dict.
            input_state = current_state.dict()
            
            # Run the workflow
            # invoke() returns the final state (as a dict usually)
            final_state_dict = await self.workflow.ainvoke(input_state)
            
            # 4. Update and Save State
            updated_state = GameState(**final_state_dict)
            self.redis_manager.save_session(session_id, updated_state)
            
            logger.info(f"Move processed successfully for {session_id}")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error processing move for {session_id}: {e}")
            raise

_game_service = None

def get_game_service() -> GameService:
    """Singleton accessor for GameService."""
    global _game_service
    if _game_service is None:
        _game_service = GameService()
    return _game_service
