from typing import List, Optional


def create_class_from_dict(
    class_name: str,
    attributes: dict,
    base_class=object,
    defined_types: dict[str, type] | None = None,
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
    class_dict = {"__annotations__": {}}

    if not defined_types:
        defined_types = {}

    for attr, attr_type in attributes.items():
        if attr_type.endswith("?"):
            actual_type_str = attr_type[:-1]
            actual_type = defined_types.get(actual_type_str)
            if actual_type is None:
                actual_type = Optional[eval(actual_type_str)]
        elif attr_type.startswith("list[") and attr_type.endswith("]"):
            element_type_str = attr_type[5:-1]

            element_type = defined_types.get(element_type_str)
            if element_type is None:
                element_type = eval(element_type_str)

            actual_type = list[element_type]
        else:
            actual_type = defined_types.get(attr_type)
            if actual_type is None:
                actual_type = eval(attr_type)

        class_dict["__annotations__"][attr] = actual_type

    return type(class_name, (base_class,), class_dict)
