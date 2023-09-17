from threading import Thread
from typing import Generator
import wmi, time, pythoncom



def loop() -> Generator[int, None, None]:
    while True:
        for i in range(100):
            yield i
        for i in range(100, 0, -1):
            yield i


def brightness(level: int) -> None:
    pythoncom.CoInitialize()
    c: wmi.WMI = wmi.WMI(namespace="wmi")
    methods: wmi.WmiMonitorBrightnessMethods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(level, 0)


def roll(durations: int) -> None:
    ctime, it = time.time(), loop()
    while time.time() - ctime < durations:
        brightness(next(it))


def run(durations: int) -> None:
    Thread(target=roll, args=(durations,)).start()


if __name__ == "__main__":
    run(10)
