"""
This module defines the core `Factory` type representation.
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

    # 1:1 correspondence with the .fctr file sections
    extends: Optional["Factory"]
    definitions: Optional[FactoryDefinitions]
    input: Optional[FactoryInput]
    output: Optional[FactoryOutput]
    prompt: Optional[FactoryPrompt]
