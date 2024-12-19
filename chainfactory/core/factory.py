"""
This module defines the core `Factory` type representation.
"""

from datetime import datetime
import uuid
import yaml
import farmhash
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from typing import Any, Optional, Literal
import importlib.resources as pkg_resources
from abc import abstractmethod

from chainfactory.core.engine.chainfactory_engine_config import ChainFactoryEngineConfig
from chainfactory.core.utils import load_cache_file, save_cache_file

from .components import (
    FactoryDefinitions,
    FactoryPrompt,
    FactoryOutput,
    FactoryInput,
    FactoryMask,
)


class BaseChainFactoryLink:
    _name: str
    _link_type: Literal["sequential", "parallel"] = "sequential"
    _is_tool: bool = False

    def __init__(
        self,
        name: str,
        link_type: Literal["sequential", "parallel"] = "sequential",
        is_tool: bool = False,
    ):
        self._name = name
        self._link_type = link_type
        self._is_tool = is_tool

    @abstractmethod
    def execute(self, *args, **kwargs) -> dict:
        pass

    @classmethod
    @abstractmethod
    def from_file(
        cls,
        file_path: str,
        file_content: str | None = None,
        *args,
        **kwargs,
    ) -> "BaseChainFactoryLink":
        pass


class ChainFactoryTool(BaseChainFactoryLink):
    def __init__(
        self,
        name: str,
        source: dict,
        link_type: Literal["sequential", "parallel"] = "sequential",
        fn: Callable[..., dict] | None = None,
    ):
        super().__init__(
            name=name,
            link_type=link_type,
            is_tool=True,
        )
        self.fn = fn
        input = source.get("in", {})
        self.input = FactoryInput(attributes=input)

    def execute(self, **kwargs) -> dict:
        if not self.fn:
            raise ValueError("ChainFactoryTool.fn is None. Cannot execute.")

        if self.input.input_variables:
            input = {k.rsplit(".")[-1]: v for k, v in kwargs.items()}
        else:
            input = kwargs

        res = self.fn(**input)
        if not res:
            return {**kwargs}

        if isinstance(res, dict):
            return {**kwargs, **res}

        raise ValueError(
            f"ChainFactoryTool.fn must return a dict or None. Got {type(res)}."
        )

    @classmethod
    def from_file(cls):
        """
        We do not need to parse this.
        """
        raise NotImplementedError


class ChainFactoryLink(BaseChainFactoryLink):
    """
    This type is the representation of a factory.
    """

    def __init__(
        self,
        name: str,
        source: Optional[dict] = None,
        parsed_source: Optional[Any] = None,
        definitions: Optional[FactoryDefinitions] = None,
        output: Optional[FactoryOutput] = None,
        prompt: Optional[FactoryPrompt] = None,
        mask: Optional[FactoryMask] = None,
        link_type: Literal["sequential", "parallel"] = "sequential",
    ):
        self._name = name
        self._source = source  # the YAML template
        self._parsed_source = parsed_source  # the parsed YAML object / dictionary

        self.definitions: Optional[FactoryDefinitions] = definitions  # section `def`
        self.prompt: Optional[FactoryPrompt] = prompt  # section `prompt`
        self.mask: Optional[FactoryMask] = (
            mask  # section `mask` (only for convex chainlinks)
        )
        self.output: Optional[FactoryOutput] = output  # section `out`
        self._link_type = link_type

    @classmethod
    def from_file(
        cls,
        name: str,
        source: dict,
        link_type: Literal["sequential", "parallel"] = "sequential",
        convex: bool = False,
        global_defs: FactoryDefinitions | None = None,
        internal_engine_cls: Any | None = None,
        internal_engine_config: Any | None = None,
        **kwargs,
    ) -> "ChainFactoryLink":
        """
        Parse the source .fctr file into a `ChainFactoryLink` object.
        Extensions are not supported yet.

        Args:
            file_path (str): The path to the .fctr file.
        Returns:
            ChainFactoryLink: The parsed `ChainFactoryLink` object.
        """
        input = source.get("in")
        purpose = source.get("purpose")
        prompt = source.get("prompt")
        defs = source.get("def")
        output = source.get("out")
        mask = source.get("mask")

        if isinstance(prompt, str):
            prompt = {
                "type": "template",
                "template": prompt,
                "purpose": None,
            }

        if prompt and not purpose:
            purpose = prompt.get("purpose")

        if not prompt and not purpose:
            raise ValueError(
                "Neither purpose nor a prompt template were provided. Both are required if the chainlink is not a tool."
            )

        factory_input = (
            None
            if not input
            else FactoryInput(
                attributes=input,
            )
        )
        input_variables = [] if not factory_input else factory_input.input_variables

        if purpose:
            cachekey = str(
                farmhash.FarmHash64(
                    purpose + ",".join([name] if convex else sorted(input_variables)),
                )
            )
            cached: dict[str, str] | None = load_cache_file(cachekey)
            if cached:
                print(
                    f"[{name}] Loading prompt template from cache for given purpose (hash: {cachekey}).",
                )

                factory_prompt = FactoryPrompt(
                    template=cached.get("prompt_template", ""),
                    purpose=purpose,
                    input_variables=input_variables,
                )
            else:
                assert internal_engine_cls
                assert internal_engine_config

                with pkg_resources.open_text(
                    "chainfactory.chains", "generate_prompt_template.fctr"
                ) as file:
                    file_content = file.read()
                    print(
                        f"[{name}]",
                        "Generating Prompt Template: ",
                        purpose,
                        f"({cachekey})",
                    )
                    engine = internal_engine_cls.from_str(
                        file_content,
                        config=internal_engine_config,
                        for_internal_use=True,
                    )
                    generated_prompt_template = engine(
                        purpose=purpose,
                        input_variables=[name] if convex else input_variables,
                    ).prompt_template

                    save_cache_file(
                        cachekey,
                        {
                            "chainlink": name,
                            "purpose": purpose,
                            "input_variables": input_variables,
                            "prompt_template": generated_prompt_template,
                            "ts": datetime.now().isoformat(),
                        },
                    )

                    factory_prompt = FactoryPrompt(
                        template=generated_prompt_template,
                        purpose=purpose,
                        input_variables=input_variables,
                    )
        elif prompt:
            factory_prompt = FactoryPrompt(
                template=prompt["template"],
                purpose=None,
                input_variables=input_variables,
            )
        else:
            raise ValueError(
                "prompt / prompt.template or purpose / prompt.purpose must be provided."
            )

        factory_defs = FactoryDefinitions(definitions=defs)

        if factory_defs and global_defs:
            factory_defs.extend(global_defs)

        factory_output = FactoryOutput(
            attributes=output or {},
            definitions=factory_defs.defined_types,
        )

        if isinstance(mask, str):
            if mask == "auto":
                factory_mask = FactoryMask(
                    type="auto",
                    variables=[],
                    template=None,
                )
            else:
                factory_mask = FactoryMask(
                    type="template",
                    template=mask,
                    variables=[],
                )
        elif isinstance(mask, dict):
            template = mask.get("template", None)
            variables = mask.get("variables", [])
            if not template and not variables:
                raise ValueError(
                    "FactoryMask.variables cannot be empty when type is auto."
                )
            elif not template:
                cachekey = str(farmhash.FarmHash64(str(sorted(variables))))
                if cached := load_cache_file(cachekey):
                    factory_mask = FactoryMask(
                        template=cached.get("mask_template"),
                        variables=variables,
                    )
                else:
                    assert internal_engine_cls
                    assert internal_engine_config

                    with pkg_resources.open_text(
                        "chainfactory.chains", "generate_mask_template.fctr"
                    ) as file:
                        file_content = file.read()

                        print(
                            f"[{name}]", "Generating new mask template for:", variables
                        )

                        engine = internal_engine_cls.from_str(
                            file_content,
                            config=internal_engine_config,
                            for_internal_use=True,
                        )

                        generated_mask_template = engine(
                            variables=variables,
                        ).template

                        factory_mask = FactoryMask(
                            template=generated_mask_template,
                            variables=variables,
                        )

                        save_cache_file(
                            cachekey,
                            {
                                "chainlink": name,
                                "variables": variables,
                                "mask_template": generated_mask_template,
                                "ts": datetime.now().isoformat(),
                            },
                        )
            else:
                factory_mask = FactoryMask(
                    template=mask.get("template"),
                    variables=[],
                )
        else:
            if convex:
                raise ValueError(
                    f"A convex (parallel to sequential) chainlink necessarily requires a valid mask. Please provide a mask or alter the convexity by either making preceding chain sequential or the current chain: {name} parallel."
                )

            factory_mask = None

        return cls(
            name=name,
            source=source,
            parsed_source=source,
            prompt=factory_prompt,
            output=factory_output,
            definitions=factory_defs,
            mask=factory_mask,
            link_type=link_type,
        )

    def execute(self, data: dict) -> dict:
        return super().execute(data)


def chainfactorylink_or_tool(
    name: str,
    file_path: str | None = None,
    file_content: str | None = None,
    link_type: Literal["sequential", "parallel"] = "sequential",
    convex: bool = False,
    global_defs: FactoryDefinitions | None = None,
    internal_engine_cls: Any | None = None,
    internal_engine_config: Any | None = None,
    is_tool: bool = False,
    tools: dict[str, Callable[..., dict]] | None = None,
    **kwargs,
) -> ChainFactoryLink | ChainFactoryTool:
    """
    Parse the source .fctr file into a `ChainFactoryLink` object.
    Extensions are not supported yet.

    Args:
        file_path (str): The path to the .fctr file.
    Returns:
        ChainFactoryLink: The parsed `ChainFactoryLink` object.
    """
    source = {}
    if file_content:
        source = yaml.safe_load(file_content)
    elif file_path:
        source = yaml.safe_load(open(file_path, "r"))
    else:
        pass

    if not source and not is_tool:
        raise ValueError("Either file_path or file_object must be provided.")

    if is_tool:
        if not tools:
            raise ValueError("tools must be provided when is_tool is True.")

        fn = tools.get(name)
        if not fn:
            raise ValueError(f"tool {name} has not been registered in engine config.")

        return ChainFactoryTool(
            name=name,
            link_type=link_type,
            fn=fn,
            source=source,
        )

    return ChainFactoryLink.from_file(
        name=name,
        source=source,
        link_type=link_type,
        convex=convex,
        global_defs=global_defs,
        internal_engine_cls=internal_engine_cls,
        internal_engine_config=internal_engine_config,
    )


@dataclass
class ChainFactory:
    """
    This type is the representation of multiple factories.
    """

    links: list[ChainFactoryTool | ChainFactoryLink]
    base_chain: Optional["ChainFactory"] = None
    definitions: FactoryDefinitions = field(default_factory=FactoryDefinitions)
    config: ChainFactoryEngineConfig = field(default_factory=ChainFactoryEngineConfig)
    internal_engine_cls: Any = None
    internal_engine_config: Any = None
    source: dict | None = None

    @classmethod
    def from_file(
        cls,
        file_path: str,
        config: ChainFactoryEngineConfig | None = None,
        internal_engine_cls: Any | None = None,
        internal_engine_config: Any | None = None,
    ) -> "ChainFactory":
        """
        Parse the source .fctr file into a `Factory` object.

        Args:
            file_path (str): The path to the .fctr file.
            engine_cls (Any): The engine class to generate the prompt template from purpose.

        Returns:
            Factory: The parsed `ChainFactory` object.
        """
        with open(file_path, "r") as file:
            content = file.read()

        return cls.from_str(
            content,
            config=config,
            internal_engine_cls=internal_engine_cls,
            internal_engine_config=internal_engine_config,
        )

    @classmethod
    def from_str(
        cls,
        content: str,
        path: str | None = None,
        config: ChainFactoryEngineConfig | None = None,
        internal_engine_cls: Any | None = None,
        internal_engine_config: Any | None = None,
        for_internal_use: bool = False,
    ) -> "ChainFactory":
        """
        Parse the content of a .fctr file into a `ChainFactory` object.

        Args:
            content (str): The content of the .fctr file.
            path (str): The path to the .fctr file. Can be used as an alternative to content.
            internal_engine_cls (Any): The engine class to generate the prompt template from purpose.
            internal_engine_config (Any): The engine config to generate the prompt template from purpose.

        Returns:
            Factory: The parsed `ChainFactory` object.
        """
        lines = content.splitlines()
        parts = {}
        current_part = None
        base_chain_path = None

        if "@chainlink" not in content:
            return cls(
                links=[
                    chainfactorylink_or_tool(
                        name="chainlink"
                        + ("-internal-" if for_internal_use else "-")
                        + str(uuid.uuid4().hex),
                        file_content=content,
                        file_path=path,
                        is_tool=False,
                    ),
                ]
            )

        for i, line in enumerate(lines):
            if not line:
                continue

            if line.startswith("#"):
                continue

            chainlink_directive = line.strip().startswith("@chainlink")
            extends_directive = line.strip().startswith("@extends")
            tool_directive = line.strip().startswith("@tool")

            if extends_directive:
                if base_chain_path:
                    raise ValueError(
                        f"Error on line {i}. @extends directive can only be used once."
                    )

                extends_parts = [part.strip() for part in line.strip().split(" ")]
                if len(extends_parts) != 2:
                    raise ValueError(
                        f"Error on line {i}. Invalid @extends directive. Must be of the form `@extends [path]`."
                    )

                base_chain_path = extends_parts[1]
                continue

            is_directive = tool_directive or chainlink_directive or extends_directive
            type_str = None
            if is_directive:
                if tool_directive:
                    type_str = "@tool"
                elif chainlink_directive:
                    type_str = "@chainlink"
                elif extends_directive:
                    type_str = "@extends"

            if not is_directive and current_part:
                parts[current_part]["lines"].append(line)
                continue

            if line.startswith("  "):
                line = line.replace("  ", "\t")

            tokens = [token for token in line.strip().split(" ")]

            if len(tokens) > 3:
                raise ValueError(
                    f"Error on line {i}. Invalid {type_str} definition. Must be of the form `{type_str} <name> <link_type>`."
                )
            elif len(tokens) == 3:
                name = tokens[1]
                link_type = tokens[2]

                if link_type not in ["sequential", "parallel", "--", "||"]:
                    raise ValueError(
                        f"Error on line {i}. Invalid {type_str} definition. Must be of the form `{type_str} [name] [link_type: 'sequential' | '--' | 'parallel' | '||']."
                    )

                if name in parts and not parts[name].get("is_tool"):
                    raise ValueError(
                        f"Error on line {i}. Invalid {type_str} definition. Another chainlink with the same name exists."
                    )
            elif len(tokens) == 2:
                unknown_token = tokens[1]
                if unknown_token in ["sequential", "parallel", "--", "||"]:
                    # assign random name
                    name = "chainlink-" + str(uuid.uuid4().hex)
                    link_type = unknown_token
                else:
                    name = tokens[1]
                    link_type = "sequential"
            else:
                name = "chainlink-" + str(uuid.uuid4().hex)
                link_type = "sequential"

            if link_type == "--":
                link_type = "sequential"
            elif link_type == "||":
                link_type = "parallel"

            current_part = name
            parts[name] = {
                "beginning_line": i,
                "link_type": link_type,
                "is_tool": tool_directive,
                "lines": [],
            }

        chainlinks = []
        previous_link = None
        global_defs = FactoryDefinitions()
        for name, part in parts.items():
            if not part["lines"] and not part.get("is_tool"):
                raise ValueError(
                    f"Error on line {part['beginning_line']}. Chainlink definition cannot be empty. Empty direcives are only allowed for tools."
                )

            convex = (
                previous_link
                and previous_link._link_type == "parallel"
                and part["link_type"] == "sequential"
            )

            link = chainfactorylink_or_tool(
                name=name,
                file_content="\n".join(part["lines"]).replace("\t", "  "),
                link_type=part["link_type"],
                convex=bool(convex),
                global_defs=global_defs,
                internal_engine_cls=internal_engine_cls,
                internal_engine_config=internal_engine_config,
                is_tool=part.get("is_tool", False),
                tools={} if not config else config.tools,
            )

            if isinstance(link, ChainFactoryTool):
                previous_link = link
                chainlinks.append(link)
                continue

            if (
                previous_link
                and previous_link._link_type == "parallel"
                and not previous_link._is_tool
            ):
                assert link.prompt
                assert link.prompt.input_variables
                assert link.prompt.template

                match link._link_type:
                    case "parallel":
                        updated_input_variables = []
                        for var in link.prompt.input_variables:
                            if var.startswith(previous_link._name):
                                continue

                            if var.startswith("element"):
                                full_var = f"{previous_link._name}${var}"
                            else:
                                full_var = f"{previous_link._name}$element${var}"

                            updated_input_variables.append(full_var)
                            link.prompt.template = link.prompt.template.replace(
                                "{" + var + "}",
                                "{" + full_var + "}",
                            )

                        if updated_input_variables:
                            link.prompt.input_variables = updated_input_variables
                    case "sequential":
                        pass
                    case _:
                        raise ValueError(
                            f"Invalid chainlink type: {link._link_type}. Must be one of 'sequential', '--', 'parallel', '||' or empty."
                        )

            previous_link = link
            chainlinks.append(link)

            if link.definitions:
                global_defs.extend(link.definitions)

        base_chain = None
        if base_chain_path:
            base_chain = cls.from_file(
                base_chain_path,
                internal_engine_cls=internal_engine_cls,
                internal_engine_config=internal_engine_config,
            )
            chainlinks = base_chain.links + chainlinks
            global_defs.extend(base_chain.definitions)

            # TODO: add a basic compatibility check between the base chain and the current chain

        return cls(
            links=chainlinks,
            definitions=global_defs,
            base_chain=base_chain,
            internal_engine_cls=internal_engine_cls,
            internal_engine_config=internal_engine_config,
        )
