import time
import traceback
from pprint import pprint
from typing import Any, Literal
from dataclasses import dataclass, field

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableSerializable

from chainfactory.types.factory import ChainFactoryLink, ChainFactory


@dataclass
class ChainFactoryEngineConfig:
    """
    Configuration for the ChainFactoryEngine.
    """

    model: str = "gpt-4o"
    temperature: float = 0
    provider: Literal["openai", "anthropic"] = "openai"
    max_tokens: int = 1024
    model_kwargs: dict = field(default_factory=dict)


class ChainFactoryEngine:
    def __init__(
        self,
        factory: ChainFactory,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ):
        self.factory = factory
        self.config = config
        self.chains = self._create_chains(factory.links, config)

    def _print_trace(self, trace: list[dict]):
        """
        Pretty print the execution trace.
        """
        print("Execution Trace:")
        for res in trace:
            print("=" * 80)
            print(f"{res['name']}: {res['execution_time']} seconds")
            print("Input:")
            pprint(res["input"])
            print("Output:")
            pprint(res["output"])

        print("=" * 80)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Call the chain with the given arguments.
        """
        chain_input = None
        if len(args) > 1:
            raise ValueError(
                "ChainFactoryEngine() only supports one positional argument."
            )
        elif len(args) == 1:
            chain_input = args[0]

        else:
            if len(kwargs) == 0:
                raise ValueError(
                    "ChainFactoryEngine.__call__() requires at least one keyword argument or one positional argument."
                )

            chain_input = kwargs

        trace = []

        try:
            trace = self._execute_chains(chain_input)
        except ValueError as e:
            traceback.print_exc()
        finally:
            self._print_trace(trace)

        if len(trace) == 0:
            raise ValueError(
                "ChainFactoryEngine.__call__() failed. Trace contains zero results."
            )
        elif kwargs.get("return_trace", False):
            return trace

        return trace[-1]["output"]

    def _execute_chains(self, initial_input: dict) -> list[dict]:
        """
        Execute the chains, while piping the outputs in successive chains.
        """
        execution_trace = []
        previous_output = None
        previous_chain_name = None
        for name, data in self.chains.items():
            chain: RunnableSerializable = data["chain"]
            link: ChainFactoryLink = data["link"]

            if previous_output:
                input = {
                    k: v
                    for k, v in previous_output.dict().items()
                    if k in link.prompt.input_variables
                }
                if len(input) == 0:
                    raise ValueError(
                        f"Piping failed. No input variable match found for {previous_chain_name} -> {name}."
                    )
            else:
                input = initial_input

            t1 = time.time()
            output = chain.invoke(input)
            t2 = time.time()

            execution_trace.append(
                {
                    "name": name,
                    "input": input,
                    "output": output,
                    "execution_time": t2 - t1,
                }
            )

            previous_output = output
            previous_chain_name = name

        return execution_trace

    def _create_chains(
        self,
        chainlinks: list[ChainFactoryLink],
        config: ChainFactoryEngineConfig,
    ) -> dict[str, dict[str, RunnableSerializable | ChainFactoryLink]]:
        """
        Create a chain from the factory.
        """
        runnables = {}
        for link in chainlinks:
            match config.provider:
                case "openai":
                    llm = ChatOpenAI(
                        temperature=config.temperature,
                        model=config.model,
                        model_kwargs=config.model_kwargs,
                    )
                case "anthropic":
                    llm = ChatAnthropic(
                        temperature=config.temperature,
                        model_name=config.model,
                        **config.model_kwargs,
                    )
                case _:
                    raise ValueError(f"Invalid provider: {config.provider}")

            if link.output is None:
                model = llm
            else:
                model = llm.with_structured_output(link.output._type)

            prompt = ChatPromptTemplate.from_template(link.prompt.template)

            runnables[link._name] = {
                "chain": prompt | model,
                "link": link,
            }

        return runnables

    @classmethod
    def from_file(
        cls,
        file_path: str,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ) -> "ChainFactoryEngine":
        """
        Create a ChainFactoryEngine from a file.
        """
        factory = ChainFactory.from_file(file_path, engine_cls=cls)

        return cls(factory, config)

    @classmethod
    def from_str(
        cls,
        fctr_str: str | None = None,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ) -> "ChainFactoryEngine":
        """
        Create a ChainFactoryEngine from a file.
        """
        factory = Factory.from_file(file_content=fctr_str, engine_cls=cls)

        return cls(factory, config)
