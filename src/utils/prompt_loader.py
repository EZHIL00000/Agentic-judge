"""
Prompt Loader Utility.

Loads and renders Jinja2 prompt templates from the prompts directory.
"""
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.managers.config_manager import get_app_config
from src.utils.logger import logger


class PromptLoader:
    """
    Loads and renders Jinja2 prompt templates from the configured prompts directory.
    """
    _instance: Optional["PromptLoader"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        try:
            config = get_app_config()
            self.prompts_base_path = Path(config.paths.prompts_base_path).resolve()
            
            if not self.prompts_base_path.exists():
                logger.warning(f"Prompts directory not found: {self.prompts_base_path}")
                self.prompts_base_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created prompts directory: {self.prompts_base_path}")
            
            # Initialize Jinja2 environment
            self.env = Environment(
                loader=FileSystemLoader(str(self.prompts_base_path)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            
            self._initialized = True
            logger.debug(f"PromptLoader initialized with path: {self.prompts_base_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize PromptLoader: {e}")
            raise
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a raw prompt template content by name.
        
        Args:
            prompt_name: Name of the prompt file (with or without .jinja2 extension)
        
        Returns:
            The raw template content as a string.
        """
        try:
            # Add extension if not provided
            if not prompt_name.endswith('.jinja2'):
                prompt_name = f"{prompt_name}.jinja2"
            
            prompt_path = self.prompts_base_path / prompt_name
            
            if not prompt_path.exists():
                logger.error(f"Prompt file not found: {prompt_path}")
                raise FileNotFoundError(f"Prompt file not found: {prompt_name}")
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"Loaded prompt: {prompt_name}")
            return content
            
        except Exception as e:
            logger.error(f"Error loading prompt '{prompt_name}': {e}")
            raise
    
    def render_prompt(self, prompt_name: str, **variables: Any) -> str:
        """
        Load and render a Jinja2 prompt template with the given variables.
        
        Args:
            prompt_name: Name of the prompt file (with or without .jinja2 extension)
            **variables: Variables to render in the template
        
        Returns:
            The rendered prompt string.
        """
        try:
            # Add extension if not provided
            if not prompt_name.endswith('.jinja2'):
                prompt_name = f"{prompt_name}.jinja2"
            
            template = self.env.get_template(prompt_name)
            rendered = template.render(**variables)
            
            logger.debug(f"Rendered prompt: {prompt_name}")
            return rendered
            
        except TemplateNotFound:
            logger.error(f"Prompt template not found: {prompt_name}")
            raise FileNotFoundError(f"Prompt template not found: {prompt_name}")
        except Exception as e:
            logger.error(f"Error rendering prompt '{prompt_name}': {e}")
            raise


@lru_cache()
def get_prompt_loader() -> PromptLoader:
    """Get the singleton PromptLoader instance."""
    return PromptLoader()


def load_prompt(prompt_name: str) -> str:
    """
    Convenience function to load a raw prompt template.
    
    Args:
        prompt_name: Name of the prompt file (e.g., "intent_system" or "intent_system.jinja2")
    
    Returns:
        The raw template content.
    """
    return get_prompt_loader().load_prompt(prompt_name)


def render_prompt(prompt_name: str, **variables: Any) -> str:
    """
    Convenience function to load and render a Jinja2 prompt template.
    
    Args:
        prompt_name: Name of the prompt file (e.g., "intent_user" or "intent_user.jinja2")
        **variables: Variables to render in the template
    
    Returns:
        The rendered prompt string.
    
    Example:
        >>> rendered = render_prompt("intent_user", user_input="I choose rock")
    """
    return get_prompt_loader().render_prompt(prompt_name, **variables)
