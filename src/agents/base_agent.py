"""
Base agent class for APPA system.

This module defines the abstract base class that all agents inherit from,
ensuring consistent interface and behavior across the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from ..utils.logging_config import LoggerMixin


class BaseAgent(ABC, LoggerMixin):
    """
    Abstract base class for all APPA agents.
    
    Each agent has a single, well-defined responsibility with clear
    input/output specifications.
    """
    
    def __init__(self, config: Dict[str, Any], name: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            config: System configuration dictionary
            name: Optional agent name (defaults to class name)
        """
        self.config = config
        self.name = name or self.__class__.__name__
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.metrics: Dict[str, Any] = {}
        
        self.logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        Process input data and return results.
        
        This is the main method that each agent must implement.
        
        Args:
            input_data: Input data specific to the agent
            
        Returns:
            Processed results specific to the agent
            
        Raises:
            AgentError: If processing fails
        """
        pass
    
    def run(self, input_data: Any) -> Any:
        """
        Run the agent with timing and error handling.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Processing results
            
        Raises:
            AgentError: If processing fails
        """
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.name} processing")
        
        try:
            # Validate input
            self._validate_input(input_data)
            
            # Process data
            result = self.process(input_data)
            
            # Validate output
            self._validate_output(result)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            self.logger.info(f"Completed {self.name} processing in {duration:.2f}s")
            self._update_metrics(input_data, result, duration)
            
            return result
            
        except Exception as e:
            self.end_time = datetime.now()
            self.logger.error(f"Error in {self.name}: {str(e)}")
            raise AgentError(f"{self.name} processing failed: {str(e)}") from e
    
    def _validate_input(self, input_data: Any) -> None:
        """
        Validate input data format and content.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            AgentError: If input is invalid
        """
        if input_data is None:
            raise AgentError(f"{self.name} requires non-None input data")
    
    def _validate_output(self, output_data: Any) -> None:
        """
        Validate output data format and content.
        
        Args:
            output_data: Output data to validate
            
        Raises:
            AgentError: If output is invalid
        """
        if output_data is None:
            raise AgentError(f"{self.name} produced None output")
    
    def _update_metrics(self, input_data: Any, output_data: Any, duration: float) -> None:
        """
        Update agent performance metrics.
        
        Args:
            input_data: Input data that was processed
            output_data: Output data that was produced
            duration: Processing duration in seconds
        """
        self.metrics.update({
            'last_run_duration': duration,
            'last_run_timestamp': self.start_time.isoformat(),
            'total_runs': self.metrics.get('total_runs', 0) + 1,
            'total_duration': self.metrics.get('total_duration', 0) + duration
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        metrics = self.metrics.copy()
        if metrics.get('total_runs', 0) > 0:
            metrics['average_duration'] = metrics['total_duration'] / metrics['total_runs']
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset agent performance metrics."""
        self.metrics.clear()
        self.logger.info(f"Reset metrics for {self.name}")
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the value
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default


class AgentError(Exception):
    """Exception raised by agents during processing."""
    pass


class AgentRegistry:
    """Registry for managing agent instances."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent instance.
        
        Args:
            agent: Agent instance to register
        """
        self._agents[agent.name] = agent
    
    def get(self, name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """
        Get list of registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all registered agents.
        
        Returns:
            Dictionary mapping agent names to their metrics
        """
        return {name: agent.get_metrics() for name, agent in self._agents.items()}


# Global agent registry
agent_registry = AgentRegistry()


if __name__ == "__main__":
    # Test base agent functionality
    class TestAgent(BaseAgent):
        def process(self, input_data):
            return f"Processed: {input_data}"
    
    config = {'test': 'value'}
    agent = TestAgent(config)
    
    result = agent.run("test input")
    print(f"Result: {result}")
    print(f"Metrics: {agent.get_metrics()}")
