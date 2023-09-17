
class Player(list):
    def __init__(self, name: str, cards: list = None) -> None:
        super().__init__(cards or [])
        self.name: str = name

    def __repr__(self) -> str:
        return f"Player {self.name} with {len(self)} cards : {', '.join(map(str, self))}"

    def append(self, card: object) -> None:
        card.player = self
        super().append(card)

    def extend(self, __iterable: object) -> None:
        for card in __iterable:
            card.player = self
        return super().extend(__iterable)