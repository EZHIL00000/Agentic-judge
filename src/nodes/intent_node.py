"""
Intent Understanding Node for the AI Judge workflow.

This node parses the user's free-text input and extracts the intended move.
It uses the LLM to understand ambiguous or creative inputs.
"""
from typing import Any, Dict
from src.nodes.llm_node import create_sync_llm_node
from src.utils import logger
from src.utils.prompt_loader import load_prompt


def understand_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that understands the user's intent from their input.
    
    Expected state keys:
        - user_input: The raw text input from the user
    
    Returns:
        - intent: Parsed intent with detected_move, status, confidence, reasoning
    """
    try:
        # Convert Pydantic state to dict if needed
        state_dict = state.dict() if hasattr(state, "dict") else state
        
        logger.info(f"Understanding intent for input: {state_dict.get('user_input', '')[:50]}...")
        
        # Load prompts from Jinja2 files
        system_prompt = load_prompt("intent_system")
        user_prompt_template = load_prompt("intent_user")
        
        # Create the LLM node for intent parsing
        llm_node = create_sync_llm_node(
            prompt_template=user_prompt_template,
            output_key="intent_raw",
            model_name="gemini-2.5-flash",
            system_prompt=system_prompt,
            parse_json=True
        )
        
        # Execute the LLM node
        result = llm_node(state)
        
        intent = result.get("intent_raw")
        
        if intent is None:
            logger.warning("Intent parsing returned None, marking as unclear")
            intent = {
                "detected_move": None,
                "status": "unclear",
                "confidence": 0.0,
                "reasoning": "Failed to parse user input"
            }
        
        logger.info(f"Intent parsed: {intent.get('status', 'unknown')} - {intent.get('detected_move', 'none')}")
        
        return {"intent": intent}
        
    except Exception as e:
        logger.error(f"Error in understand_intent: {e}")
        return {
            "intent": {
                "detected_move": None,
                "status": "unclear",
                "confidence": 0.0,
                "reasoning": f"Error processing input: {str(e)}"
            }
        }
