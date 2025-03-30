import asyncio
from typing import Union

import psutil
from rich.console import Group
from rich.style import Style
from rich.text import Text
from textual import events
from textual._time import time
from textual.app import ComposeResult, RenderResult
from textual.containers import Container, VerticalGroup
from textual.reactive import reactive
from textual.renderables.gradient import LinearGradient
from textual.widget import Widget
from textual.widgets import Static

from braille_stream import BrailleStream

class MemChart(Widget):
    def __init__(self, id, style: Union[str, Style] = ""):
        super().__init__()
        self.id = id
        self.style = style
        self.group = Group("")
        mem_total = psutil.virtual_memory().total
        self.braille_stream = BrailleStream(20, 4, 0.0, mem_total)

    def write(self, mem_used):
        self.braille_stream.add_value(mem_used)
        self.group.renderables[0] = Text("\n".join(self.braille_stream.graph), style=self.style)
        self.refresh()

    def render(self) -> RenderResult:
        return self.group



class Mem(VerticalGroup):
    total_gb = reactive(1.0, recompose=True)
    used_gb = reactive(1.0, recompose=True)
    free_gb = reactive(1.0, recompose=True)

    def __init__(self):
        super().__init__()
        self.mem_chart_used = None
        self.mem_chart_free = None

    async def get_mem_usage(self, interval):
        while True:
            self.mem_chart_used.write(psutil.virtual_memory().used)
            self.mem_chart_free.write(psutil.virtual_memory().free)

            total = psutil.virtual_memory().total
            self.total_gb = total / (1024 ** 3)
            used = psutil.virtual_memory().used
            self.used_gb = used / (1024 ** 3)
            free = psutil.virtual_memory().free
            self.free_gb = free / (1024 ** 3)


            await asyncio.sleep(interval)

    async def on_mount(self, event: events.Mount) -> None:
        self.mem_chart_used = self.query_exactly_one("#mem_chart_used")
        self.mem_chart_free = self.query_exactly_one("#mem_chart_free")
        asyncio.create_task(self.get_mem_usage(1))

    def compose(self):
        yield VerticalGroup(
         Static(f"Total:  {self.total_gb:0f}GB"),

         Static(f"Used:  {self.used_gb:0f}GB"),
         MemChart(id="mem_chart_used", style="blue_violet"),

         Static(f"Free:  {self.free_gb:0f}GB"),
         MemChart(id="mem_chart_free", style="orange1"),
        )
        #https://github.com/Textualize/rich/blob/863d3daa54565cd169139616b71ab4bd8548e3ec/docs/source/appendix/colors.rst