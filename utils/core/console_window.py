

from subprocess import Popen
from typing import Optional


class ConsoleWindow:
    def __init__(self, process: Optional[Popen[bytes]] = None) -> None:
        self.process: Optional[Popen[bytes]] = process
