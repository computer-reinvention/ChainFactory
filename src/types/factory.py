"""
This module defines the core `Factory` type representation.
"""

import yaml
from typing import Any, Optional
from .components import FactoryDefinitions, FactoryPrompt, FactoryOutput, FactoryInput


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

        # extends = source.get("extends")
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

        # factory_extends = None if not extends else Factory(source=extends)
        factory_input = None if not input else FactoryInput(attributes=input)
        factory_prompt = (
            None
            if not prompt
            else FactoryPrompt(
                string=prompt.get("template"),
                purpose=prompt.get("purpose", purpose),
                input_variables=(
                    None if not factory_input else factory_input.input_variables
                ),
            )
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
            source=file_path,
            parsed_source=source,
            prompt=factory_prompt,
            output=factory_output,
            definitions=factory_defs,
        )
