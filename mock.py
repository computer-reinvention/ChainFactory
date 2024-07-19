import pendulum
from pprint import pprint
from src.types.factory import Factory
from src.interfaces.engine import ChainFactoryEngine


if __name__ == "__main__":
    haiku_engine = ChainFactoryEngine.from_file("chains/haiku.fctr")

    res = haiku_engine({"topic": "Python", "num": 3})
    # res = haiku_engine(topic="LSD", num=2)

    for haiku in res.haikus:
        print(haiku.haiku)
        print(haiku.explanation)
        print("\n")
