"""
This module defines the core `Factory` type representation.
"""

import yaml
from typing import Any, Optional
from .components import FactoryDefinitions, FactoryPrompt, FactoryOutput


class Factory:
    """
    This type is the representation of a factory.
    """

    _source: Optional[str]
    _parsed_source: Optional[Any]

    # 1:1 correspondence with the .fctr file sections
    extends: Optional["Factory"]
    definitions: Optional[FactoryDefinitions]
    output: Optional[FactoryOutput]
    prompt: Optional[FactoryPrompt]

    def __init__(
        self,
        source: str,
        parsed_source: Optional[Any] = None,
        extends: Optional["Factory"] = None,
        definitions: Optional[FactoryDefinitions] = None,
        output: Optional[FactoryOutput] = None,
        prompt: Optional[FactoryPrompt] = None,
    ):
        self._source = source  # the YAML string
        self._parsed_source = parsed_source  # the parsed YAML object / dictionary

        # 1:1 correspondence with the .fctr file sections
        self.extends: Optional["Factory"] = extends  # section `extends`
        self.definitions: Optional[FactoryDefinitions] = definitions  # section `def`
        self.prompt: Optional[FactoryPrompt] = prompt  # section `prompt`
        self.output: Optional[FactoryOutput] = output  # section `out`

    @classmethod
    def from_file(cls, file_path: str) -> "Factory":
        """
        Parse the source file into a `Factory` object.
        Currently only supports the `prompt` and `out` sections. Definitions and extending are not supported. Neither is input and auto prompting.
        """
        source = yaml.safe_load(open(file_path, "r"))
        # ext = source.get("extends")
        # input = source.get("input")
        # defs = source.get("def")

        prompt = source["prompt"]

        if isinstance(prompt, str):
            prompt_template = prompt
        elif isinstance(prompt, dict):
            prompt_template = source["prompt"]["template"]
        else:
            raise ValueError("Invalid prompt format.")

        output = source.get("out")

        factory_prompt = FactoryPrompt(string=prompt_template)

        if output is None:
            factory_output = None
        else:
            factory_output = FactoryOutput(attributes=output)

        return cls(
            source=file_path,
            parsed_source=source,
            prompt=factory_prompt,
            output=factory_output,
        )
