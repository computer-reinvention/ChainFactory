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
        self._source = source  # the YAML template
        self._parsed_source = parsed_source  # the parsed YAML object / dictionary

        # 1:1 correspondence with the .fctr file sections
        self.extends: Optional["Factory"] = extends  # section `extends`
        self.definitions: Optional[FactoryDefinitions] = definitions  # section `def`
        self.prompt: Optional[FactoryPrompt] = prompt  # section `prompt`
        self.output: Optional[FactoryOutput] = output  # section `out`

    @classmethod
    def from_file(cls, file_path: str, engine_cls: Any | None = None) -> "Factory":
        """
        Parse the source .fctr file into a `Factory` object.
        Extensions are not supported yet.

        Args:
            file_path (str): The path to the .fctr file.
        Returns:
            Factory: The parsed `Factory` object.
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

        if prompt and not purpose:
            purpose = prompt.get("purpose")

        if not prompt and not purpose:
            raise ValueError("Neither purpose nor a prompt template were provided.")

        # factory_extends = None if not extends else Factory(source=extends)
        factory_input = None if not input else FactoryInput(attributes=input)
        input_variables = None if not factory_input else factory_input.input_variables

        if purpose:
            if engine_cls is None:
                raise ValueError(
                    "engine_cls must be provided for generating prompt template from purpose."
                )

            engine = engine_cls.from_file(
                "chainfactory/chains/generate_prompt_template.fctr"
            )

            generated_prompt_template = engine(
                purpose=purpose,
                input_variables=input_variables,
            ).prompt_template

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
            source=file_path,
            parsed_source=source,
            prompt=factory_prompt,
            output=factory_output,
            definitions=factory_defs,
        )
