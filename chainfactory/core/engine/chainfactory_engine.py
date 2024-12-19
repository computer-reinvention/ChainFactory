import time
import traceback
import dataclasses
from pprint import pprint
from typing import Any, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableSerializable
from colorama import Back, Fore, Style

from chainfactory.core.factory import (
    ChainFactoryLink,
    ChainFactory,
    ChainFactoryTool,
)
from .chainfactory_engine_config import ChainFactoryEngineConfig


class ChainFactoryEngine:
    def __init__(
        self,
        factory: ChainFactory,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ):
        self.factory = factory
        self.config = config
        self.chains = self._create_chains(factory.links, config)
        self.execution_trace = {}
        self.execution_trace_list = []

    @staticmethod
    def _print_trace(trace: list[dict[str, dict]]):
        """
        Print the execution trace.
        """
        print(Fore.YELLOW + "Execution Trace:" + Style.RESET_ALL)
        for res in trace:
            print(
                Back.WHITE
                + Fore.BLACK
                + f"{res['name']}: {res['execution_time']} seconds"
                + Fore.RESET
                + Style.RESET_ALL
            )
            print(Fore.WHITE + "Input:" + Style.BRIGHT)
            pprint(res["input"])
            print(Fore.WHITE + "Output:" + Style.BRIGHT)
            pprint(res["output"])
            print("" + Style.RESET_ALL)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Call the chainlinks 1 by 1 starting from the first chainlink and arguments.
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

        trace = {}

        try:
            trace = self._execute_chains(initial_input=chain_input)
        except ValueError:
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

        return trace[-1]["output"]

    def _execute_parallel_chain(self, previous: dict, current: dict) -> list:
        """
        Execute a parallel chain.
        """
        chain: RunnableSerializable | None = current["chain"]
        link: ChainFactoryLink | ChainFactoryTool = current["link"]
        previous_output: dict = previous["output"]

        matching_vars = []
        matching_list_vars = []
        link_is_tool = isinstance(link, ChainFactoryTool)

        if not previous_output:
            raise ValueError(f"Error: output from {previous['name']} is None.")

        input_variables = []
        if link_is_tool:
            input_variables = link.input.input_variables
        else:
            assert link.prompt
            input_variables = link.prompt.input_variables

        if not input_variables:
            input_variables = []

        for var in input_variables:
            if var in previous_output:
                matching_vars.append(var)

            if "element" in var:
                varsplit = var.split("$")
                if varsplit[0] == "element":
                    raise ValueError(
                        f"Field address cannot start with 'element' in {link._name}."
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
                if isinstance(link, ChainFactoryTool):
                    fn = lambda x: link.execute(**x)
                    future = executor.submit(fn, input)
                else:
                    if not chain:
                        raise ValueError(
                            f"Chain cannot be None at this stage. Please report this issue."
                        )
                    future = executor.submit(chain.invoke, input)

                futures.append(future)

            for future in as_completed(futures):
                output = future.result()
                results.append(output)

            return results

    @staticmethod
    def _get_nested_value(d: dict, keys: list[str]):
        """
        Recursively fetches value from a nested dictionary using a list of keys.
        """
        if not keys or not isinstance(d, dict):
            return None
        if len(keys) == 1:
            return d.get(keys[0], None)
        return ChainFactoryEngine._get_nested_value(d.get(keys[0], {}), keys[1:])

    def _get_next_step_input(
        self,
        input_variables: list[str],
        previous_output: dict,
        aliases: dict[str, str] | None = None,
    ):
        """
        Get the input for the next step.
        """
        input = {}
        keys = []
        if not aliases:
            aliases = {}
        for var in input_variables:
            alias = aliases.get(var)
            if var in previous_output:
                input[alias or var] = previous_output[var]
                continue

            for sep in [".", "$"]:
                if sep not in var:
                    continue
                keys = var.split(sep)

            if not keys:
                continue

            breakpoint()
            if keys[0] in self.execution_trace.keys():
                prev = self.execution_trace[keys[0]]
                input[alias or var] = self._get_nested_value(prev, keys[1:])
            else:
                prev = previous_output
                input[alias or var] = self._get_nested_value(prev, keys)

        if not input:
            input = previous_output

        return input

    def _execute_sequential_chain(self, previous: dict, current: dict):
        """
        Execute a sequential chain.
        """
        chain: RunnableSerializable | None = current["chain"]
        link: ChainFactoryLink | ChainFactoryTool = current["link"]
        previous_link: ChainFactoryLink | ChainFactoryTool = previous["link"]
        previous_output: dict = previous["output"]
        previous_link_type: Literal["sequential", "parallel"]

        if not previous_link:
            previous_link_type = "sequential"
        else:
            previous_link_type = previous_link._link_type

        match previous_link_type:
            case "sequential":
                input = {}
                input_variables = []
                executor = None

                if isinstance(link, ChainFactoryTool):
                    input_variables = link.input.input_variables or []
                    aliases = link.input.aliases
                    executor = lambda x: link.execute(**x)
                elif isinstance(link, ChainFactoryLink):
                    assert chain
                    assert link.prompt
                    input_variables = link.prompt.input_variables or []
                    aliases = {}
                    executor = chain.invoke
                else:
                    raise ValueError("Invalid link type.")

                input = self._get_next_step_input(
                    input_variables, previous_output, aliases
                )

                return executor(input)
            case "parallel":
                assert previous_link._name in previous_output
                previous_output = self.execution_trace[previous_link._name]
                assert isinstance(previous_output, list)

                if isinstance(link, ChainFactoryTool):
                    input_variables = link.input.input_variables or []
                    input = [
                        self._get_next_step_input(input_variables, item)
                        for item in previous_output
                    ]

                    return link.execute(*input)

                assert chain
                assert link.mask

                input = {
                    link._name: [
                        f"({i + 1}) "
                        + link.mask.render(
                            {
                                k: output.get(k.split("$")[-1])
                                for k in link.mask.variables
                            }
                        )
                        for i, output in enumerate(previous_output)
                    ]
                }

                return chain.invoke(input)
            case _:
                raise ValueError(
                    f"Invalid link type: {previous_link._link_type} for chain {previous['name']}"
                )

    def proceed_yes_no(
        self,
        next_chain_name: str,
        is_tool: bool | None = False,
    ) -> bool:
        if not self.config.pause_between_executions:
            return True

        if next_chain_name:
            print(
                Fore.GREEN
                + f"\nNext to be executed: {next_chain_name}"
                + (" (tool) " if is_tool else " (chainlink) ")
                + Style.RESET_ALL
            )

        while True:
            response = (
                input(Fore.WHITE + "Proceed? (Yes/No): " + Style.RESET_ALL)
                .strip()
                .lower()
            )

            if response in ["yes", "y", ""]:
                print(
                    Fore.GREEN
                    + f"Executing chainlink: {next_chain_name}"
                    + Style.RESET_ALL
                )
                return True
            elif response in ["no", "n"]:
                print(Fore.RED + f"Terminating execution." + Style.RESET_ALL)
                return False
            else:
                continue  # ask again

    def _execute_chains(self, initial_input: dict) -> list[dict[str, Any]]:
        """
        Execute the chains, while piping the outputs to successive chains.
        """
        previous_output = None
        previous_chain_name = None
        previous_chain = None
        previous_link = None

        should_proceed = True
        for name, data in self.chains.items():
            chain: RunnableSerializable | None = data["chain"]
            link: ChainFactoryLink | ChainFactoryTool = data["link"]

            should_proceed = self.proceed_yes_no(
                next_chain_name=name,
                is_tool=isinstance(link, ChainFactoryTool),
            )

            if not should_proceed:
                break

            if not previous_output:
                previous_output = initial_input

            if previous_link and previous_link._link_type == "parallel":
                assert isinstance(previous_output, list)

                def try_convert_to_dict(item):
                    try:
                        return item.dict()
                    except:
                        return item

                if not isinstance(previous_output[0], dict):
                    previous_output = [
                        try_convert_to_dict(item) for item in previous_output
                    ]

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
            output_dict = None

            if not isinstance(output, dict):
                output_dict = output.dict()
            else:
                output_dict = output

            self.execution_trace[name] = {
                "name": name,
                "type": link._link_type,
                "is_tool": isinstance(link, ChainFactoryTool),
                "input": previous_output,
                "in": previous_output,
                "output": output,
                "out": output_dict,
                "execution_time": t2 - t1,
            }
            self.execution_trace_list.append(
                {
                    "name": name,
                    "type": link._link_type,
                    "is_tool": isinstance(link, ChainFactoryTool),
                    "input": previous_output,
                    "in": previous_output,
                    "output": output,
                    "out": output_dict,
                    "execution_time": t2 - t1,
                }
            )

            if output_dict and (
                self.config.print_trace
                or self.config.print_trace_for_single_chain
                or self.config.pause_between_executions
            ):
                print(Fore.CYAN + f"\nOutput from '{name}':" + Style.RESET_ALL)
                print("=" * 100)
                pprint(output_dict)
                print("=" * 100)

            previous_output = output
            previous_chain_name = name
            previous_chain = chain
            previous_link = link

        return self.execution_trace_list

    def _create_chains(
        self,
        chainlinks: list[ChainFactoryTool | ChainFactoryLink],
        config: ChainFactoryEngineConfig,
    ) -> dict[
        str, dict[str, RunnableSerializable | ChainFactoryLink | ChainFactoryTool]
    ]:
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
                case "ollama":
                    llm = ChatOllama(
                        temperature=config.temperature,
                        **config.model_kwargs,
                    )
                case _:
                    raise ValueError(f"Invalid provider: {config.provider}")

            if isinstance(link, ChainFactoryTool):
                runnables[link._name] = {
                    "chain": None,
                    "link": link,
                }
                continue

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
            config=config,
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
            config=config,
            internal_engine_cls=kwargs.get("internal_engine_cls", cls),
            internal_engine_config=kwargs.get("internal_engine_config", config),
            for_internal_use=kwargs.get("for_internal_use", False),
        )

        return cls(factory, config)
