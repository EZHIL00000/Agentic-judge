from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.managers.config_manager import get_app_config
from src.services.game_service import get_game_service
from src.models.game_models import GameState

router = APIRouter(
    prefix="/game",
    tags=["Game"]
)

class MoveRequest(BaseModel):
    user_input: str

class GameResponse(BaseModel):
    session_id: str
    message: str
    state: GameState

@router.post("/start", response_model=GameResponse)
async def start_game():
    """Start a new game session."""
    service = get_game_service()
    state = await service.start_new_game()
    return GameResponse(
        session_id=state.session_id,
        message="New game started! You have 5 rounds. Make your move.",
        state=state
    )

@router.post("/{session_id}/move", response_model=GameResponse)
async def make_move(session_id: str, request: MoveRequest):
    """Submit a move for the current round."""
    service = get_game_service()
    state = await service.process_move(session_id, request.user_input)
    
    if not state:
        raise HTTPException(status_code=404, detail="Game session not found")
        
    return GameResponse(
        session_id=state.session_id,
        message=state.response or "Move processed.",
        state=state
    )

@router.get("/{session_id}", response_model=GameState)
async def get_status(session_id: str):
    """Get the current status of a game session."""
    service = get_game_service()
    state = await service.get_game_status(session_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Game session not found")
        
    return state
