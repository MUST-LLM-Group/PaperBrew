import asyncio

import psutil
from rich.console import Group
from rich.text import Text
from textual._time import time
from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.reactive import reactive
from textual.renderables.gradient import LinearGradient
from textual.widget import Widget
from textual.widgets import Static

from braille_stream import BrailleStream


class CPU(Widget):

    def __init__(self):
        super().__init__()
        self.os_type = self._get_os_type()
        self.cpu_arch = self._get_cpu_arch()
        self.hostname = self._get_hostname()
        self.python_version = self._get_python_version()
        self.env_hf_endpoint = self._get_env_hf_endpoint()
        self.env_hf_home = self._get_env_hf_home()

        self.group = Group("")
        self.braille_stream = BrailleStream(40, 12, 0.0, 100.0)

        # asyncio run get_cpu_usage in background
        asyncio.create_task(self.get_cpu_usage(1))



    def _get_cpu_arch(self) -> str:
        import platform
        return platform.machine()

    def _get_env_hf_home(self) -> str:
        import os
        return os.getenv("HF_HOME")

    def _get_env_hf_endpoint(self) -> str:
        import os
        return os.getenv("HF_ENDPOINT")

    def _get_python_version(self) -> str:
        import sys
        return sys.version.split()[0]

    def _get_hostname(self) -> str:
        import socket
        return socket.gethostname()

    def _get_os_type(self) -> str:
        import platform
        return platform.system().lower()

    async def get_cpu_usage(self, interval):
        while True:
            cpu_usage = psutil.cpu_percent()
            # self.cpu_usage = cpu_usage
            self.braille_stream.add_value(cpu_usage)
            val_string = f" CPU Usage {cpu_usage}% "
            graph = "\n".join(
                [val_string + self.braille_stream.graph[0][len(val_string):]] + self.braille_stream.graph[1:]
            )
            self.group.renderables[0] = Text(graph, style="green")
            self.refresh()
            await asyncio.sleep(interval)

    def render(self) -> RenderResult:
        return self.group
