from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static
from textual_terminal import Terminal

from cpu import CPU
from disk import Disk
from gpu import GPU
from mem import Mem


class DashBoard(Container):

    cpu_usage = reactive(0.0, recompose=True)
    gpu_usage = reactive(0.0)

    # on_mount
    def __init__(self):
        super().__init__()
        self.os_type = self._get_os_type()
        self.cpu_arch = self._get_cpu_arch()
        self.hostname = self._get_hostname()
        self.python_version = self._get_python_version()
        self.env_hf_endpoint = self._get_env_hf_endpoint()
        self.env_hf_home = self._get_env_hf_home()



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

    def compose(self) -> ComposeResult:
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
        cpu.border_title="CPU"
        yield cpu

        mem = Mem()
        mem.border_title = "MEM"
        yield Mem()

        gpu = GPU()
        gpu.border_title = "GPU"
        yield gpu

        disk = Disk()
        disk.border_title = "DISK"
        yield disk


        # hf = Static(f"HugginFace", classes="box", id="hf")
        # hf.border_title = "HugginFace"
        # yield hf
