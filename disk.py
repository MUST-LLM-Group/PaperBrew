import asyncio
from typing import Union

import psutil
from rich.console import Group
from rich.style import Style
from rich.text import Text
from textual import events
from textual._time import time
from textual.app import ComposeResult, RenderResult
from textual.containers import Container, VerticalGroup, HorizontalGroup
from textual.reactive import reactive
from textual.renderables.gradient import LinearGradient
from textual.widget import Widget
from textual.widgets import Static, Label

from braille_stream import BrailleStream

class DiskChart(Widget):
    def __init__(self, id, style: Union[str, Style] = ""):
        super().__init__()
        self.id = id
        self.style = style
        self.group = Group("")

    def render(self) -> RenderResult:
        return self.group



class Disk(VerticalGroup):
    disk_space_psutil = reactive(None, recompose=True)

    def __init__(self):
        super().__init__()
        self.disk_space_psutil = None

    async def get_disk_usage(self, interval):
        while True:
            self.disk_space_psutil = self.get_disk_space_psutil()
            self.refresh()
            await asyncio.sleep(interval)

    def get_disk_space_psutil(self):
        disk_partitions = psutil.disk_partitions()
        disk_space_info = []
        for partition in disk_partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_space_info.append({
                "mountpoint": partition.mountpoint,
                "device": partition.device,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
                'total_gb': usage.total / (1024 ** 3),
                'used_gb': usage.used / (1024 ** 3),
                'free_gb': usage.free / (1024 ** 3),
            })
        return disk_space_info

    async def on_mount(self, event: events.Mount) -> None:
        # self.mem_chart_used = self.query_exactly_one("#mem_chart_used")
        asyncio.create_task(self.get_disk_usage(1))

    def compose(self):
        if self.disk_space_psutil is not None:
            for item in self.disk_space_psutil:
                mount_point:str = item["mountpoint"]
                if mount_point != "/" and not mount_point.startswith("/System/") and not mount_point.startswith("/Volumes/"):
                    break
                if mount_point == "/":
                    mount_name = "root"
                else:
                    mount_name = mount_point.rsplit('/', 1)[-1]

                total_gb = item["total_gb"]
                free_gb = item["free_gb"]
                yield HorizontalGroup(
                    Label(f"{mount_name}", classes="disk_label_left"),
                    Label(f"{free_gb:.2f}GB / {total_gb:.2f}GB", classes="disk_label_right")
                )
        else:
            yield Label("Loading...")

