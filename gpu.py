import asyncio

import subprocess
import psutil
from rich.console import Group
from rich.text import Text
from textual import events
from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.reactive import reactive
from textual.renderables.gradient import LinearGradient
from textual.widget import Widget
from textual.widgets import Static, RichLog, Label

from braille_stream import BrailleStream


class GPU(Widget):

    def __init__(self):
        super().__init__()
        self.os_type = self._get_os_type()
        self.cpu_arch = self._get_cpu_arch()

    def _get_cpu_arch(self) -> str:
        import platform
        return platform.machine()

    def _get_os_type(self) -> str:
        import platform
        return platform.system().lower()

    def on_mount(self) -> None:
        if self.is_nvidia_smi_installed():
            asyncio.create_task(self.get_nvidia_smi_output(1))

    def is_nvidia_smi_installed(self) -> bool:# 检测是否有nvidia-smi命令
        if self.os_type == "linux" and self.cpu_arch == "x86_64":
            try:
                result = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                # 返回标准输出
                output = result.stdout.strip()
                if output.__contains__("No devices were found"):
                    return False

                return True
            except subprocess.CalledProcessError:
                print("nvidia-smi command not found")
                return False
        else:
            print("Unsupported OS or CPU architecture")
            return False

    async def get_nvidia_smi_output(self, interval):
        while True:
            # run nvidia-smi command
            result = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            output = result.stdout
            self.query_one(RichLog).clear()
            self.query_one(RichLog).write(output)
            await asyncio.sleep(interval)

    def compose(self) -> ComposeResult:
        rich_log = RichLog()

        yield rich_log