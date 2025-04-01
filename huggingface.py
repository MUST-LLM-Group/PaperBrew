import os

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, HorizontalGroup, VerticalGroup, Container
from textual.message import Message
from textual.widgets import Button, Label, Select, Input, Rule
import asyncio
import subprocess
from textual.reactive import reactive


class HuggingFace(VerticalScroll):
    pip_version = reactive("", recompose=True)

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
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        # if event.button.label == "Install MiniConda3":
        #     # disable button
        #     event.button.disabled = True
        #     await self._install_miniconda3_linux()
        if event.button.id == "hf_home_button":
            self.post_message(self.SendCommand(f"export HF_HOME={self.query_one("#hf_home_input").value}\n"))


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

    def compose(self) -> ComposeResult:

        yield Label("Notice: We only set envs for this running shell, it won't affect your system envs.", classes="title")

        hf_mirror = os.getenv("HF_MIRROR", "None")
        yield HorizontalGroup(
            Container(Label("HuggingFace Mirror", id="hf_mirror_label"),classes="text_box"),
            Select.from_values(["None", "hf-mirror.com"], value=hf_mirror,
                               id="hf_mirrors_select"),
        )
        hf_home = os.getenv("HF_HOME", "None")
        yield HorizontalGroup(
            Container(
                Label("HuggingFace HOME", id="hf_home_label"),
                classes="text_box"
            ),
            Input(value=hf_home, id="hf_home_input"),
            Button("Set", classes="title", id="hf_home_button"),
        )
