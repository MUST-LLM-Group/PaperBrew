from textual import events
from textual.app import ComposeResult, App
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual_terminal import Terminal

from conda import Conda
from dashboard import DashBoard
from huggingface import HuggingFace
from papers import Papers
from pip import Pip
from terminal_panel import TerminalPanel


class PaperReproducer(App):
    """Paper reproducer app."""

    CSS_PATH = "main.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def on_resize(self, event: events.Resize) -> None:
        # self.refresh(recompose=True)
        # self.recompose()
        # self.compose()
        pass

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

        # with TabbedContent():
        #     with TabPane("DashBoard", id="dashboard"):
        #         yield DashBoard()
        #     with TabPane("Conda", id="conda"):
        #         yield Conda()
        #     with TabPane("Pip", id="pip"):
        #         yield Pip()
        #     with TabPane("HuggingFace", id="huggingface"):
        #         yield HuggingFace()
        #     with TabPane("Papers", id="papers"):
        #         yield Papers()

        yield Terminal(command=f"bash", id="terminal_bash")

    def on_ready(self) -> None:
        terminal_bash: Terminal = self.query_one("#terminal_bash")
        terminal_bash.start()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = PaperReproducer()
    # app = DashBoard()
    app.run()