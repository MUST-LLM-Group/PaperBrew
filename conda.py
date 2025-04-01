import os
from platform import python_version
from typing import List

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, HorizontalGroup, VerticalGroup
from textual.widgets import Button, ListView, Label, ListItem, Input, Select, Log
from rich.syntax import Syntax
import asyncio
import subprocess
from textual.layouts.grid import GridLayout
from textual.reactive import reactive


class Conda(VerticalScroll):
    conda_prefix = reactive("")
    conda_info_root = reactive("")
    conda_envs = reactive([])

    def __init__(self, id: str = None):
        # 调用父类的构造方法，确保父类的初始化逻辑也被执行
        super().__init__(id=id)
        # 调用当前类的私有方法 _get_conda_env() 来获取 conda 环境的前缀路径
        # 并将结果赋值给实例变量 self.conda_prefix
        self.conda_info_root = None
        self.update_conda_info_root()
        self.conda_envs = []

        self.text_log = None
        self.conda_prefix = self._get_conda_prefix()

    async def _install_miniconda3_linux(self):
        self.text_log.write_line("Installing Miniconda3 ...")
        # await self.run_command_log(['ping', 'www.aibsd.com', '-c', '1000'])
        home_dir = os.path.expanduser("~")

        import platform
        machine = platform.machine()
        if machine == 'x86_64':
            arch = 'x86_64'
        elif machine == 'aarch64':
            arch = 'aarch64'
        else:
            raise ValueError(f"Unsupported architecture: {machine}")

        await self.run_command_log(['mkdir', '-p', f'{home_dir}/miniconda3'])

        import urllib.request
        # Downloading the Miniconda3 installer from the provided URL
        url = f"https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-{arch}.sh"
        destination = f'{home_dir}/miniconda3/miniconda.sh'
        urllib.request.urlretrieve(url, destination)

        try:
            # await self.run_command_log(['wget', 'https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh', '-O', f'{home_dir}/miniconda3/miniconda.sh'])
            await self.run_command_log(['bash', f'{home_dir}/miniconda3/miniconda.sh', '-b', '-u', '-p', f'{home_dir}/miniconda3'])
            await self.run_command_log(['rm', '-rf', f'{home_dir}/miniconda3/miniconda.sh'])
            await self.run_command_log([f'{home_dir}/miniconda3/bin/conda', 'init', 'bash'])
            await self.run_command_log([f'{home_dir}/miniconda3/bin/conda', 'init', 'zsh'])
        except:
            pass

    async def run_command_log(self, command):
        # 打印command
        self.text_log.write_line(f"- {' '.join(command)}")

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
            self.text_log.write_line(line.decode().strip())

        # 等待子进程结束
        await process.wait()
        # 检查子进程退出码
        if process.returncode == 0:
            self.text_log.write_line("\n")
        else:
            error = await process.stderr.read()
            self.text_log.write_line(f"Command failed with error: {error.decode().strip()}\n\n")


    def run_command(self, command: List[str]) -> str:
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

    def _get_conda_prefix(self) -> str:
        import os
        return os.getenv("CONDA_PREFIX")


    async def on_mount(self) -> None:
        """Called  when the DOM is ready."""
        self.text_log = self.query_one("#conda_log")
        self.call_after_refresh(self.update_conda_envs)
        self.call_after_refresh(self.update_conda_env_listview)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.label == "Install MiniConda3":
            # disable button
            event.button.disabled = True
            await self._install_miniconda3_linux()
            event.button.disabled = False

        if event.button.label == "Create New Env":
            new_env_name = self.query_one("#new_env_name_input").value
            new_env_version = self.query_one("#new_env_version_select").value

            event.button.disabled = True
            self.text_log.write_line(f"Creating new environment: {new_env_name} with Python {new_env_version} ...")
            await self.run_command_log([f'{self.conda_info_root}/bin/conda', 'create', '-y', '-n', new_env_name, f'python={new_env_version}'])
            self.text_log.write_line("Done.\n")
            event.button.disabled = False

            self.update_conda_envs()
            await self.update_conda_env_listview()

    async def update_conda_env_listview(self):
        await self.query_one(ListView).clear()
        for conda_env in self.conda_envs:
            await self.query_one(ListView).append(ListItem(Label(f"{conda_env['name']:<16} {conda_env['python_version']}")))
        self.query_one(ListView).refresh()

    def on_list_view_selected(self, event: ListView.Selected):
        # self.text_log.write_line(f"Selected: !!!!")
        self.conda_prefix = self._get_conda_prefix()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        # self.title = str(event.value)
        pass

    async def update_conda_envs(self):
        envs = [f for f in os.listdir(self.conda_info_root + "/envs") if not f.startswith('.')]
        envs.sort()
        # use conda run -n myenv python --version to get python version
        self.conda_envs = []
        for env in envs:
            # 这种方法太慢了！
            python_version = self.run_command([f'{self.conda_info_root}/bin/conda', 'run', '-n', env, 'python', '--version'])

            # 通过 ls envs/env_name/conda-meta/python-3.12.9-*.json文件 来判断python版本为3.12
            files = os.listdir(self.conda_info_root + "/envs/" + env + "/conda-meta")
            # 正则表达式匹配 'python-版本号' 格式
            pattern = r'python-(\d+\.\d+\.\d+)'
            # 提取版本号
            import re
            version_numbers = [re.search(pattern, file).group(1) for file in files if re.search(pattern, file)]

            self.conda_envs.append({
                "name": f"{env}",
                "python_version" : version_numbers[0] if version_numbers else ""
            })

    def update_conda_info_root(self):
        self.conda_info_root = self.run_command(['conda', 'info', '--root'])

    def compose(self) -> ComposeResult:

        conda_info_root_label = Label(f"CONDA_ROOT: {self.conda_info_root}" + f"""\nCONDA_PREFIX: {self.conda_prefix}""", id="conda_info_root_label")
        yield conda_info_root_label

        # listview = ListView(*[ListItem(Label(f"{conda_env['name']:<16} {conda_env['python_version']}")) for conda_env in self.conda_envs], id="conda_env_listview")
        listview = ListView(id="conda_env_listview")
        yield listview

        if self.conda_prefix is None:
            yield Button("Install MiniConda3")
        else:
            supported_python_versions: List[str] = ['3.12', '3.11', '3.10', '3.9', '3.8', '3.7', '3.6']
            yield HorizontalGroup(
                Input(id="new_env_name_input", placeholder="New Env Name"),
                Select.from_values(supported_python_versions, value=supported_python_versions[0], id="new_env_version_select"),
                Button("Create New Env"),
            )
        yield VerticalGroup(
            Label("Console Log"),
            Log(id="conda_log"),
            id="conda_log_group"
        )