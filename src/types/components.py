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

    string: str
    input_variables: list[str]


class FactoryOutput:
    """
    This type is the representation of the `out` section of a chain factory file.
    """

    type_: type
    type_name: str
    source: dict
