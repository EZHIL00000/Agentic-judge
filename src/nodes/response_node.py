"""
Response Generation Node for the AI Judge workflow.

This node generates user-friendly, explainable responses about game outcomes.
Uses LLM to create engaging and clear explanations.
"""
from typing import Any, Dict
from src.nodes.llm_node import create_sync_llm_node
from src.utils import logger
from src.utils.prompt_loader import load_prompt
from src.managers.config_manager import get_app_config


def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that generates a user-friendly response.
    
    Expected state keys:
        - round_number, user_input, user_move, bot_move
        - validation, round_result
        - user_score, bot_score
        - user_bomb_used, bot_bomb_used
    
    Returns:
        - response: The generated user-facing message
        - is_game_over: Whether the game has ended
        - final_result: Final game result if game is over
    """
    try:
        # Convert Pydantic state to dict if needed
        state_dict = state.dict() if hasattr(state, "dict") else state
        
        round_number = state_dict.get("round_number", 1)
        user_score = state_dict.get("user_score", 0)
        bot_score = state_dict.get("bot_score", 0)
        validation = state_dict.get("validation", {})
        
        # Check if game is over (5 rounds)
        is_game_over = round_number >= 5
        
        # Determine final result if game over
        final_result = None
        if is_game_over:
            if user_score > bot_score:
                final_result = "user_wins"
            elif bot_score > user_score:
                final_result = "bot_wins"
            else:
                final_result = "draw"
        
        logger.info(f"Generating response for round {round_number}")
        
        # Get node configuration
        
        config = get_app_config()
        node_config = config.nodes.response_node

        # Load prompts from Jinja2 files
        system_prompt = load_prompt(node_config.system_prompt)
        user_prompt_template = load_prompt(node_config.user_prompt)
        
        # Prepare context for LLM
        # Use state_dict for accessing top-level fields, but check validity
        # Note: We constructed llm_state specifically for the prompt
        
        user_move_val = state_dict.get("user_move")
        bot_move_val = state_dict.get("bot_move")
        
        llm_state = {
            "round_number": round_number,
            "user_input": state_dict.get("user_input", ""),
            "user_move": user_move_val if user_move_val else "None (invalid)",
            "bot_move": bot_move_val if bot_move_val else "None",
            "validation_status": validation.get("status", "UNKNOWN"),
            "validation_reason": validation.get("reason", ""),
            "round_result": state_dict.get("round_result", "unknown"),
            "user_score": user_score,
            "bot_score": bot_score,
            "is_game_over": is_game_over,
            "user_bomb_used": state_dict.get("user_bomb_used", False),
            "bot_bomb_used": state_dict.get("bot_bomb_used", False),
        }
        
        # Create and execute LLM node
        llm_node = create_sync_llm_node(
            prompt_template=user_prompt_template,
            output_key="response_raw",
            model_name=node_config.model_name,
            system_prompt=system_prompt,
            parse_json=False
        )
        
        result = llm_node(llm_state)
        response = result.get("response_raw", "Round complete.")
        
        logger.info(f"Response generated. Game over: {is_game_over}")
        
        return {
            "response": response,
            "is_game_over": is_game_over,
            "final_result": final_result
        }
        
    except Exception as e:
        logger.error(f"Error in generate_response: {e}")
        # Fallback response
        validation = state_dict.get("validation", {})
        round_result = state_dict.get("round_result", "unknown")
        
        fallback = f"Round {state_dict.get('round_number', '?')}: "
        if validation.get("valid"):
            fallback += f"You played {state_dict.get('user_move')}, Bot played {state_dict.get('bot_move')}. "
            fallback += f"Result: {round_result}."
        else:
            fallback += f"{validation.get('reason', 'Invalid move.')}"
        
        return {
            "response": fallback,
            "is_game_over": state_dict.get("round_number", 1) >= 5,
            "final_result": None
        }
