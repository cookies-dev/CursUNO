def merge(a, b, c):
    c = {}
    for k in set(list(a.keys()) + list(b.keys()) + list(c.keys())):
        c[k] = a.get(k, []) + b.get(k, []) + c.get(k, [])
    return c


import keyboard, time, os


def select_data(data: list[dict] | list[object], dkey: str = "name") -> dict:
    if not isinstance(data[0], dict):
        data = [{dkey: x} for x in data]

    terminal_size = os.get_terminal_size()
    selected_index = 0
    size_max = max([len(dt[dkey]) for dt in data])
    size_max += len(str(len(data))) + 4
    columns: int = min(len(data) // 3, terminal_size.columns // (size_max + 2) + (terminal_size.columns % (size_max + 2) > 0))
    rows: int = len(data) // columns + 1
    table: list[list[dict[str:any]]] = []

    for i in range(0, rows):
        table.append(data[i::rows])
    rows, columns, lstr = len(table), len(table[0]), len(str(len(data)))

    while True:
        print(f"┌{'─' * ((size_max) * columns)}┐")
        for i in range(rows):
            print("│", end="")
            for j in range(columns):
                idx = rows * j + i
                if idx < len(data):
                    if selected_index == idx:
                        print(f"\033[7m{str(idx + 1).rjust(lstr)}. {data[idx][dkey].ljust(size_max - 4)}\033[0m", end="")
                    else:
                        print(f"{str(idx + 1).rjust(lstr)}. {data[idx][dkey].ljust(size_max - 4)}", end="")
                else:
                    print(" " * size_max, end="")
            print("│")
        print(f"└{'─' * ((size_max) * columns)}┘")

        while (key := keyboard.read_key()) == None or key not in ["up", "down", "haut", "bas", "enter"]:
            pass

        if key == "up" or key == "haut":
            selected_index = (selected_index - 1) % len(data)
        elif key == "down" or key == "bas":
            selected_index = (selected_index + 1) % len(data)
        elif key == "enter":
            return data[selected_index]
        time.sleep(0.15)
        print(f"\033[{rows + 2}A", end="")


if __name__ == "__main__":
    data = [
        {"name": "a"},
        {"name": "b"},
        {"name": "c"},
        {"name": "d"},
        {"name": "e"},
        {"name": "f"},
        {"name": "g"},
        {"name": "h"},
        {"name": "i"},
        {"name": "j"},
        {"name": "k"},
        {"name": "l"},
        {"name": "m"},
        {"name": "n"},
        {"name": "o"},
        {"name": "p"},
        {"name": "q"},
        {"name": "r"},
        {"name": "s"},
        {"name": "t"},
        {"name": "u"},
        {"name": "v"},
        {"name": "w"},
        {"name": "x"},
        {"name": "y"},
        {"name": "z"},
    ]
    print(select_data(data, "name"))
