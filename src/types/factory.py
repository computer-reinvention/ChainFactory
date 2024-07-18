"""
This module defines the core `Factory` type representation.
"""

from typing import Any, Optional
from .components import FactoryDefinitions, FactoryPrompt, FactoryOutput


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

    def __init__(self, source: str):
        self._source = source  # the YAML string
        self._parsed_source = None  # the parsed YAML object / dictionary

        # 1:1 correspondence with the .fctr file sections
        self.extends: Optional["Factory"] = None  # section `extends`
        self.definitions: Optional[FactoryDefinitions] = None  # section `def`
        self.prompt: Optional[FactoryPrompt] = None  # section `prompt`

    @classmethod
    def from_file(cls, file_path: str) -> "Factory":
        """
        Parse the source file into a `Factory` object.
        """
        raise NotImplementedError
