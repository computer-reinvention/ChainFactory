from time import sleep
from chainfactory import Engine, EngineConfig


def run_fctr_file(path: str, **kwargs):
    """
    Function to test while developing.
    """
    config = EngineConfig(pause_between_executions=True)
    engine = Engine.from_file(path, config=config)
    res = engine(**kwargs)

    return res


if __name__ == "__main__":
    pass
