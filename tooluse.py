from time import sleep
from pprint import pprint

from chainfactory import Engine, EngineConfig


def important_fn(**kwargs):
    print("important_fn()")

    sleep(2)

    print("\n\n\n============================")
    pprint("Imagine something important happening here....")
    print("============================")

    sleep(2)

    pprint("Important things take time. Be patient.")
    print("============================")

    sleep(2)

    pprint("Just a bit more. Pinky promise!")
    print("============================")

    sleep(6)

    pprint("LOL. I was sleeping the whole time.")
    print("============================")

    sleep(2)

    print("\n\n\n============================")
    pprint("Bye! I will just return the input now. Fuck you.")
    print("============================")

    sleep(2)

    return {
        "greeting": "Hello World!",
        "echo": kwargs,
    }


def main(topic):
    """
    Demonstrates how to create a chain which can call a tool.
    """
    config = EngineConfig(pause_between_executions=True)
    config.register_tool(important_fn)

    haiku_engine = Engine.from_file("examples/tooluse.fctr", config=config)

    res = haiku_engine(topic=topic)

    return res


if __name__ == "__main__":
    res = main(topic="Star Wars")

    print("\n\n======= Final Output =======")
    pprint(res)
    print("============================")
