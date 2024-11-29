from typing import Any, Literal, Optional


def create_class_from_dict(
    class_name: str,
    attributes: dict,
    base_class=object,
    defined_types: dict[str, type] | None = None,
    default_value_class: type | None = None,
):
    """
    Dynamically create a class from a dictionary of attributes and their types.

    Args:
        class_name (str): The name of the class to be created.
        attributes (dict): A dictionary of attributes and their strings for their types.
        base_class (type): The base class for the dynamically created class. Defaults to object.
        defined_types (dict): A dictionary of attribute types that are predefined. Defaults to {}.

    Returns:
        type: The dynamically created class.
    """
    local_types = {
        "Any": Any,
        "Literal": Literal,
        "Optional": Optional,
        "list": list,
        "dict": dict,
    }
    class_dict = {"__annotations__": {}}

    if not defined_types:
        defined_types = {}

    description = None
    default_value = None

    for attr, attr_type in attributes.items():
        if "%" in attr_type:
            parts = [part.strip() for part in attr_type.split("%")]
            if len(parts) > 2:
                raise ValueError(
                    "Invalid attribute definition % can only be used once."
                )
            attr_type = parts[0]
            description = parts[1]

            if "=" in description:
                parts = [part.strip() for part in description.split("=")]
                description = parts[0]
                default_value = parts[1]

        if "=" in attr_type:
            parts = [part.strip() for part in attr_type.split("=")]

            if len(parts) > 2:
                raise ValueError(
                    "Invalid attribute definition = can only be used once."
                )

            attr_type = parts[0]
            default_value = parts[1]

        if attr_type.endswith("?"):
            actual_type_str = attr_type[:-1]
            actual_type = defined_types.get(actual_type_str)
            if actual_type is None:
                actual_type = Optional[eval(actual_type_str, local_types)]
        elif attr_type.startswith("list[") and attr_type.endswith("]"):
            element_type_str = attr_type[5:-1]
            element_type = defined_types.get(element_type_str)
            if element_type is None:
                element_type = eval(element_type_str, local_types)
            actual_type = list[element_type]
        else:
            actual_type = defined_types.get(attr_type)
            if actual_type is None:
                actual_type = eval(attr_type, local_types)

        class_dict["__annotations__"][attr] = actual_type

        if default_value_class:
            if description and default_value is not None:
                class_dict[attr] = default_value_class(
                    default=default_value,
                    description=description,
                )
            elif default_value is not None:
                class_dict[attr] = default_value_class(default=default_value)
            elif description:
                class_dict[attr] = default_value_class(description=description)

    return type(class_name, (base_class,), class_dict)
