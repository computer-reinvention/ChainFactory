from dataclasses import dataclass, field
from typing import Callable, Literal


@dataclass
class ChainFactoryEngineConfig:
    """
    Configuration for the ChainFactoryEngine.
    """

    provider: Literal["openai", "anthropic", "ollama"] = "openai"
    model: str = field(default="gpt-4")
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
        if self.model == "gpt-4":  # Only change if it's the default
            match self.provider:
                case "openai":
                    self.model = "gpt-4"
                case "anthropic":
                    self.model = "claude-3-opus-20240229"
                case "ollama":
                    self.model = "llama2"

        # Validate temperature
        if not 0 <= self.temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")

        # Validate max_tokens
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be greater than 0")

        # Validate max_parallel_chains
        if self.max_parallel_chains < 1:
            raise ValueError("max_parallel_chains must be greater than 0")

    def register_tool(self, fn: Callable) -> Callable:
        """
        Register a function to be used as a tool. The function can have arbitrary arguments but should necessarily return a dictionary.
        """
        self.tools[fn.__name__] = fn
        return fn

    def register_tools(self, fns: list[Callable[..., dict]]) -> None:
        """
        Register a function to be used as a tool. The function can have arbitrary arguments but should necessarily return a dictionary.
        """
        for fn in fns:
            self.register_tool(fn)
