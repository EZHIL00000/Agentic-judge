"""
Game Logic Node for the AI Judge workflow.

This node applies the game rules to validate moves and determine outcomes.
Logic is primarily driven by clear rules, not LLM inference.
"""
import random
from typing import Any, Dict, Optional
from src.utils import logger

# Valid moves in the game
VALID_MOVES = {"rock", "paper", "scissors", "bomb"}

# Win conditions: key beats values in the list
WIN_MAP = {
    "rock": ["scissors"],
    "paper": ["rock"],
    "scissors": ["paper"],
    "bomb": ["rock", "paper", "scissors"],  # Bomb beats everything except bomb
}


def _determine_winner(user_move: str, bot_move: str) -> str:
    """
    Determine the winner of a round.
    
    Returns:
        "user", "bot", or "draw"
    """
    if user_move == bot_move:
        return "draw"
    
    if bot_move in WIN_MAP.get(user_move, []):
        return "user"
    
    return "bot"


def _generate_bot_move(bot_bomb_used: bool) -> str:
    """Generate a random move for the bot."""
    available_moves = list(VALID_MOVES)
    if bot_bomb_used:
        available_moves.remove("bomb")
    return random.choice(available_moves)


def _validate_move(
    intent: Dict[str, Any],
    user_bomb_used: bool
) -> Dict[str, Any]:
    """
    Validate the user's move based on game rules.
    
    Returns:
        Validation result with status, reason, and validated_move
    """
    status = intent.get("status", "unclear")
    detected_move = intent.get("detected_move")
    
    # Handle unclear or invalid intents
    if status == "unclear":
        return {
            "valid": False,
            "status": "UNCLEAR",
            "reason": intent.get("reasoning", "Your move was unclear. Please specify rock, paper, scissors, or bomb."),
            "validated_move": None
        }
    
    if status == "invalid" or detected_move is None:
        return {
            "valid": False,
            "status": "INVALID",
            "reason": intent.get("reasoning", "That doesn't seem like a valid move."),
            "validated_move": None
        }
    
    # Check if move is in valid set
    move_lower = detected_move.lower()
    if move_lower not in VALID_MOVES:
        return {
            "valid": False,
            "status": "INVALID",
            "reason": f"'{detected_move}' is not a valid move. Choose rock, paper, scissors, or bomb.",
            "validated_move": None
        }
    
    # Check bomb constraint
    if move_lower == "bomb" and user_bomb_used:
        return {
            "valid": False,
            "status": "INVALID",
            "reason": "You've already used your bomb! Each player can only use bomb once per game.",
            "validated_move": None
        }
    
    return {
        "valid": True,
        "status": "VALID",
        "reason": f"Move '{move_lower}' is valid.",
        "validated_move": move_lower
    }


def evaluate_logic(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that evaluates game logic.
    
    Expected state keys:
        - intent: Parsed intent from intent_node
        - user_bomb_used: Whether user has used their bomb
        - bot_bomb_used: Whether bot has used their bomb
        - round_number: Current round number
        - user_score: User's current score
        - bot_score: Bot's current score
    
    Returns:
        - validation: Move validation result
        - user_move: The validated user move (or None)
        - bot_move: The bot's move for this round
        - round_result: Winner of this round
        - user_bomb_used: Updated bomb usage
        - bot_bomb_used: Updated bomb usage
        - user_score: Updated score
        - bot_score: Updated score
    """
    try:
        # Convert Pydantic state to dict if needed
        state_dict = state.dict() if hasattr(state, "dict") else state
        
        intent = state_dict.get("intent", {})
        user_bomb_used = state_dict.get("user_bomb_used", False)
        bot_bomb_used = state_dict.get("bot_bomb_used", False)
        round_number = state_dict.get("round_number", 1)
        user_score = state_dict.get("user_score", 0)
        bot_score = state_dict.get("bot_score", 0)
        
        logger.info(f"Evaluating logic for round {round_number}")
        
        # Validate the user's move
        validation = _validate_move(intent, user_bomb_used)
        
        updates: Dict[str, Any] = {
            "validation": validation,
            "user_move": None,
            "bot_move": None,
            "round_result": None,
        }
        
        if not validation["valid"]:
            # Invalid/unclear move - turn wasted, bot still plays
            bot_move = _generate_bot_move(bot_bomb_used)
            updates["bot_move"] = bot_move
            updates["round_result"] = "bot"  # Invalid moves lose the round
            updates["bot_score"] = bot_score + 1
            
            # Update bot bomb usage
            if bot_move == "bomb":
                updates["bot_bomb_used"] = True
            
            logger.info(f"Invalid move. Bot wins round with {bot_move}")
        else:
            # Valid move - play the round
            user_move = validation["validated_move"]
            bot_move = _generate_bot_move(bot_bomb_used)
            
            # Determine winner
            round_result = _determine_winner(user_move, bot_move)
            
            updates["user_move"] = user_move
            updates["bot_move"] = bot_move
            updates["round_result"] = round_result
            
            # Update scores
            if round_result == "user":
                updates["user_score"] = user_score + 1
            elif round_result == "bot":
                updates["bot_score"] = bot_score + 1
            
            # Update bomb usage
            if user_move == "bomb":
                updates["user_bomb_used"] = True
            if bot_move == "bomb":
                updates["bot_bomb_used"] = True
            
            logger.info(f"Round result: {user_move} vs {bot_move} = {round_result}")
        
        return updates
        
    except Exception as e:
        logger.error(f"Error in evaluate_logic: {e}")
        return {
            "validation": {
                "valid": False,
                "status": "INVALID",
                "reason": f"Game error: {str(e)}",
                "validated_move": None
            },
            "round_result": "error"
        }
