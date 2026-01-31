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


def create_llm_node(
    prompt_template: str,
    output_key: str,
    model_name: str = "gemini-1.5-flash",
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
            
            # Get the model
            model_manager = get_model_manager()
            llm: BaseChatModel = model_manager.get_model(model_name)
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt_template))
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages(messages)
            
            # Format with state variables
            formatted_prompt = prompt.format_messages(**state)
            
            # Invoke LLM
            response = await llm.ainvoke(formatted_prompt)
            
            result_content = response.content
            
            # Parse JSON if requested
            if parse_json:
                try:
                    parser = JsonOutputParser()
                    result_content = parser.parse(result_content)
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    # Return raw content if parsing fails
            
            logger.debug(f"LLM node completed. Output key: {output_key}")
            return {output_key: result_content}
            
        except Exception as e:
            logger.error(f"LLM node error: {e}")
            return {output_key: None, "error": str(e)}
    
    return node_function


def create_sync_llm_node(
    prompt_template: str,
    output_key: str,
    model_name: str = "gemini-1.5-flash",
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
            
            # Get the model
            model_manager = get_model_manager()
            llm: BaseChatModel = model_manager.get_model(model_name)
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt_template))
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages(messages)
            
            # Format with state variables
            formatted_prompt = prompt.format_messages(**state)
            
            # Invoke LLM (sync)
            response = llm.invoke(formatted_prompt)
            
            result_content = response.content
            
            # Parse JSON if requested
            if parse_json:
                try:
                    parser = JsonOutputParser()
                    result_content = parser.parse(result_content)
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
            
            logger.debug(f"Sync LLM node completed. Output key: {output_key}")
            return {output_key: result_content}
            
        except Exception as e:
            logger.error(f"Sync LLM node error: {e}")
            return {output_key: None, "error": str(e)}
    
    return node_function
