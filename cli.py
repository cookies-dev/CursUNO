from win10toast import ToastNotifier
import random, json, time

from src.card import Card
from src.pile import Pile
from src.regex_in import regex_in
from src.utils import merge, select_data
from src.player import Player


class Cards:
    __current_player: str = None
    __next_player: str = None
    __direction: int = 1
    __pile: Pile = Pile()

    def __init__(self) -> None:
        self.cards: list[Card] = []
        self.played: list[Card] = []
        self.players: dict[str:Player] = {}
        self.deck: dict[str : list[str]] = {}

        self.init_deck()

    def init_deck(self) -> None:
        try:
            config = json.load(open("deck.json"))
        except FileNotFoundError:
            print("deck.json not found")
            exit(1)
        except json.decoder.JSONDecodeError:
            print("deck.json is not a valid json file")
            exit(1)
        except Exception as e:
            print(e)
            exit(1)

        self.regex = config["regex"]
        deck = merge(config["template"], config["cards"], config["addons"])
        self.cards = []
        for color in deck["color"]:
            for value in deck["classic"]:
                self.cards.append(Card(color, value, self))
            for value in deck["sp_counter"]:
                self.cards.append(Card(color, value, self))
            for value in deck["sp_no_counter"]:
                self.cards.append(Card(color, value, self))
        for value in deck["wild"]:
            self.cards.append(Card("wild", value, self))
        self.deck = deck.copy()
        # shuffle the deck
        random.shuffle(self.cards)

    def init_players(self, players: list[str], nb_card: int) -> None:
        for player in players:
            self.players[player] = Player(player)
            [self.players[player].append(self.cards.pop(0)) for _ in range(nb_card)]
        self.order = list(self.players.keys())
        random.shuffle(self.order)
        self.current_player = self.order[0]

    def turn(self) -> None:
        finished = False
        while not finished:
            action = select_data([{"name": x} for x in ["pick", "play", "finish"]])['name']
            print(action)
            match action:
                case "pick":
                    self.pick_card()
                case "play":
                    self.play_card()
                case "finish":
                    pass
            time.sleep(5)

    def play_card(self) -> None:
        select_data(self.players[self.current_player])

    def play(self, player: str, card: Card) -> None:
        if player != self.current_player:
            raise ValueError("It's not your turn")
        if card not in self.players[player]:
            raise ValueError("You don't have this card")
        if not self.last_card <= card:
            raise ValueError("You can't play this card")
        if self.pile.len():
            if not self.last_card < card:
                raise ValueError("You can't play this card")

        self.played.append(card)
        self.players[player].remove(card)
        if self.last_card.is_counter:
            self.pile.add(self.last_card)
        if self.last_card.is_no_counter:
            self.n_special()

        # execute special card if needed
        # self.c_special()

    def n_special(self) -> None:
        match regex_in(self.last_card.value):
            case "^reverse$":
                self.direction *= -1
            case "^skip$":
                print(f"Player {self.next_player} is skipped")
                self.current_player = self.next_player

    def c_special(self) -> None:
        match regex_in(self.last_card.value):
            case "^draw$":
                print(f"Player {self.next_player} draw {self.last_card.action} cards")
                self.players[self.next_player].extend(self.cards[: int(self.last_card.action)])
                self.cards = self.cards[int(self.last_card.action) :]
                if self.last_card.color == "wild":
                    self.last_card.color = self.ask_color()
            case "^wild$":
                self.last_card.color = self.ask_color()

    def ask_color(self) -> str:
        print(" ".join(self.deck["color"]))
        color = input("Choose a color: ")
        while color not in self.deck["colors"]:
            color = input("Choose a color: ")
        return color

    def pick_card(self, player: str = None) -> None:
        if player is None:
            player = self.current_player
        self.players[player].append(self.cards.pop(0))
        ToastNotifier().show_toast("Cards", f"{player} pick a card: {self.players[player][-1]}", duration=1)

    @property
    def pile(self) -> Pile:
        return self.__pile

    @property
    def current_player(self) -> str:
        return self.__current_player

    @current_player.setter
    def current_player(self, player: str) -> None:
        self.__current_player = player

    @property
    def direction(self) -> int:
        return self.__direction

    @direction.setter
    def direction(self, direction: int) -> None:
        self.__direction = direction

    @property
    def get_next_player(self) -> str:
        return self.order[(self.order.index(self.__next_player if self.__next_player else self.current_player) + self.direction) % len(self.order)]

    @property
    def set_next_player(self) -> str:
        if not self.__next_player:
            self.__next_player = self.get_next_player
        return self.__next_player

    @property
    def change_player(self) -> None:
        self.current_player = self.__next_player or self.get_next_player
        self.__next_player = None
        return self.current_player

    @property
    def last_card(self) -> Card:
        return self.played[-1]


if __name__ == "__main__":
    cards = Cards()
    cards.init_players(["test 1", "test 2"], 7)
    cards.turn()
