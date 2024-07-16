"""
This module defines some of the core Factory type representation.
"""

from typing import Any, Optional
from .components import (
    FactoryDefinitions,
    FactoryPrompt,
    FactoryInput,
    FactoryOutput,
)


class Factory:
    """
    This type is the representation of a factory.
    """

    _source: Optional[str]
    _parsed_source: Optional[Any]

    # Parts of the .fctr file
    extends: Optional["Factory"]
    definitions: Optional[FactoryDefinitions]
    input: Optional[FactoryInput]
    output: Optional[FactoryOutput]
    prompt: Optional[FactoryPrompt]
