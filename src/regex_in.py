from dataclasses import dataclass
import re

@dataclass
class regex_in:
    string: str
    match: re.Match = None

    def __eq__(self, other: str | re.Pattern):
        """
        Overload the == operator

        :param other: The string or regex to compare

        :return: True if the string match the regex
        """
        if isinstance(other, str):
            other = re.compile(other)
        assert isinstance(other, re.Pattern)
        self.match = other.fullmatch(self.string)
        return self.match is not None

    def __getitem__(self, group):
        """
        Overload the [] operator

        :param group: The group to get

        :return: The group of the regex
        """
        return self.match[group]
