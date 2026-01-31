import importlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Callable

from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from src.models.game_models import GameState
from src.managers.config_manager import get_app_config

logger = logging.getLogger(__name__)


class WorkflowLoader:
    """
    Loads and compiles a LangGraph workflow from a JSON configuration file.
    
    Nodes are loaded from the nodes_base_path defined in config.json.
    """
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.graph_config = self._load_json()
        self._compiled_graph: CompiledGraph = None
        
        # Get nodes base path from app config and convert to module format
        app_config = get_app_config()
        # Convert path format (src/nodes) to module format (src.nodes)
        self.nodes_base_module = app_config.paths.nodes_base_path.replace("/", ".").replace("\\", ".")
        
    def _load_json(self) -> Dict[str, Any]:
        """Loads the JSON configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Graph config not found: {self.config_path}")
        
        with open(self.config_path, "r") as f:
            return json.load(f)

    def _import_node_function(self, node_id: str, function_name: str) -> Callable:
        """
        Dynamically imports a function from the nodes directory.
        
        Args:
            node_id: The node file name (without .py), e.g., "intent_node"
            function_name: The function to import from that module
        
        Returns:
            The imported function
        """
        module_path = f"{self.nodes_base_module}.{node_id}"
        try:
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)
            logger.debug(f"Imported {function_name} from {module_path}")
            return func
        except ImportError as e:
            logger.error(f"Failed to import module {module_path}: {e}")
            raise
        except AttributeError as e:
            logger.error(f"Function {function_name} not found in {module_path}: {e}")
            raise

    def build_graph(self) -> CompiledGraph:
        """
        Builds and compiles the StateGraph based on JSON config.
        """
        if self._compiled_graph:
            return self._compiled_graph
            
        logger.info(f"Building workflow: {self.graph_config.get('name')}")
        
        # Initialize StateGraph with the GameState model
        workflow = StateGraph(GameState)
        
        # Add Nodes
        for node_cfg in self.graph_config["nodes"]:
            node_id = node_cfg["node_id"]
            function_name = node_cfg["function"]
            func = self._import_node_function(node_id, function_name)
            workflow.add_node(node_id, func)
            logger.debug(f"Added node: {node_id}")
            
        # Add Edges
        for edge_cfg in self.graph_config["edges"]:
            source = edge_cfg["from"]
            target = edge_cfg["to"]
            
            if source == "__start__":
                workflow.set_entry_point(target)
                logger.debug(f"Set entry point: {target}")
            elif target == "__end__":
                workflow.add_edge(source, END)
                logger.debug(f"Added edge: {source} -> END")
            else:
                workflow.add_edge(source, target)
                logger.debug(f"Added edge: {source} -> {target}")
        
        self._compiled_graph = workflow.compile()
        logger.info("Workflow compiled successfully.")
        return self._compiled_graph

    def get_graph(self) -> CompiledGraph:
        """Returns the compiled graph, building it if necessary."""
        if not self._compiled_graph:
            return self.build_graph()
        return self._compiled_graph


# Singleton-like accessor
_loader_instance = None

def get_workflow() -> CompiledGraph:
    """Global accessor for the compiled game workflow."""
    global _loader_instance
    if _loader_instance is None:
        graph_json_path = Path("src/config/graph.json").resolve() 
        _loader_instance = WorkflowLoader(str(graph_json_path))
        
    return _loader_instance.get_graph()
