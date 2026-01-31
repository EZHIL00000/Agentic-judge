from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field

class MoveValidation(BaseModel):
    """Result of move validation logic."""
    valid: bool
    status: Literal["VALID", "INVALID", "UNCLEAR"]
    reason: str
    validated_move: Optional[str] = None

class GameState(BaseModel):
    """
    State schema for the Rock-Paper-Scissors Plus game workflow.
    
    This model is used by LangGraph to pass state between nodes.
    """
    # Session Context
    session_id: str = Field(..., description="Unique session identifier")
    round_number: int = Field(1, description="Current round number (1-5)")
    
    # Current Round Inputs/Outputs
    user_input: str = Field("", description="Raw input from the user")
    intent: Optional[Dict[str, Any]] = Field(None, description="Parsed user intent")
    
    # Move Data
    user_move: Optional[str] = Field(None, description="Validated user move")
    bot_move: Optional[str] = Field(None, description="Bot's move")
    
    # Logic Results
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation result")
    round_result: Optional[str] = Field(None, description="Winner of the round: user, bot, draw")
    
    # Game Status
    user_score: int = Field(0, description="User's total score")
    bot_score: int = Field(0, description="Bot's total score")
    
    # Resource Tracking
    user_bomb_used: bool = Field(False, description="Has user used their bomb?")
    bot_bomb_used: bool = Field(False, description="Has bot used their bomb?")
    
    # Final Output
    response: Optional[str] = Field(None, description="Generated response for the user")
    is_game_over: bool = Field(False, description="Is the game finished?")
    final_result: Optional[str] = Field(None, description="Final game outcome")

    class Config:
        arbitrary_types_allowed = True
