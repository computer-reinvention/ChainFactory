import re
import pprint
from typing import Any

from langchain.pydantic_v1 import BaseModel
from langchain_core.pydantic_v1 import Field

from ..parsing.class_from_dict import create_class_from_dict


class FactoryDefinitions:
    """
    This type is the representation of the `def` section of a chain factory file.
    """

    defined_types: dict[str, type]
    definitions: dict[str, Any]

    def __init__(self, definitions: dict[str, dict]):
        self.defined_types = {}
        self.definitions = definitions

        for name, definition in definitions.items():
            self.defined_types[name] = create_class_from_dict(
                class_name=name,
                attributes=definition,
                base_class=BaseModel,
                defined_types=self.defined_types,
                default_value_class=Field,
            )


class FactoryInput:
    """
    This type is the representation of the `in` section of a chain factory file.
    """

    attributes: dict

    def __init__(self, attributes: dict):
        self.attributes = attributes
        self.input_variables = list(self.attributes.keys())


class FactoryPrompt:
    """
    This type is the representation of the `prompt` section of a chain factory file.
    """

    template: str | None = None
    purpose: str | None = None
    input_variables: list[str] | None = None

    def __init__(
        self,
        template: str,
        input_variables: list[str] | None = None,
        purpose: str | None = None,
    ):
        if not template:
            raise ValueError("Either template or input_variables must be provided.")

        self.template = template
        self.input_variables = self._extract_input_variables(template)

    def _extract_input_variables(self, template: str) -> list[str]:
        """
        Extract input variables from the prompt template using regex.
        """
        pattern = r"\{([^}]+)\}"  # matches {variable_name}
        matches = re.findall(pattern, template)

        return matches


class FactoryOutput:
    """
    This type is the representation of the `out` section of a chain factory file.
    """

    _type: type
    attributes: dict
    _NAME: str = "ChainFactoryOutput"

    def __init__(self, attributes: dict, definitions: dict[str, type] | None = None):
        """
        Initialize the output class.
        """
        self.attributes = attributes
        self._type = create_class_from_dict(
            class_name=self._NAME,
            attributes=attributes,
            base_class=BaseModel,
            defined_types=definitions,
            default_value_class=Field,
        )
        pprint.pprint(self._type.__annotations__)
