"""
Generic reusable LLM node factory for LangGraph workflows.

This module provides a factory function to create LLM-powered nodes
that can be configured with different prompts and output keys.
"""
from typing import Any, Callable, Dict, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.managers.model_manager import get_model_manager
from src.utils import logger


def _clean_json_string(json_str: str) -> str:
    """Helper to clean JSON string from markdown code blocks."""
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    return json_str


def create_llm_node(
    prompt_template: str,
    output_key: str,
    model_name: str = "gemini-2.5-flash",
    system_prompt: Optional[str] = None,
    parse_json: bool = False,
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Factory function that creates a reusable LLM node for LangGraph.
    
    Args:
        prompt_template: The prompt template string with placeholders for state variables.
        output_key: The key to store the LLM response in the state.
        model_name: Name of the model to use (from config).
        system_prompt: Optional system prompt to prepend.
        parse_json: If True, parse the response as JSON.
    
    Returns:
        An async function that can be used as a LangGraph node.
    
    Example:
        >>> intent_node = create_llm_node(
        ...     prompt_template="Parse this move: {user_input}",
        ...     output_key="intent",
        ...     model_name="gemini-1.5-flash"
        ... )
    """
    
    async def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the LLM node with the current state."""
        try:
            logger.debug(f"Executing LLM node with output_key: {output_key}")
            
            # Convert Pydantic state to dict if needed
            state_dict = state.dict() if hasattr(state, "dict") else state
            
            # Get the model
            model_manager = get_model_manager()
            llm: BaseChatModel = model_manager.get_model(model_name)
            
            from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate

            # Build messages
            messages_templates = []
            if system_prompt:
                # Assuming system prompt uses Jinja2 if it contains braces
                messages_templates.append(SystemMessagePromptTemplate.from_template(system_prompt, template_format="jinja2"))
            
            messages_templates.append(HumanMessagePromptTemplate.from_template(prompt_template, template_format="jinja2"))
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages(messages_templates)
            
            # Format with state variables
            formatted_prompt = prompt.format_messages(**state_dict)
            
            # Invoke LLM
            response = await llm.ainvoke(formatted_prompt)
            
            result_content = response.content
            
            # Parse JSON if requested
            if parse_json:
                try:
                    result_content = _clean_json_string(result_content)
                    parser = JsonOutputParser()
                    
                    import json
                    try:
                        result_content = json.loads(result_content)
                    except json.JSONDecodeError:
                         result_content = parser.parse(result_content)
                         
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}. Raw content: {result_content}")
                    # In intent node, we really need the JSON.
                    # If parsing fails, we might just return None or a dict indicating failure?
                    # But the function signature expects Any.
                    # Let's return raw content if parsing fails, but intent_node expects dict.
                    # So we should probably return {"error": "parsing_failed"} or similar if we can't parse?
                    # The current behavior returns raw content, which might cause downstream issues if dict is expected.
                    # But if we return raw content, intent_node checks .get("status") on str -> Error.
                    # So let's return a default error dict if JSON parsing fails absolutely.
                    if output_key == "intent": # Specific hack or general robustness?
                        result_content = {"status": "unclear", "reasoning": "Failed to parse model output."}
                    else:
                        # Try to handle generally
                         result_content = {"error": "parsing_failed", "raw": result_content}
            
            logger.debug(f"LLM node completed. Output key: {output_key}")
            return {output_key: result_content}
            
        except Exception as e:
            logger.error(f"LLM node error: {e}")
            return {output_key: None, "error": str(e)}
    
    return node_function


def create_sync_llm_node(
    prompt_template: str,
    output_key: str,
    model_name: str = "gemini-2.5-flash",
    system_prompt: Optional[str] = None,
    parse_json: bool = False,
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Synchronous version of create_llm_node for non-async workflows.
    """
    
    def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the LLM node with the current state (sync)."""
        try:
            logger.debug(f"Executing sync LLM node with output_key: {output_key}")
            
            # Convert Pydantic state to dict if needed
            state_dict = state.dict() if hasattr(state, "dict") else state
            
            # Get the model
            model_manager = get_model_manager()
            llm: BaseChatModel = model_manager.get_model(model_name)
            
            from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate

            # Build messages
            messages_templates = []
            if system_prompt:
                messages_templates.append(SystemMessagePromptTemplate.from_template(system_prompt, template_format="jinja2"))
            
            messages_templates.append(HumanMessagePromptTemplate.from_template(prompt_template, template_format="jinja2"))
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages(messages_templates)
            
            # Format with state variables
            formatted_prompt = prompt.format_messages(**state_dict)
            
            # Invoke LLM (sync)
            response = llm.invoke(formatted_prompt)
            
            result_content = response.content
            
            # Parse JSON if requested
            if parse_json:
                try:
                    result_content = _clean_json_string(result_content)
                    parser = JsonOutputParser()
                    
                    import json
                    try:
                        result_content = json.loads(result_content)
                    except json.JSONDecodeError:
                         result_content = parser.parse(result_content)
                         
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}. Raw content: {result_content}")
                    # Safe fallback for downstream nodes expecting dict
                    result_content = {"status": "unclear", "reasoning": "Failed to parse model output.", "raw": str(result_content)}
            
            logger.debug(f"Sync LLM node completed. Output key: {output_key}")
            return {output_key: result_content}
            
        except Exception as e:
            logger.error(f"Sync LLM node error: {e}")
            return {output_key: None, "error": str(e)}
    
    return node_function
