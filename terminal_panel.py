from textual.app import ComposeResult
from textual.widget import Widget
from textual_terminal import Terminal

class TerminalPanel(Widget):

    def compose(self) -> ComposeResult:
        yield Terminal(command="bash", id="terminal_bash")

    def on_mount(self) -> None:
        terminal_bash: Terminal = self.query_one("#terminal_bash")
        terminal_bash.start()
