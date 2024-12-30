from chainfactory import Engine, EngineConfig


def run_fctr_file(path: str, **kwargs):
    """
    Function to test while developing.
    """
    config = EngineConfig(pause_between_executions=True)  # default provider: openai
    # config = ChainFactoryEngineConfig(pause_between_executions=True, provider="anthropic")
    # config = ChainFactoryEngineConfig(
    #     pause_between_executions=True,
    #     model="llama3.2:1b",
    #     provider="ollama",
    # )
    engine = Engine.from_file(path, config=config)
    res = engine(**kwargs)

    return res


if __name__ == "__main__":
    pass
