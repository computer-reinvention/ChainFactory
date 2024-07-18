from src.types.factory import Factory


class ChainFactoryEngine:
    def __init__(self, factory: Factory):
        self.factory = factory

    def create_chain(self):
        raise NotImplementedError
