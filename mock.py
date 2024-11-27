from pprint import pprint
from chainfactory import Engine
from chainfactory.core.engine.chainfactory_engine import ChainFactoryEngineConfig
from langchain.globals import set_debug, set_verbose

set_debug(False)
set_verbose(False)


def tool_use(topic="Python", num=3):
    config = ChainFactoryEngineConfig(
        print_trace=True,
        pause_between_executions=True,
    )
    engine = Engine.from_file("examples/haiku.fctr", config=config)
    res = engine(topic=topic, num=num)

    print("==================")
    pprint(res)
    print("==================")


if __name__ == "__main__":
    tool_use()
