class Pile:
    def __init__(self, items: list = None) -> None:
        self.items = items or []

    def get(self) -> object:
        return self.items[-1]

    def add(self, item: any):
        self.items.append(item)

    def remove(self):
        return self.items.pop()

    def len(self):
        return len(self.items)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)
