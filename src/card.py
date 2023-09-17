from src.regex_in import regex_in
from src.player import Player

Cards = any

class Card:
    def __init__(self, color: str, value: str, app: "Cards") -> None:
        self.color: str = color
        for r in app.regex:
            if (res := regex_in(value)) == r:
                self.value: str = res[1]
                self.action: str = res[2]
                break
        else:
            self.action: None = None
        self.value: str = value
        self.app: Cards = app
        self.player: Player = None

    def ljust(self, width: int, fillchar: str = " ") -> str:
        return self.__repr__().ljust(width, fillchar)


    def __repr__(self) -> str:
        return f"{self.color} {self.value}"

    def __eq__(self, o: object) -> bool:
        """
        Overload the == operator

        :param o: The object to compare

        :return: True if the object is a Card and have the same color and value
        """
        if isinstance(o, Card):
            return self.color == o.color and self.value == o.value
        return False

    def __le__(self, other):
        """
        Overload the <= operator

        :param other: The object to compare

        :return: True if the object is a Card and have the same color or value
        """
        return ((self.color == other.color or self.value == other.value or other.is_wild) and self.player != other.player)(self.value == other.value and self.player == other.player)

    def __lt__(self, other):
        """
        Overload the < operator

        :param other: The object to compare
        """
        return self.value == other.value

    def __call__(self, player: str = None) -> "Card":
        self.player = player
        return self

    def __len__(self) -> int:
        return len(self.__repr__())

    @property
    def len(self) -> int:
        return len(self.__repr__())

    @property
    def is_special(self) -> bool:
        return self.value in self.app.deck["sp_counter"] or self.value in self.app.deck["sp_no_counter"]

    @property
    def is_counter(self) -> bool:
        return self.value in self.app.deck["sp_counter"]

    @property
    def is_no_counter(self) -> bool:
        return self.value in self.app.deck["sp_no_counter"]

    @property
    def is_wild(self) -> bool:
        return self.color == "wild"