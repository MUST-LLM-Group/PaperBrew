import os

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, HorizontalGroup
from textual.message import Message
from textual.widgets import RichLog, Button, Label, Select, Input, Rule
import asyncio
import subprocess
from textual.reactive import reactive


class HuggingFace(VerticalScroll):
    pip_version = reactive("", recompose=True)


    async def run_command_richlog(self, command):
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
        self.text_log = self.query_one(RichLog)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        # if event.button.label == "Install MiniConda3":
        #     # disable button
        #     event.button.disabled = True
        #     await self._install_miniconda3_linux()
        pass


    class SendCommand(Message):

        def __init__(self, command: str) -> None:
            super().__init__()
            self.command = command

    @on(Select.Changed)
    async def select_changed(self, event: Select.Changed) -> None:
        # 判断id
        if event.select.id == "hf_mirrors_select":
            self.selected_mirror = event.value
            if self.selected_mirror == Select.BLANK:
                return
            elif self.selected_mirror == "hf-mirror.com":
                self.post_message(self.SendCommand("export HF_ENDPOINT=https://hf-mirror.com\n"))
                self.post_message(self.SendCommand("echo $HF_ENDPOINT\n"))

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "hf_home_input":
            self.post_message(self.SendCommand(f"export HF_HOME={event.input.value}\n"))

    def compose(self) -> ComposeResult:

        yield Label("Notice: We only set envs for this running shell, it won't affect your system envs.", classes="title")

        hf_mirror = os.getenv("HF_MIRROR", "None")
        yield HorizontalGroup(
            Label("HuggingFace Mirror", classes="title"),
            Select.from_values(["None", "hf-mirror.com"], value=hf_mirror,
                               id="hf_mirrors_select"),
        )
        Rule()
        hf_home = os.getenv("HF_HOME", "None")
        yield HorizontalGroup(
            Label("HuggingFace HOME", classes="title"),
            Input(value=hf_home, id="hf_home_input"),
        )

        yield RichLog(highlight=True, markup=True)
