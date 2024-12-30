from dataclasses import dataclass, field
from inspect import signature
import inspect
from typing import Any, Callable, Literal


@dataclass
class ChainFactoryEngineConfig:
    """
    Configuration for the ChainFactoryEngine.
    """

    provider: Literal["openai", "anthropic", "ollama"] = "openai"
    model: str = field(default="gpt-4o")
    temperature: float = field(default=0.5)
    cache: bool = field(default=False)
    max_tokens: int = field(default=1024)
    model_kwargs: dict = field(default_factory=dict)
    max_parallel_chains: int = field(default=10)
    print_trace: bool = field(default=False)
    print_trace_for_single_chain: bool = field(default=False)
    pause_between_executions: bool = field(default=True)
    tools: dict[str, Callable[..., dict]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and set provider-specific defaults"""
        # Set provider-specific model defaults if not specified
        if self.model == "gpt-4o":  # Only change if it's the default
            match self.provider:
                case "openai":
                    self.model = "gpt-4o"
                case "anthropic":
                    self.model = "claude-3-5-sonnet-latest"
                case "ollama":
                    self.model = "llama3.2"

        # Validate temperature
        if not 0 <= self.temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")

        # Validate max_tokens
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be greater than 0")

        # Validate max_parallel_chains
        if self.max_parallel_chains < 1:
            raise ValueError("max_parallel_chains must be greater than 0")

    def _validate_tool_function(self, fn: Any) -> None:
        """Validate that the function is callable and returns a dict or None"""
        if not callable(fn):
            raise TypeError(f"Tool must be callable, got {type(fn)}")

        # Get return annotation if it exists
        return_type = signature(fn).return_annotation
        if return_type is inspect.Signature.empty:
            return_type = None
        if return_type != Any and return_type != dict and return_type is not None:
            raise TypeError(
                f"Tool function {fn.__name__} must return dict or None, got {return_type}"
            )

    def register_tool(self, fn: Callable) -> Callable:
        """
        Register a function to be used as a tool. The function can have arbitrary arguments
        but should necessarily return a dictionary or None.
        """
        self._validate_tool_function(fn)
        self.tools[fn.__name__] = fn
        return fn

    def register_tools(self, fns: list[Callable[..., dict]]) -> None:
        """
        Register multiple functions to be used as tools. Each function can have arbitrary arguments
        but should necessarily return a dictionary or None.
        """
        if not isinstance(fns, list):
            raise TypeError("Expected a list of functions")

        for fn in fns:
            self.register_tool(fn)
