import os
import abc
import enum
import json
import shutil
import sqlite3
import inspect
import datetime
import tempfile
import platform
import tldextract
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from collections import defaultdict


class Platform(enum.Enum):
    OTHER = 0
    LINUX = 1
    MAC = 2
    WINDOWS = 3


def get_browsers():
    def get_subclasses(browser):
        sub_classes = []
        if not inspect.isabstract(browser):
            sub_classes.append(browser)
        for sub_class in browser.__subclasses__():
            sub_classes.extend(get_subclasses(sub_class))
        return sub_classes

    return get_subclasses(Browser)


def get_platform():
    system = platform.system()
    if system == "Linux":
        return Platform.LINUX
    if system == "Darwin":
        return Platform.MAC
    if system == "Windows":
        return Platform.WINDOWS
    raise NotImplementedError(f"Platform {system} is not supported yet")


def get_platform_name(plat: Optional[Platform] = None) -> str:
    if plat is None:
        plat = get_platform()
    if plat == Platform.LINUX:
        return "Linux"
    if plat == Platform.WINDOWS:
        return "Windows"
    if plat == Platform.MAC:
        return "MacOS"
    return "Unknown"


class Outputs:
    histories: list[tuple[datetime.datetime, str]]
    field_map: dict[str, dict[str, any]]
    format_map: dict[str, callable]

    def __init__(self, fetch_type):
        self.fetch_type = fetch_type
        self.histories = []
        self.field_map = {"history": {"var": self.histories, "fields": ("Timestamp", "URL")}, "domains": self.get_domains, "dns": self.get_dns}

    def get_dns(self) -> list[str] | None:
        if get_platform() == Platform.WINDOWS:
            output: str = subprocess.check_output("ipconfig /displaydns", shell=True)
            return [line.replace("Record Name . . . . . :", "").strip() for line in output.decode().splitlines() if "Record Name" in line]
        return None

    def sort_domain(self) -> dict[any, list[any]]:
        domain_histories: dict[any, list[any]] = defaultdict(list)
        for entry in self.field_map[self.fetch_type]["var"]:
            domain_histories[urlparse(entry[1]).netloc].append(entry)
        return domain_histories

    def get_domains(self) -> list[str]:
        domains: list[str] = [tldextract.extract(url).domain for (_, url) in self.histories if url]
        return sorted(list(set([(d, domains.count(d)) for d in domains if d])), key=lambda x: x[1], reverse=True)

    def to_json(self) -> str:
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, (datetime.date, datetime.datetime)):
                    return o.isoformat()
                return super().default(o)

        lines = []
        for entry in self.field_map[self.fetch_type]["var"]:
            json_record = {}
            for field, value in zip(self.field_map[self.fetch_type]["fields"], entry):
                json_record[field] = value
            lines.append(json_record)
        return json.dumps({self.fetch_type: lines, "domains": self.field_map["domains"](), "dns": self.field_map["dns"]()}, cls=DateTimeEncoder, indent=4)

    def save(self, filename: str):
        with open(filename, "w") as out_file:
            out_file.write(self.to_json())


class Browser(abc.ABC):
    windows_path: Optional[str] = None
    mac_path: Optional[str] = None
    linux_path: Optional[str] = None
    _local_tz: Optional[datetime.tzinfo] = datetime.datetime.now().astimezone().tzinfo
    history_dir: Path
    aliases: tuple = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """A name for the browser. Not used anywhere except for logging and errors."""

    def __init__(self, plat: Optional[Platform] = None):
        self.profile_dir_prefixes = []
        if plat is None:
            plat = get_platform()
        homedir = Path.home()

        error_string = f"{self.name} browser is not supported on {get_platform_name(plat)}"
        if plat == Platform.WINDOWS:
            assert self.windows_path is not None, error_string
            self.history_dir = homedir / self.windows_path
        elif plat == Platform.MAC:
            assert self.mac_path is not None, error_string
            self.history_dir = homedir / self.mac_path
        elif plat == Platform.LINUX:
            assert self.linux_path is not None, error_string
            self.history_dir = homedir / self.linux_path
        else:
            raise NotImplementedError()

        if self.profile_support and not self.profile_dir_prefixes:
            self.profile_dir_prefixes.append("*")

    def profiles(self, profile_file) -> list[str]:
        if not os.path.exists(self.history_dir):
            return []
        if not self.profile_support:
            return ["."]
        profile_dirs = []
        for files in os.walk(str(self.history_dir)):
            for item in files[2]:
                if os.path.split(os.path.join(files[0], item))[-1] == profile_file:
                    path = str(files[0]).split(str(self.history_dir), maxsplit=1)[-1]
                    if path.startswith(os.sep):
                        path = path[1:]
                    if path.endswith(os.sep):
                        path = path[:-1]
                    profile_dirs.append(path)
        return profile_dirs

    def history_path_profile(self, profile_dir: Path) -> Optional[Path]:
        if self.history_file is None:
            return None
        return self.history_dir / profile_dir / self.history_file

    def paths(self, profile_file):
        return [self.history_dir / profile_dir / profile_file for profile_dir in self.profiles(profile_file=profile_file)]

    def history_profiles(self, profile_dirs):
        history_paths = [self.history_path_profile(profile_dir) for profile_dir in profile_dirs]
        return self.fetch_history(history_paths)

    def fetch_history(self, history_paths=None, sort=True, desc=False):
        if history_paths is None:
            history_paths = self.paths(profile_file=self.history_file)
        output_object = Outputs(fetch_type="history")
        with tempfile.TemporaryDirectory() as tmpdirname:
            for history_path in history_paths:
                copied_history_path = shutil.copy2(history_path.absolute(), tmpdirname)
                conn = sqlite3.connect(f"file:{copied_history_path}?mode=ro&immutable=1&nolock=1", uri=True)
                cursor = conn.cursor()
                cursor.execute(self.history_SQL)
                date_histories = [(datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self._local_tz), url) for d, url in cursor.fetchall()]
                output_object.histories.extend(date_histories)
                if sort:
                    output_object.histories.sort(reverse=desc)
                conn.close()
        return output_object

    @classmethod
    def is_supported(cls):
        support_check = {Platform.LINUX: cls.linux_path, Platform.WINDOWS: cls.windows_path, Platform.MAC: cls.mac_path}
        return support_check.get(get_platform()) is not None


class ChromiumBasedBrowser(Browser, abc.ABC):
    history_file = "History"
    history_SQL = """SELECT datetime(visits.visit_time/1000000-11644473600, 'unixepoch', 'localtime') as 'visit_time', urls.url FROM visits INNER JOIN urls ON visits.url = urls.id WHERE visits.visit_duration > 0 ORDER BY visit_time DESC"""


class Chromium(ChromiumBasedBrowser):
    name = "Chromium"
    aliases = ("chromiumhtm", "chromium-browser", "chromiumhtml")
    linux_path = ".config/chromium"
    windows_path = "AppData/Local/chromium/User Data"
    profile_support = True


class Chrome(ChromiumBasedBrowser):
    name = "Chrome"
    aliases = ("chromehtml", "google-chrome", "chromehtm")
    linux_path = ".config/google-chrome"
    windows_path = "AppData/Local/Google/Chrome/User Data"
    mac_path = "Library/Application Support/Google/Chrome/"
    profile_support = True


class Firefox(Browser):
    name = "Firefox"
    aliases = ("firefoxurl",)
    linux_path = ".mozilla/firefox"
    windows_path = "AppData/Roaming/Mozilla/Firefox/Profiles"
    mac_path = "Library/Application Support/Firefox/Profiles/"
    history_file = "places.sqlite"
    history_SQL = """SELECT datetime(visit_date/1000000, 'unixepoch', 'localtime' ) AS 'visit_time', url FROM moz_historyvisits INNER JOIN moz_places ON moz_historyvisits.place_id = moz_places.id WHERE visit_date IS NOT NULL AND url LIKE 'http%' AND title IS NOT NULL"""
    profile_support = True


class LibreWolf(Firefox):
    name = "LibreWolf"
    aliases = ("librewolfurl",)
    linux_path = ".librewolf"


class Safari(Browser):
    name = "Safari"
    mac_path = "Library/Safari"
    history_file = "History.db"
    history_SQL = """SELECT datetime(visit_time + 978307200, 'unixepoch', 'localtime' ) as visit_time, url FROM history_visits INNER JOIN history_items ON history_items.id = history_visits.history_item ORDER BY visit_time DESC"""


class Edge(ChromiumBasedBrowser):
    name = "Edge"
    aliases = ("msedgehtm", "msedge", "microsoft-edge", "microsoft-edge-dev")
    linux_path = ".config/microsoft-edge-dev"
    windows_path = "AppData/Local/Microsoft/Edge/User Data"
    mac_path = "Library/Application Support/Microsoft Edge"
    profile_support = True


class Opera(ChromiumBasedBrowser):
    name = "Opera"
    aliases = ("operastable", "opera-stable")
    linux_path = ".config/opera"
    windows_path = "AppData/Roaming/Opera Software/Opera Stable"
    mac_path = "Library/Application Support/com.operasoftware.Opera"
    profile_support = False


class OperaGX(ChromiumBasedBrowser):
    name = "OperaGX"
    aliases = ("operagxstable", "operagx-stable")
    windows_path = "AppData/Roaming/Opera Software/Opera GX Stable"
    profile_support = False


class Brave(ChromiumBasedBrowser):
    name = "Brave"
    aliases = ("bravehtml",)
    linux_path = ".config/BraveSoftware/Brave-Browser"
    mac_path = "Library/Application Support/BraveSoftware/Brave-Browser"
    windows_path = "AppData/Local/BraveSoftware/Brave-Browser/User Data"
    profile_support = True


class Vivaldi(ChromiumBasedBrowser):
    name = "Vivaldi"
    aliases = ("vivaldi-stable", "vivaldistable")
    linux_path = ".config/vivaldi"
    mac_path = "Library/Application Support/Vivaldi"
    windows_path = "AppData/Local/Vivaldi/User Data"
    profile_support = True


def get_history():
    output_object = Outputs(fetch_type="history")
    browser_classes = get_browsers()
    for browser_class in browser_classes:
        try:
            browser_object = browser_class()
            browser_output_object = browser_object.fetch_history()
            output_object.histories.extend(browser_output_object.histories)
        except AssertionError:
            pass
    output_object.histories.sort()
    return output_object


if __name__ == "__main__":
    outputs = get_history()

    # save to file
    # outputs.save("history.json")

    # print to console
    # print(outputs.to_json())

    # print to console domain only
    # print(list(filter(lambda x: "por" in x[0], outputs.get_domains())))
