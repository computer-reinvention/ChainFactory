import time
import traceback
from pprint import pprint
from typing import Any, Literal
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableSerializable

from chainfactory.core.factory import ChainFactoryLink, ChainFactory


@dataclass
class ChainFactoryEngineConfig:
    """
    Configuration for the ChainFactoryEngine.
    """

    model: str = "gpt-4o"
    temperature: float = 0
    cache: bool = False
    provider: Literal["openai", "anthropic"] = "openai"
    max_tokens: int = 1024
    model_kwargs: dict = field(default_factory=dict)
    max_parallel_chains: int = 10
    print_trace: bool = False
    print_trace_for_single_chain: bool = False


class hashable_dict(dict):
    def __hash__(self):
        values = sorted([str(v) for _, v in self.items()])
        return hash(values)


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

        if len(trace) > 0:
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
            trace = self._execute_chains(initial_input=chain_input)
        except ValueError as e:
            traceback.print_exc()
        finally:
            if self.config.print_trace:
                if len(trace) > 1:
                    self._print_trace(trace)
                elif len(trace) == 1 and self.config.print_trace_for_single_chain:
                    self._print_trace(trace)
                else:
                    pass

        if len(trace) == 0:
            raise ValueError(
                "ChainFactoryEngine.__call__() failed. Trace contains zero results."
            )
        elif kwargs.get("return_trace", False):
            return trace

        return trace[-1]["output"]

    def _execute_parallel_chain(self, previous: dict, current: dict) -> list:
        """
        Execute a parallel chain.
        """
        chain: RunnableSerializable = current["chain"]
        link: ChainFactoryLink = current["link"]
        previous_output = previous["output"]

        matching_vars = []
        matching_list_vars = []

        if not previous_output:
            raise ValueError(f"Error: output from {previous['name']} is None.")

        if not link.prompt:
            raise ValueError(f"link.prompt cannot be None for chain {link._name}")

        if not link.prompt.input_variables:
            raise ValueError(
                f"unable to determine input_variables for chain: {link._name}"
            )

        for var in link.prompt.input_variables:
            if var in previous_output:
                matching_vars.append(var)

            if "element" in var:
                varsplit = var.split("$")
                if varsplit[0] == "element":
                    raise ValueError(
                        f"Field address cannot start with 'element' in {var}."
                    )

                if varsplit[0] not in previous_output:
                    raise ValueError(
                        f"The iterable field {varsplit[0]} is not present in the previous chain's output."
                    )

                keys = []
                subkey_mode = False
                for v in varsplit:
                    if subkey_mode:
                        keys.append(v)

                    if v == "element":
                        subkey_mode = True
                        continue

                if len(keys) > 0:
                    iterable_len = len(previous_output[varsplit[0]])

                    if len(matching_list_vars) > 0:
                        last_iterable_len = len(
                            previous_output[matching_list_vars[-1]["parent"]]
                        )

                        if iterable_len != last_iterable_len:
                            raise ValueError(
                                f"All the iterable fields must have the same length. {var} has {iterable_len} elements and {matching_list_vars[-1]['var']} has {last_iterable_len} elements."
                            )

                matching_list_vars.append(
                    {
                        "var": var,
                        "varsplit": varsplit,
                        "parent": varsplit[0],
                        "keys": keys,
                    }
                )

        if len(matching_list_vars) == 0:
            raise ValueError(
                f"No iterable field found in output from chain {previous['name']} - the succeeding parallel chain {current['name']} cannot be executed."
            )

        current_inputs = []
        iterable_len = len(previous_output[matching_list_vars[-1]["parent"]])

        for i in range(iterable_len):
            current_input = {}
            for var in matching_vars:
                current_input[var] = previous_output[var]

            for var in matching_list_vars:
                element = previous_output[var["parent"]][i]

                if len(var["keys"]) == 0:
                    current_input[var["var"]] = element
                    continue

                for key in var["keys"]:
                    if not element:
                        current_input[var["var"]] = None
                        break

                    element = element.get(key)

                if element:
                    current_input[var["var"]] = element
                    continue

            current_inputs.append(current_input)

        # execute the chains in parallel, preserving the order of the inputs
        with ThreadPoolExecutor(self.config.max_parallel_chains) as executor:
            futures = []
            results = []
            for input in current_inputs:
                future = executor.submit(chain.invoke, input)
                futures.append(future)

            for future in as_completed(futures):
                output = future.result()
                results.append(output)

            return results

    def _execute_sequential_chain(self, previous: dict, current: dict):
        """
        Execute a sequential chain.
        """
        chain: RunnableSerializable = current["chain"]
        link: ChainFactoryLink = current["link"]
        previous_link: ChainFactoryLink = previous["link"]
        previous_output: dict = previous["output"]
        previous_link_type: Literal["sequential", "parallel"]

        if not previous_link:
            previous_link_type = "sequential"
        else:
            previous_link_type = previous_link._link_type

        match previous_link_type:
            case "sequential":
                assert link.prompt
                input = {
                    k: v
                    for k, v in previous_output.items()
                    if k in link.prompt.input_variables
                }

                if not input:
                    raise ValueError(
                        f"Piping failed. No matching input variables found for linking chains {previous['name']} -> {current['name']}."
                    )

                return chain.invoke(input)
            case "parallel":
                assert link.mask
                assert previous_link._name in previous_output
                previous_output = previous_output[previous_link._name]
                assert isinstance(previous_output, list)

                input = {
                    link._name: [
                        f"({i + 1}) "
                        + link.mask.render(
                            {k: output.get(k) for k in link.mask.variables}
                        )
                        for i, output in enumerate(previous_output)
                    ]
                }

                if not input[link._name]:
                    raise ValueError(
                        f"Piping failed. No matching variables found for linking chains {previous['name']} -> {current['name']}. Please note that this is a convex chain and hence the matching variables are determined by the mask."
                    )

                print("=====================")
                print("Convex Chain Input:")
                pprint(input)
                print("=====================")
                return chain.invoke(input)
            case _:
                raise ValueError(
                    f"Invalid link type: {previous_link._link_type} for chain {previous['name']}"
                )

    def _execute_chains(self, initial_input: dict) -> list[dict]:
        """
        Execute the chains, while piping the outputs to successive chains.
        """
        execution_trace = []
        previous_output = None
        previous_chain_name = None
        previous_chain = None
        previous_link = None

        for name, data in self.chains.items():
            chain: RunnableSerializable = data["chain"]
            link: ChainFactoryLink = data["link"]

            if not previous_output:
                previous_output = initial_input

            if previous_link and previous_link._link_type == "parallel":
                assert isinstance(previous_output, list)

                if not isinstance(previous_output[0], dict):
                    previous_output = [item.dict() for item in previous_output]

                previous_output = {
                    previous_link._name: previous_output,
                }

            previous = {
                "name": previous_chain_name,
                "output": previous_output,
                "link": previous_link,
                "chain": previous_chain,
            }

            current = {
                "name": name,
                "output": None,
                "link": link,
                "chain": chain,
            }

            t1 = time.time()
            match link._link_type:
                case "sequential":
                    output = self._execute_sequential_chain(previous, current)
                case "parallel":
                    output = self._execute_parallel_chain(previous, current)
                case _:
                    raise ValueError(f"Invalid link type: {link._link_type}")
            t2 = time.time()

            assert output

            execution_trace.append(
                {
                    "name": name,
                    "type": link._link_type,
                    "input": previous_output,
                    "output": output,
                    "execution_time": t2 - t1,
                }
            )

            if not isinstance(output, list):
                output = output.dict()

            previous_output = output
            previous_chain_name = name
            previous_chain = chain
            previous_link = link

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

            assert link.prompt
            assert link.prompt.template

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
        **kwargs,
    ) -> "ChainFactoryEngine":
        """
        Create a ChainFactoryEngine from a file.
        """
        factory = ChainFactory.from_file(
            file_path,
            internal_engine_cls=kwargs.get("internal_engine_cls", cls),
            internal_engine_config=kwargs.get("internal_engine_config", config),
        )

        return cls(factory, config)

    @classmethod
    def from_str(
        cls,
        content: str,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
        **kwargs,
    ) -> "ChainFactoryEngine":
        """
        Create a ChainFactoryEngine from a file.
        """
        factory = ChainFactory.from_str(
            content,
            internal_engine_cls=kwargs.get("internal_engine_cls", cls),
            internal_engine_config=kwargs.get("internal_engine_config", config),
        )

        return cls(factory, config)
