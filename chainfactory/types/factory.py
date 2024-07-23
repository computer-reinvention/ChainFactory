"""
This module defines the core `Factory` type representation.
"""

import uuid
import yaml
from typing import Any, Optional
from dataclasses import dataclass
from typing import Any, Optional, Literal
import importlib.resources as pkg_resources

from .components import (
    FactoryDefinitions,
    FactoryPrompt,
    FactoryOutput,
    FactoryInput,
)


class ChainFactoryLink:
    """
    This type is the representation of a factory.
    """

    _name: str
    _source: Optional[str]
    _parsed_source: Optional[Any]
    _link_type: Literal["sequential", "parallel"] = "sequential"

    # 1:1 correspondence with the .fctr file sections
    definitions: Optional[FactoryDefinitions]
    output: Optional[FactoryOutput]
    prompt: Optional[FactoryPrompt]

    def __init__(
        self,
        name: str,
        source: Optional[str] = None,
        parsed_source: Optional[Any] = None,
        definitions: Optional[FactoryDefinitions] = None,
        output: Optional[FactoryOutput] = None,
        prompt: Optional[FactoryPrompt] = None,
        link_type: Literal["sequential", "parallel"] = "sequential",
    ):
        self._name = name
        self._source = source  # the YAML template
        self._parsed_source = parsed_source  # the parsed YAML object / dictionary

        # 1:1 correspondence with the .fctr file sections
        self.definitions: Optional[FactoryDefinitions] = definitions  # section `def`
        self.prompt: Optional[FactoryPrompt] = prompt  # section `prompt`
        self.output: Optional[FactoryOutput] = output  # section `out`
        self._link_type = link_type

    @classmethod
    def from_file(
        cls,
        name: str,
        file_path: str | None = None,
        file_content: str | None = None,
        link_type: Literal["sequential", "parallel"] = "sequential",
        engine_cls: Any | None = None,
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

        factory_input = None if not input else FactoryInput(attributes=input)
        input_variables = None if not factory_input else factory_input.input_variables

        if purpose:
            if engine_cls is None:
                raise ValueError(
                    "engine_cls must be provided for generating prompt template from purpose."
                )

            with pkg_resources.open_text(
                "chainfactory.chains", "generate_prompt_template.fctr"
            ) as file:
                file_content = file.read()

                engine = engine_cls.from_str(file_content)

                generated_prompt_template = engine(
                    purpose=purpose,
                    input_variables=input_variables,
                ).prompt_template

                print("============== GENERATED PROMPT ==============")
                print(generated_prompt_template)
                print("==============================================")

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
        factory_output = (
            None
            if not output
            else FactoryOutput(
                attributes=output,
                definitions=None if not factory_defs else factory_defs.defined_types,
            )
        )

        return cls(
            name=name,
            source=file_path,
            parsed_source=source,
            prompt=factory_prompt,
            output=factory_output,
            definitions=factory_defs,
            link_type=link_type,
        )


@dataclass
class ChainFactory:
    """
    This type is the representation of multiple factories.
    """

    links: list[ChainFactoryLink]

    @classmethod
    def from_file(cls, file_path: str, engine_cls: Any | None = None) -> "ChainFactory":
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

        return cls.from_str(content, engine_cls=engine_cls)

    @classmethod
    def from_str(cls, content: str, engine_cls: Any | None = None) -> "ChainFactory":
        """
        Parse the content of a .fctr file into a `ChainFactory` object.

        Args:
            content (str): The content of the .fctr file.
            engine_cls (Any): The engine class to generate the prompt template from purpose.

        Returns:
            Factory: The parsed `ChainFactory` object.
        """
        lines = content.splitlines()
        parts = {}
        current_part = None

        if "@chainlink" not in content:
            return cls(
                links=[
                    ChainFactoryLink.from_file(
                        name="chainlink-0", file_content=content
                    ),
                ]
            )

        for i, line in enumerate(lines):
            if not line:
                continue

            if line.startswith("#"):
                continue

            new_portion_start = line.strip().startswith("@chainlink")

            if not new_portion_start and current_part:
                parts[current_part]["lines"].append(line)
                continue

            if line.startswith("  "):
                line = line.replace("  ", "\t")

            tokens = [token for token in line.strip().split(" ")]

            print(tokens)

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

        for name, part in parts.items():
            if not part["lines"]:
                raise ValueError(
                    f"Error on line {part['beginning_line']}. Chainlink definition cannot be empty."
                )

            print(f"Processing {part['link_type']} chainlink: {name}")

            chainlinks.append(
                ChainFactoryLink.from_file(
                    name=name,
                    file_content="\n".join(part["lines"]).replace("\t", "  "),
                    link_type=part["link_type"],
                    engine_cls=engine_cls,
                )
            )

        return cls(links=chainlinks)
