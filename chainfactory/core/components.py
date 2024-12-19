import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from .parsing.class_from_dict import create_class_from_dict


class FactoryMask:
    """
    This type is the representation of the `mask` section of a chain factory file.
    """

    type: str
    variables: list[str] = []
    template: str | None = None

    def __init__(
        self,
        variables: list[str],
        template: str | None = None,
        type: Literal["auto", "template"] = "auto",
    ):
        if not template:
            raise ValueError("FactoryMask cannot be initialized without a template.")
        else:
            self.template = template

        if not variables:
            variables = self._extract_variables(template)

        if not variables:
            if template:
                raise ValueError("FactoryMask template does not contain any variables.")
            else:
                raise ValueError("FactoryMask cannot be initialized without variables.")

        for var in variables:
            original = var
            cleaned = var.replace(".", "$")
            self.variables.append(cleaned)
            self.template = self.template.replace(
                "{" + original + "}",
                "{" + cleaned + "}",
            )

    def render(self, variables: dict[str, Any]) -> str:
        """
        Render the mask template with the given variables.
        """
        assert self.template
        rendered = self.template

        for var, value in variables.items():
            rendered = rendered.replace("{" + var + "}", str(value))

        return rendered

    def _extract_variables(self, template: str) -> list[str]:
        """
        Extract input variables from the prompt template using regex.
        """
        pattern = r"\{([^}]+)\}"  # matches {variable_name}
        matches = re.findall(pattern, template)

        return matches


class FactoryDefinitions:
    """
    This type is the representation of the `def` section of a chain factory file. It contains defined types.
    """

    defined_types: dict[str, type] = {}
    definitions: dict[str, dict] = {}

    def __init__(
        self,
        definitions: dict[str, dict] | None = None,
        types: dict[str, type] | None = None,
    ):
        if types:
            self.defined_types = types

            if definitions:
                self.definitions = definitions

            return

        if not definitions:
            return

        self.definitions = definitions

        for name, definition in definitions.items():
            self.defined_types[name] = create_class_from_dict(
                class_name=name,
                attributes=definition,
                base_class=BaseModel,
                defined_types=self.defined_types,
                default_value_class=Field,
            )

    def extend(self, definitions: "FactoryDefinitions"):
        """
        Extend the factory definitions with the another FactoryDefinitions object.
        """
        self.defined_types.update(definitions.defined_types)
        self.definitions.update(definitions.definitions)


class FactoryInput:
    """
    This type is the representation of the `in` section of a chain factory file. It lists the input variables and their annotations.
    """

    attributes: dict
    aliases: dict[str, str] = {}

    def __init__(self, attributes: dict | list[str]):
        if isinstance(attributes, list):
            self.attributes = {k: Any for k in attributes}
            self.input_variables = attributes
        else:
            self.attributes = attributes
            self.input_variables = list(self.attributes.keys())

        dot_access_notation = lambda x: x.split(" as ")[0].strip()
        shorthand = lambda x: x.split(" as ")[1].strip()
        cleaned_input_variables = []
        for var in self.input_variables:
            if " as " in var:
                self.aliases[dot_access_notation(var)] = shorthand(var)
                cleaned_input_variables.append(dot_access_notation(var))
            else:
                cleaned_input_variables.append(var)

        self.input_variables = cleaned_input_variables


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
            raise ValueError("FactoryPrompt cannot be initialized without a template.")

        self.purpose = purpose
        self.template = template
        self.input_variables = []

        if not input_variables:
            input_variables = self._extract_input_variables(template)

        for var in input_variables:
            if "." in var:
                original = var
                cleaned = var.replace(".", "$")
                self.input_variables.append(cleaned)
                self.template = self.template.replace(
                    "{" + original + "}",
                    "{" + cleaned + "}",
                )
            else:
                self.input_variables.append(var)

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
