"""
This module defines the core `Factory` type representation.
"""

from datetime import datetime
import time
import uuid
import yaml
import farmhash
from typing import Any, Optional
from dataclasses import dataclass
from typing import Any, Optional, Literal
import importlib.resources as pkg_resources

from chainfactory.core.utils import load_cache_file, save_cache_file

from .components import (
    FactoryDefinitions,
    FactoryPrompt,
    FactoryOutput,
    FactoryInput,
    FactoryMask,
)


class ChainFactoryLink:
    """
    This type is the representation of a factory.
    """

    _name: str
    _source: Optional[str]
    _parsed_source: Optional[Any]
    _link_type: Literal["sequential", "parallel"] = "sequential"
    global_definitions: Optional[FactoryDefinitions]
    definitions: Optional[FactoryDefinitions]
    output: Optional[FactoryOutput]
    prompt: Optional[FactoryPrompt]
    mask: Optional[FactoryMask]

    def __init__(
        self,
        name: str,
        source: Optional[str] = None,
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
        file_path: str | None = None,
        file_content: str | None = None,
        link_type: Literal["sequential", "parallel"] = "sequential",
        convex: bool = False,
        global_defs: FactoryDefinitions | None = None,
        internal_engine_cls: Any | None = None,
        internal_engine_config: Any | None = None,
    ) -> "ChainFactoryLink":
        """
        Parse the source .fctr file into a `ChainFactoryLink` object.
        Extensions are not supported yet.

        Args:
            file_path (str): The path to the .fctr file.
        Returns:
            ChainFactoryLink: The parsed `ChainFactoryLink` object.
        """
        if file_content:
            source = yaml.safe_load(file_content)
        elif file_path:
            source = yaml.safe_load(open(file_path, "r"))
        else:
            raise ValueError("Either file_path or file_object must be provided.")

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
            raise ValueError("Neither purpose nor a prompt template were provided.")

        factory_input = (
            None
            if not input
            else FactoryInput(
                attributes=input,
            )
        )
        input_variables = None if not factory_input else factory_input.input_variables

        if purpose:
            cachekey = str(
                farmhash.FarmHash64(
                    purpose + ",".join([name] if convex else sorted(input_variables)),
                )
            )
            if cached := load_cache_file(cachekey):
                print(
                    f"[{name}]",
                    "Loading prompt template from file cached for purpose:",
                    purpose,
                    f"({cachekey})",
                )
                factory_prompt = FactoryPrompt(
                    template=cached.get("prompt_template"),
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
                        "Generating new prompt template for purpose:",
                        purpose,
                        f"({cachekey})",
                    )
                    engine = internal_engine_cls.from_str(
                        file_content,
                        config=internal_engine_config,
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

        factory_defs = None if not defs else FactoryDefinitions(definitions=defs)
        if factory_defs and global_defs:
            factory_defs.extend(global_defs)

        factory_output = (
            None
            if not output
            else FactoryOutput(
                attributes=output,
                definitions=(None if not factory_defs else factory_defs.defined_types),
            )
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
                            file_content, config=internal_engine_config
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
            source=file_path,
            parsed_source=source,
            prompt=factory_prompt,
            output=factory_output,
            definitions=factory_defs,
            mask=factory_mask,
            link_type=link_type,
        )


@dataclass
class ChainFactory:
    """
    This type is the representation of multiple factories.
    """

    links: list[ChainFactoryLink]
    base_chain: Optional["ChainFactory"] = None
    definitions: FactoryDefinitions = FactoryDefinitions()
    internal_engine_cls: Any = None
    internal_engine_config: Any = None

    @classmethod
    def from_file(
        cls,
        file_path: str,
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
            internal_engine_cls=internal_engine_cls,
            internal_engine_config=internal_engine_config,
        )

    @classmethod
    def from_str(
        cls,
        content: str,
        path: str | None = None,
        internal_engine_cls: Any | None = None,
        internal_engine_config: Any | None = None,
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
                    ChainFactoryLink.from_file(
                        name="chainlink-0",
                        file_content=content,
                        file_path=path,
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

            if not chainlink_directive and current_part:
                parts[current_part]["lines"].append(line)
                continue

            if line.startswith("  "):
                line = line.replace("  ", "\t")

            tokens = [token for token in line.strip().split(" ")]

            if len(tokens) > 3:
                raise ValueError(
                    f"Error on line {i}. Invalid @chainlink definition. Must be of the form `@chainlink <name> <link_type>`."
                )
            elif len(tokens) == 3:
                name = tokens[1]
                link_type = tokens[2]

                if link_type not in ["sequential", "parallel", "--", "||"]:
                    raise ValueError(
                        f"Error on line {i}. Invalid @chainlink definition. Must be of the form `@chainlink [name] [link_type: 'sequential' | '--' | 'parallel' | '||']."
                    )

                if name in parts:
                    raise ValueError(
                        f"Error on line {i}. Invalid @chainlink definition. Another chainlink with the same name exists."
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
                "lines": [],
            }

        chainlinks = []
        previous_link = None
        global_defs = FactoryDefinitions()
        for name, part in parts.items():
            if not part["lines"]:
                raise ValueError(
                    f"Error on line {part['beginning_line']}. Chainlink definition cannot be empty."
                )

            if (
                previous_link
                and previous_link._link_type == "parallel"
                and part["link_type"] == "sequential"
            ):
                convex = True
            else:
                convex = False

            link = ChainFactoryLink.from_file(
                name=name,
                file_content="\n".join(part["lines"]).replace("\t", "  "),
                link_type=part["link_type"],
                convex=convex,
                global_defs=global_defs,
                internal_engine_cls=internal_engine_cls,
                internal_engine_config=internal_engine_config,
            )

            if previous_link and previous_link._link_type == "parallel":
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
