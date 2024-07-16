"""
This module defines some of the core types used in the chain factory project.
"""

from typing import Any, Optional


class FactoryPrompt:
    """
    This type is the representation of an `prompt` section of a chain factory file.
    """

    pass


class FactoryInput:
    """
    This type is the representation of an `in` section of a chain factory file.
    """

    pass


class FactoryOutput:
    """
    This type is the representation of the `out` section of a chain factory file.
    """

    pass


class Factory:
    """
    This type is the representation of a factory.
    """

    _source: Optional[str]
    _parsed_source: Optional[Any]
    extends: Optional["Factory"]
    in_: Optional[FactoryInput]
    out: Optional[FactoryOutput]
    prompt: Optional[FactoryPrompt]
