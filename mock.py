from chainfactory import Engine
from langchain.globals import set_debug, set_verbose

set_debug(True)
set_verbose(True)

if __name__ == "__main__":
    haiku_engine = Engine.from_file("examples/haiku.fctr")
    res = haiku_engine(topic="Python", num=4)

    for haiku in res.haikus:
        print("Topic:")
        print(haiku.topic)
        print("Haiku:")
        print(haiku.haiku)
        print("Explanation:")
        print(haiku.explanation)
        print("\n")
