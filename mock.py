from src.types.factory import Factory
from src.interfaces.engine import ChainFactoryEngine


if __name__ == "__main__":
    factory = Factory.from_file("test.yaml")
    engine = ChainFactoryEngine(factory)

    print("===========================")
    print(
        engine(
            {
                "input": "Hello world!",
                "name": "Steve Jobs",
            }
        ).content
    )
    print("===========================")
