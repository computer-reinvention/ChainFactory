import argparse
from chainfactory import Engine, EngineConfig


def run_fctr_file(path: str, **kwargs):
    """
    Function to test while developing.
    """
    config = EngineConfig(
        pause_between_executions=False, print_trace=True
    )  # default provider: openai
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
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", help="The path to the .fctr file")
    parser.add_argument(
        "--kwargs", nargs="*", help="Keyword arguments to pass to the engine"
    )
    args = parser.parse_args()

    kwargs = {}
    if args.kwargs:
        for arg in args.kwargs:
            key, value = arg.split("=")
            kwargs[key] = value

    run_fctr_file(args.file_path, **kwargs)
