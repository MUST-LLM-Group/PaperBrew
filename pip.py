from __future__ import annotations

import os
from typing import List

from textual import on, events, work
from textual.app import ComposeResult
from textual.containers import VerticalScroll, VerticalGroup, HorizontalGroup, Container
from textual.widget import Widget
from textual.widgets import Button, ListView, Label, ListItem, Select, Input, Rule, Log
from rich.syntax import Syntax
import asyncio
import subprocess
from textual.layouts.grid import GridLayout
from textual.reactive import reactive

class PipPackageListView(Widget):
    pip_packages = reactive([], recompose=True)

    def compose(self) -> ComposeResult:
        pip_packages_listview = ListView(*[ListItem(Label(package)) for package in self.pip_packages],
                                         id="pip_packages_listview")
        yield pip_packages_listview


class Pip(VerticalScroll):
    pip_version = reactive("", recompose=True)

    def __init__(self, id: str | None= None):
        super().__init__(id = id)
        # pip_version_raw = self.run_command(["pip", "--version"])
        # self.pip_version = pip_version_raw.split(" ")[1]
        self.selected_env = Select.BLANK
        self.pip_package_list_view = PipPackageListView(id="pip_package_list_view")
        self.grabbed = False

    def on_mount(self) -> None:
        """Called  when the DOM is ready."""
        self.text_log = self.query_exactly_one("#pip_log")
        # self.text_log.write_line(f"Pip Version: {self.pip_version}\n\n")
        self.call_after_refresh(self.update_data)

    @work(exclusive=True, thread=True)
    def update_data(self):
        pip_mirror = self.run_command(['pip', 'config', 'get', 'global.index-url'])
        if pip_mirror is None:
            pip_mirror = "官方源(国外)"
        elif pip_mirror == "https://pypi.tuna.tsinghua.edu.cn/simple":
            pip_mirror = "清华源"
        elif pip_mirror == "https://mirrors.ustc.edu.cn/pypi/web/simple":
            pip_mirror = "中科大"
        elif pip_mirror == "https://mirrors.huaweicloud.com/pypi/simple":
            pip_mirror = "华为云"
        elif pip_mirror == "https://mirrors.aliyun.com/pypi/simple":
            pip_mirror = "阿里云"
        else:
            pip_mirror = "官方源(国外)"
        self.query_one("#pip_mirrors_select", Select).value = pip_mirror


        conda_info_root = self.run_command(['conda', 'info', '--root'])
        conda_envs = [f for f in os.listdir(conda_info_root + "/envs") if not f.startswith('.')]
        conda_envs.sort()
        conda_env_select = self.query_one("#conda_env_select", Select)
        conda_env_select.set_options([(env, env) for env in conda_envs])


    async def refresh_pip_packages(self, env_name):
        pip_packages_raw = await self.run_command_log(['conda', 'run', '-n', env_name, 'pip', 'list'], should_send_to_log=False)
        self.pip_package_list_view.pip_packages = pip_packages_raw[2:]


    async def run_command_log(self, command, should_send_to_log: bool = True):
        # 打印command
        if should_send_to_log:
            self.text_log.write_line(f"- {' '.join(command)}")

        # 创建子进程，并设置管道以捕获标准输出
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        lines = []

        # 读取子进程的标准输出和标准错误输出
        while True:
            # 读取一行输出
            line = await process.stdout.readline()
            if not line:
                break
            # 解码并打印输出
            lines.append(line.decode().strip())
            if should_send_to_log:
                self.text_log.write_line(line.decode().strip())

        # 等待子进程结束
        await process.wait()
        # 检查子进程退出码
        if process.returncode == 0:
            if should_send_to_log:
                self.text_log.write_line("\n")
        else:
            error = await process.stderr.read()
            if should_send_to_log:
                self.text_log.write_line(f"Command failed with error: {error.decode().strip()}\n\n")
        return lines

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

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        package_name = self.query_one(Input).value
        if event.button.id == "pip_install_button":
            if package_name != "":
                self.query_one("#pip_install_button").disabled = True
                self.query_one("#pip_uninstall_button").disabled = True

                # get pip mirrors
                pip_mirror = self.query_one("#pip_mirrors_select").value
                if pip_mirror == "清华源":
                    await self.run_command_log(['conda', 'run', '-n', self.selected_env, '--live-stream', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple', package_name])
                elif pip_mirror == "阿里云":
                    await self.run_command_log(['conda', 'run', '-n', self.selected_env, '--live-stream', 'pip', 'install', '-i', 'https://mirrors.aliyun.com/pypi/simple', package_name])
                elif pip_mirror == "华为云":
                    await self.run_command_log(['conda', 'run', '-n', self.selected_env, '--live-stream', 'pip', 'install', '-i', 'https://mirrors.huaweicloud.com/pypi/simple', package_name])
                else:
                    await self.run_command_log(['conda', 'run', '-n', self.selected_env, '--live-stream', 'pip', 'install', package_name])
                # refresh pip package list
                await self.refresh_pip_packages(self.selected_env)

                self.query_one("#pip_install_button").disabled = False
                self.query_one("#pip_uninstall_button").disabled = False

        if event.button.id == "pip_uninstall_button":
            if package_name != "":
                await self.run_command_log(['conda', 'run', '-n', self.selected_env, '--live-stream', 'pip', 'uninstall', '-y', package_name])


    def on_list_view_selected(self, event: ListView.Selected):
        pass

    @on(Select.Changed)
    async def select_changed(self, event: Select.Changed) -> None:
        # 判断id
        if event.select.id == "conda_env_select":
            self.selected_env = event.value
            self.text_log.write_line(f"Selected conda env: {event.value}\n\n")
            if self.selected_env != Select.BLANK:
                await self.refresh_pip_packages(event.value)
        if event.select.id == "pip_mirrors_select":
            if event.value == Select.BLANK:
                return
            pip_mirror = event.value
            self.text_log.write_line(f"Selected pip mirror: {event.value}\n\n")
            # pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
            if pip_mirror == "清华源":
                await self.run_command_log(['pip', 'config', 'set', 'global.index-url', 'https://pypi.tuna.tsinghua.edu.cn/simple'])
            elif pip_mirror == "中科大":
                await self.run_command_log(['pip', 'config', 'set', 'global.index-url', 'https://mirrors.ustc.edu.cn/pypi/web/simple'])
            elif pip_mirror == "阿里云":
                await self.run_command_log(['pip', 'config', 'set', 'global.index-url', 'https://mirrors.aliyun.com/pypi/simple'])
            elif pip_mirror == "华为云":
                await self.run_command_log(['pip', 'config', 'set', 'global.index-url', 'https://mirrors.huaweicloud.com/pypi/simple'])
            else:
                await self.run_command_log(['pip', 'config', 'set', 'global.index-url', 'https://pypi.org/simple'])

    def compose(self) -> ComposeResult:
        # pip_version_label = Label(f"Pip Version: {self.pip_version}", classes="pip-version")
        # yield pip_version_label

        yield HorizontalGroup(
            Container(Label("Pip Mirror(Global)", id="pip_mirror_label"),
                      classes="text_box"),
            Select.from_values(["官方源(国外)", "清华源", "中科大", "阿里云", "华为云"], value=Select.BLANK, id="pip_mirrors_select"),
            id="pip_horizontal_group"
        )
        yield HorizontalGroup(
            Container(Label("Conda Env", id="conda_env_label"),
                      classes="text_box"),
            Select([], id="conda_env_select", value=Select.BLANK),
        )

        yield self.pip_package_list_view

        yield HorizontalGroup(
            Input(id="pip_install_package_name_input", placeholder="Package Name"),
            Button("Install", id="pip_install_button"),
            Button("Uninstall", id="pip_uninstall_button"),
        )

        yield VerticalGroup(
            Label("Console Log"),
            Log(id="pip_log"),
            id="pip_log_group"
        )

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
