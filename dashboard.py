from __future__ import annotations

import platform
from textual import events
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static
from cpuinfo import get_cpu_info

from cpu import CPU
from gpu import GPU


class DashBoard(VerticalScroll):

    cpu_usage = reactive(0.0, recompose=True)
    gpu_usage = reactive(0.0)

    # on_mount
    def __init__(
            self,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.os_type = self._get_os_type()
        self.cpu_arch = self._get_cpu_arch()
        self.cpu_model = self._get_cpu_model()
        self.hostname = self._get_hostname()
        self.python_version = self._get_python_version()
        self.env_hf_endpoint = self._get_env_hf_endpoint()
        self.env_hf_home = self._get_env_hf_home()
        self.grabbed = False

    def _get_cpu_arch(self) -> str:
        return platform.machine()

    def _get_cpu_model(self) -> str:
        cpuinfo = get_cpu_info()
        return cpuinfo['brand_raw']

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

    def compose(self) -> ComposeResult:

        gpu = GPU()
        gpu.border_title = "GPU"
        yield gpu

        is_autodl = True if self.hostname.startswith("autodl") else False
        status_str = f"""OS: {self.os_type}
Arch: {self.cpu_arch}
Hostname: {self.hostname}
AutoDL: {is_autodl}
Python Version: {self.python_version}
HF_ENDPOINT: {self.env_hf_endpoint}
HF_HOME: {self.env_hf_home}
"""
        basic_info = Static(status_str, classes="box", id="basic_info")
        basic_info.border_title = "Basic Info"
        yield basic_info

        cpu = CPU()
        cpu.border_title=f"CPU - {self.cpu_model}"
        yield cpu

        # mem = Mem()
        # mem.border_title = "MEM"
        # yield Mem()

        # disk = Disk()
        # disk.border_title = "DISK"
        # yield disk


        # hf = Static(f"HugginFace", classes="box", id="hf")
        # hf.border_title = "HugginFace"
        # yield hf


    async def on_mouse_down(self, event: events.MouseDown) -> None:
        self.grabbed = True
        event.stop()

    async def on_mouse_up(self, event: events.MouseUp) -> None:
        if self.grabbed:
            self.grabbed = False
        event.stop()

    async def on_mouse_move(self, event: events.MouseMove) -> None:
        if self.grabbed:
            self.styles.offset = (self.offset.x + event.delta_x, self.offset.y + event.delta_y)
