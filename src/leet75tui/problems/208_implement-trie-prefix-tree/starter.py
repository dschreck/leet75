class Trie:
    def __init__(self) -> None:
        # TODO: initialise state
        pass

    def insert(self, word: str) -> None:
        raise NotImplementedError("Trie.insert")

    def search(self, word: str) -> bool:
        raise NotImplementedError("Trie.search")

    def startsWith(self, prefix: str) -> bool:
        raise NotImplementedError("Trie.startsWith")
