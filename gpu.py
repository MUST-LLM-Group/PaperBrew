import asyncio
import json

import subprocess
from time import sleep

import psutil
from rich.console import Group
from rich.text import Text
from textual import events, work
from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.reactive import reactive
from textual.renderables.gradient import LinearGradient
from textual.widget import Widget
from textual.widgets import Static, Label, Log

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
        self.call_after_refresh(self.start_gpu_monitor)

    def start_gpu_monitor(self):
        if self.os_type == "darwin":
            self.get_macmon_output(3)
        elif self.is_nvidia_smi_installed:
            self.get_nvidia_smi_output(3)

    @work(exclusive=True, thread=True)
    def is_nvidia_smi_installed(self) -> bool:  # 检测是否有nvidia-smi命令
        if self.os_type == "linux" and self.cpu_arch == "x86_64":
            try:
                result = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                        check=True)
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

    def csv_str_to_dict(self, csv_str):
        # 将CSV字符串分割成行
        lines = csv_str.strip().split('\n')

        # 获取标题行和值行
        headers = lines[0].split(', ')
        values = lines[1].split(', ')

        # 将标题和值组合成字典
        gpu_dict = {}
        for header, value in zip(headers, values):
            gpu_dict[header] = value

        return gpu_dict


    @work(exclusive=True, thread=True)
    def get_macmon_output(self, interval):
        while True:
            try:
                result = subprocess.run(["macmon", "pipe", "-s", "1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                # parse json
                json_result = json.loads(result.stdout)
                self.app.call_from_thread(self.query_one(Log).clear)
                self.app.call_from_thread(self.query_one(Log).write_line, f"{"Frequency:":<12} {json_result['gpu_usage'][0]}MHz")
                self.app.call_from_thread(self.query_one(Log).write_line, f"{"Usage:":<12} {json_result['gpu_usage'][1]* 100:.0f}%")
                sleep(1)
            except Exception as e:
                self.app.call_from_thread(self.query_one(Log).clear)
                self.app.call_from_thread(self.query_one(Log).write_line, "CPU Monitor relies on macmon.")
                self.app.call_from_thread(self.query_one(Log).write_line, "Run 'brew install macmon' to install it.")
                print(f"An unexpected error occurred: {e}")
                break

    @work(exclusive=True, thread=True)
    def get_nvidia_smi_output(self, interval):
        while True:
            try:
                # run nvidia-smi command
                csv_result = subprocess.run(["nvidia-smi",
                                             "--query-gpu=name,temperature.gpu,fan.speed,power.draw,power.limit,memory.total,memory.used,utilization.gpu,compute_mode",
                                             "--format=csv,nounits"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            text=True, check=True)
                # 整理为Python字典
                gpu_info_dict = self.csv_str_to_dict(csv_result.stdout)
                self.app.call_from_thread(self.query_one(Log).clear)
                self.app.call_from_thread(self.query_one(Log).write, f"{gpu_info_dict["name"]}\n\n")
                self.app.call_from_thread(self.query_one(Log).write, f"Usage: {gpu_info_dict["utilization.gpu [%]"]}%\n")
                self.app.call_from_thread(self.query_one(Log).write, f"TEMP: {gpu_info_dict["temperature.gpu"]}C\n")
                self.app.call_from_thread(self.query_one(Log).write, f"FAN: {gpu_info_dict["fan.speed [%]"]}%\n")
                self.app.call_from_thread(self.query_one(Log).write,
                    f"POWER: {gpu_info_dict["power.draw [W]"]}W / {gpu_info_dict["power.limit [W]"]}W\n")
                self.app.call_from_thread(self.query_one(Log).write,
                    f"MEM: {gpu_info_dict["memory.used [MiB]"]}MiB / {gpu_info_dict["memory.total [MiB]"]}MiB\n")
                sleep(1)
            except Exception as e:
                self.app.call_from_thread(self.query_one(Log).clear)
                self.app.call_from_thread(self.query_one(Log).write_line, "Nvidia GPU not detected")
                print(f"An unexpected error occurred: {e}")
                break

    def compose(self) -> ComposeResult:
        yield Log(id="gpu_log")
