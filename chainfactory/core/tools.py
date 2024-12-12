from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Any
from dataclasses import dataclass
from typing import Any, TypeVar, Generic

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


@dataclass
class ToolContext(Generic[T]):
    """
    A context object that provides a clean interface for tool implementations.

    Example:
        @config.register_tool
        def my_tool(ctx: ToolContext[Classification]):
            # Access input data through ctx.input
            classification = ctx.input.classification

            # Add new data to output
            ctx.output.action = f"Action for {classification.label}"

            # Access all kwargs if needed
            all_data = ctx.kwargs

            # No need to return anything, ctx.output is automatically returned
    """

    kwargs: dict[str, Any]
    _output: dict[str, Any]

    def __init__(self, kwargs: dict[str, Any]):
        self.kwargs = kwargs
        self._output = {}

    def get(self, key: str) -> Any:
        return self.kwargs.get(key)

    @property
    def input(self) -> T:
        """Access input data through a typed interface"""
        # Creates a simple object with attribute access to kwargs
        return type("Input", (), self.kwargs)

    @property
    def output(self) -> Any:
        """Access output data through attribute interface"""

        # Creates a simple object that updates _output dict when attributes are set
        class Output:
            def __init__(self, output_dict):
                self._dict = output_dict

            def __setattr__(self, name: str, value: Any):
                if name == "_dict":
                    super().__setattr__(name, value)
                else:
                    self._dict[name] = value

            def __getattr__(self, name: str) -> Any:
                return self._dict.get(name)

        return Output(self._output)

    def get_output(self) -> dict[str, Any]:
        """Get the final output dictionary"""
        return self._output


def tool_wrapper(fn: Callable[P, dict[str, Any]]) -> Callable[P, dict[str, Any]]:
    """
    A decorator that ensures tools properly handle input/output data flow.

    This wrapper:
    1. Passes all kwargs to the tool function
    2. Merges the tool's return value with the original kwargs
    3. Ensures the return value is a dictionary

    Example:
        @config.register_tool
        @tool_wrapper
        def my_tool(**kwargs):
            # Just focus on tool logic, wrapper handles data flow
            result = do_something()
            return {"new_data": result}  # Only return new/modified data
    """

    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        # Call the original function
        result = fn(*args, **kwargs)

        # Ensure result is a dictionary
        if result is None:
            result = {}
        if not isinstance(result, dict):
            raise ValueError(
                f"Tool {fn.__name__} must return a dictionary, got {type(result)}"
            )

        # Merge with original kwargs, giving precedence to tool's return values
        return {**kwargs, **result}

    return wrapped
