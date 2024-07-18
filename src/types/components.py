import re

from langchain.pydantic_v1 import BaseModel

from src.parsing.utils import create_class_from_dict


class FactoryDefinitions:
    """
    This type is the representation of the `def` section of a chain factory file.
    """

    types: dict[str, type]
    registered_types: list[str]


class FactoryPrompt:
    """
    This type is the representation of the `prompt` section of a chain factory file.
    """

    string: str | None = None
    purpose: str | None = None
    input_variables: list[str] | None = None

    def __init__(
        self,
        string: str | None = None,
        input_variables: list[str] | None = None,
        purpose: str | None = None,
    ):
        if not any([string, input_variables and purpose]):
            raise ValueError(
                "Either string or input_variables + purpose must be provided."
            )

        if string is None and input_variables is not None:
            if purpose is None:
                raise ValueError(
                    "purpose must be provided if input_variables is provided."
                )

            self.string = self._create_prompt_string(input_variables, purpose)
            self.input_variables = input_variables
            return

        if string is not None:
            self.string = string
            self.input_variables = self._extract_input_variables(string)

    def _extract_input_variables(self, string: str) -> list[str]:
        """
        Extract input variables from the prompt string using regex.
        """
        pattern = r"\{([^}]+)\}"  # matches {variable_name}
        matches = re.findall(pattern, string)

        return matches

    def _create_prompt_string(self, input_variables: list[str], purpose: str) -> str:
        """
        Create a prompt string from the input variables.
        """
        raise NotImplementedError


class FactoryOutput:
    """
    This type is the representation of the `out` section of a chain factory file.
    """

    _type: type
    attributes: dict
    _NAME: str = "ChainFactoryOutput"

    def __init__(self, attributes: dict):
        """
        Initialize the output class.
        """
        self.attributes = attributes
        self._type = create_class_from_dict(
            class_name=self.NAME,
            attributes=attributes,
            base_class=BaseModel,
        )
