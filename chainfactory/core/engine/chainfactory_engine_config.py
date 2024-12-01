from dataclasses import dataclass, field
from typing import Callable, Literal


@dataclass
class ChainFactoryEngineConfig:
    """
    Configuration for the ChainFactoryEngine.
    """

    model: str = "gpt-4o"
    temperature: float = 0.5
    cache: bool = False
    provider: Literal["openai", "anthropic", "ollama"] = "openai"
    max_tokens: int = 1024
    model_kwargs: dict = field(default_factory=dict)
    max_parallel_chains: int = 10
    print_trace: bool = False
    print_trace_for_single_chain: bool = False
    pause_between_executions: bool = True
    tools: dict[str, Callable[..., dict]] = field(default_factory=dict)

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
