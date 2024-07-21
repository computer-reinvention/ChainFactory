from pprint import pprint
from typing import Any, Literal
from dataclasses import dataclass, field

from langchain_core.runnables import RunnableSerializable

from chainfactory.types.factory import Factory

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


@dataclass
class ChainFactoryEngineConfig:
    """
    Configuration for the ChainFactoryEngine.
    """

    model: str = "gpt-4o"
    temperature: float = 0
    provider: Literal["openai", "anthropic"] = "openai"
    max_tokens: int = 1024
    model_kwargs: dict = field(default_factory=dict)


class ChainFactoryEngine:
    def __init__(
        self,
        factory: Factory,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ):
        self.factory = factory
        self.config = config
        self.chain = self._create_chain(factory, config)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Call the chain with the given arguments.
        """
        if len(args) > 1:
            raise ValueError(
                "ChainFactoryEngine() only supports one positional argument."
            )
        elif len(args) == 1:
            return self.chain.invoke(args[0])
        else:
            if len(kwargs) == 0:
                raise ValueError(
                    "ChainFactoryEngine() requires at least one keyword argument or one positional argument."
                )

            return self.chain.invoke(kwargs)

    def _create_chain(
        self,
        factory: Factory,
        config: ChainFactoryEngineConfig,
    ) -> RunnableSerializable:
        """
        Create a chain from the factory.
        """
        match config.provider:
            case "openai":
                llm = ChatOpenAI(
                    temperature=config.temperature,
                    model=config.model,
                    model_kwargs=config.model_kwargs,
                )
            case "anthropic":
                llm = ChatAnthropic(
                    temperature=config.temperature,
                    model_name=config.model,
                    **config.model_kwargs,
                )
            case _:
                raise ValueError(f"Invalid provider: {config.provider}")

        if factory.output is None:
            model = llm
        else:
            model = llm.with_structured_output(factory.output._type)

        prompt = ChatPromptTemplate.from_template(factory.prompt.template)

        return prompt | model

    @classmethod
    def from_file(
        cls,
        file_path: str | None = None,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ) -> "ChainFactoryEngine":
        """
        Create a ChainFactoryEngine from a file.
        """
        factory = Factory.from_file(file_path, engine_cls=cls)

        return cls(factory, config)

    @classmethod
    def from_str(
        cls,
        fctr_str: str | None = None,
        config: ChainFactoryEngineConfig = ChainFactoryEngineConfig(),
    ) -> "ChainFactoryEngine":
        """
        Create a ChainFactoryEngine from a file.
        """
        factory = Factory.from_file(file_content=fctr_str, engine_cls=cls)

        return cls(factory, config)
