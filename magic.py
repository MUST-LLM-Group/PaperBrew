from __future__ import annotations

import asyncio
import os
from asyncio import subprocess

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static, RichLog
from textual_terminal import Terminal

from cpu import CPU
from disk import Disk
from gpu import GPU
from mem import Mem


class Magic(VerticalScroll):

    cpu_usage = reactive(0.0, recompose=True)
    gpu_usage = reactive(0.0)

    # on_mount
    def __init__(
            self,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)

    papers = [
        {
            "title": "A Survey on Graph Neural Networks",
            "author": "Jie Chen, Xuan Long Do, and Xiaojun Chang",
            "abstract": "Graph Neural Networks (GNNs) have emerged as a powerful tool for learning from graph-structured data. This survey provides an overview of GNNs, covering their key concepts, architectures, and applications. We also discuss the challenges and future directions in GNN research.",
            "git_url": "htpps://xxxx",
        },
        {
            "title": "GNN for Recommendation Systems",
            "author": "Xiang Wang, Yifan Hong, and Jie Tang",
            "abstract": "Graph Neural Networks (GNNs) have been successfully applied to recommendation systems. This paper provides an overview of GNN-based recommendation methods, including their architectures, algorithms, and evaluation metrics. We also discuss the challenges and future directions in GNN-based recommendation research.",
            "git_url": "htpps://xxxx",
        },
        {
            "title": "DressCode: Autoregressively Sewing and Generating Garments from Text Guidance",
            "author": "Kai He, Kaixin Yao, Qixuan Zhang, Jingyi Yu, Lingjie Liu, Lan Xu",
            "abstract": "DressCode is a novel method for generating garments from text guidance. It uses an autoregressive model to sew garments from text descriptions, allowing users to create custom clothing designs. This paper provides an overview of DressCode, including its architecture, algorithm, and applications.",
            "git_url": "https://github.com/IHe-KaiI/DressCode.git"
        }
    ]

    async def start(self):
        rich_log:RichLog = self.query_one("#magic_rich_log")
        self.text_log = rich_log
        rich_log.write("Starting Magic...")
        rich_log.write("正在获取Git仓库信息")
        git_url = await self.run_command_richlog(["git", "config", "--get", "remote.origin.url"])
        git_url = "https://github.com/IHe-KaiI/DressCode.git"
        for paper in self.papers:
            if paper["git_url"] == git_url:
                rich_log.write(f"Found paper:\n {paper['title']}\n  by {paper['author']}")
        rich_log.write("开始分析项目代码...")
        # 使用pipreqs分析项目代码
        # 获取当前目录的绝对路径
        current_dir = os.path.abspath(os.getcwd())
        await self.run_command_richlog(["python", "-m", "pipreqs.pipreqs", current_dir, "--print"])
        rich_log.write("项目代码分析完成...")




    def on_mount(self, event: events.Mount) -> None:
        self.call_after_refresh(self.start)


    def compose(self) -> ComposeResult:
        yield RichLog(id="magic_rich_log")

    async def run_command_richlog(self, command, should_send_to_richlog: bool = True):
        # 打印command
        if should_send_to_richlog:
            self.text_log.write(f"- {' '.join(command)}")

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
            if should_send_to_richlog:
                self.text_log.write(line.decode().strip())

        # 等待子进程结束
        await process.wait()
        # 检查子进程退出码
        if process.returncode == 0:
            if should_send_to_richlog:
                self.text_log.write("\n")
        else:
            error = await process.stderr.read()
            if should_send_to_richlog:
                self.text_log.write(f"Command failed with error: {error.decode().strip()}\n\n")
        return lines
