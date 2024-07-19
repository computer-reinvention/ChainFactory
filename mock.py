from chainfactory.interfaces.engine import ChainFactoryEngine

if __name__ == "__main__":
    haiku_engine = ChainFactoryEngine.from_file("examples/haiku.fctr")
    res = haiku_engine(topic="Language Models", num=3)

    for haiku in res.haikus:
        print("Haiku:")
        print(haiku.haiku)
        print("Explanation:")
        print(haiku.explanation)
        print("\n")
