import time
import random
import win32api
import win32con
import pywintypes
from functools import partial


class Platform:
    size = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    available = [
        [800, 600],
        [832, 624],
        [1024, 768],
        [1152, 864],
        [1152, 872],
        [1176, 664],
        [1280, 720],
        [1280, 800],
        [1280, 960],
        [1280, 1024],
        [1366, 768],
        [1400, 1050],
        [1440, 900],
        [1600, 900],
        [1600, 1024],
        [1600, 1200],
        [1680, 1050],
        [1920, 1080],
        [1920, 1200],
        [2048, 1080],
        [1920, 1440],
        [2560, 1440],
    ]

    @staticmethod
    def on_set_resolution(width: int, height: int):
        devmode = pywintypes.DEVMODEType()
        devmode.PelsWidth = width
        devmode.PelsHeight = height
        devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
        res = win32api.ChangeDisplaySettings(devmode, 0)
        if res != win32con.DISP_CHANGE_SUCCESSFUL:
            return False
        return True

    @staticmethod
    def P1440():
        Platform.on_set_resolution(2560, 1440)

    @staticmethod
    def P1080():
        Platform.on_set_resolution(1920, 1080)

    @staticmethod
    def P720():
        Platform.on_set_resolution(1280, 720)

    @staticmethod
    def min():
        for width, height in Platform.available:
            if Platform.on_set_resolution(width, height):
                return

    @staticmethod
    def max():
        for width, height in reversed(Platform.available):
            if Platform.on_set_resolution(width, height):
                return

    @staticmethod
    def random():
        width, height = random.choice(Platform.available)
        Platform.on_set_resolution(width, height)

    @staticmethod
    def map():
        for width, height in Platform.available:
            if Platform.on_set_resolution(width, height):
                time.sleep(1)


if __name__ == "__main__":
    # Platform.map()
    Platform.min()

    time.sleep(5)
    Platform.max()
    # Platform.P1440()
