import yaml
from pprint import pprint

from datetime import datetime
from typing import List, Optional

from langchain.pydantic_v1 import BaseModel


def create_class_from_dict(class_name: str, attributes: dict, base_class=object):
    """
    Dynamically create a class from a dictionary of attributes and their types.

    Args:
        class_name (str): The name of the class to be created.
        attributes (dict): A dictionary of attributes and their types.
    Returns:
        type: The dynamically created class.
    """
    class_dict = {"__annotations__": {}}
    for attr, attr_type in attributes.items():
        if attr_type.endswith("?"):
            actual_type = (
                eval(attr_type[:-1])
                if attr_type[:-1] in globals()
                else Optional[eval(attr_type[:-1])]
            )
        elif attr_type.startswith("list[") and attr_type.endswith("]"):
            element_type = attr_type[5:-1]
            actual_type = List[eval(element_type)]
        else:
            actual_type = eval(attr_type)

        class_dict["__annotations__"][attr] = actual_type

    return type(class_name, (base_class,), class_dict)


if __name__ == "__main__":
    with open("test.yaml", "r") as f:
        data = yaml.safe_load(f)
        pprint(data)

    GeneratedOutputClass = create_class_from_dict(
        "OutputClass", data["out"], base_class=BaseModel
    )

    pprint(GeneratedOutputClass.__annotations__)
