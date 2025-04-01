import os

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Button, ListView, Label, ListItem, Input, Log
from rich.syntax import Syntax
import asyncio
import subprocess
from textual.layouts.grid import GridLayout
from textual.reactive import reactive


class Papers(VerticalScroll):
    pip_version = reactive("", recompose=True)


    async def run_command_log(self, command):
        # 打印command
        self.text_log.write(f"- {' '.join(command)}")

        # 创建子进程，并设置管道以捕获标准输出
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 读取子进程的标准输出和标准错误输出
        while True:
            # 读取一行输出
            line = await process.stdout.readline()
            if not line:
                break
            # 解码并打印输出
            self.text_log.write({line.decode().strip()})

        # 等待子进程结束
        await process.wait()
        # 检查子进程退出码
        if process.returncode == 0:
            self.text_log.write("\n")
        else:
            error = await process.stderr.read()
            self.text_log.write(f"Command failed with error: {error.decode().strip()}\n\n")


    def run_command(self, command):
        """
        执行指定的命令并返回输出。

        :param command: 要执行的命令，作为列表传入，例如 ['conda', 'info', '--root']
        :return: 命令的输出
        """
        try:
            # 执行命令，捕获标准输出和标准错误
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            # 返回标准输出
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # 命令执行失败，返回错误信息
            return f"An error occurred: {e.stderr}"
        except FileNotFoundError:
            # 命令未找到
            return "Command not found. Please check if the command is installed and in the system PATH."


    def on_mount(self) -> None:
        """Called  when the DOM is ready."""
        self.text_log = self.query_one(Log)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        # if event.button.label == "Install MiniConda3":
        #     # disable button
        #     event.button.disabled = True
        #     await self._install_miniconda3_linux()
        pass

    def on_list_view_selected(self, event: ListView.Selected):
        # self.text_log.write(f"Selected: !!!!")
        # self.conda_prefix = self._get_conda_env()
        pass

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search by arxiv id, GitHub repo or title", id="search-input")

        yield Log(highlight=True)
