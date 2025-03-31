from textual import events, log
from textual.app import ComposeResult, App
from textual.containers import HorizontalGroup, Grid
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Header, Footer, Button, Label

from dashboard import DashBoard
from huggingface import HuggingFace
from papers import Papers
from pip import Pip
from textual_terminal import Terminal

from conda import Conda

class QuitScreen(ModalScreen[bool]):  # (1)!
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.dismiss(True)
        else:
            self.dismiss(False)


class PopupScreen(ModalScreen[bool]):

    def __init__(self, widget: Widget):
        super().__init__()
        self.widget = widget

    def compose(self) -> ComposeResult:
        yield self.widget

    def on_click(self, event: events.Click) -> None:
        # check if mouse click outside the modal
        # then dismiss the modal
        conda = self.query_one(f"#{self.widget.id}")
        if not conda.is_mouse_over:
            self.dismiss(True)


class PaperReproducer(App):
    """Paper reproducer app."""

    CSS_PATH = "main.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
    ]

    def action_request_quit(self) -> None:
        """Action to display the quit dialog."""

        def check_quit(quit: bool | None) -> None:
            """Called when QuitScreen is dismissed."""
            if quit:
                self.exit()

        self.push_screen(QuitScreen(), check_quit)

    def on_resize(self, event: events.Resize) -> None:
        # self.refresh(recompose=True)
        # self.recompose()
        # self.compose()
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dashboard_button":
            await self.push_screen(PopupScreen(DashBoard(id="dashboard")))
        elif event.button.id == "conda_button":
            await self.push_screen(PopupScreen(Conda(id="conda")))
        elif event.button.id == "pip_button":
            await self.push_screen(PopupScreen(Pip(id="pip")))
        elif event.button.id == "huggingface_button":
            await self.push_screen(PopupScreen(HuggingFace(id="huggingface")))
        elif event.button.id == "papers_button":
            await self.push_screen(PopupScreen(Papers(id="papers")))


    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

        yield HorizontalGroup(
            Button("DashBoard", id="dashboard_button"),
            Button("Conda", id="conda_button"),
            Button("Pip", id="pip_button"),
            Button("HuggingFace", id="huggingface_button"),
            Button("Papers", id="papers_button"),
        )
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

        yield Terminal(command=f"bash -rcfile ~/.bashrc -i -l", id="terminal_bash")

    async def send_message(self, message: str) -> None:
        terminal_bash: Terminal = self.query_one("#terminal_bash")
        await terminal_bash.send_queue.put(["stdin", message])


    async def on_ready(self) -> None:
        terminal_bash: Terminal = self.query_one("#terminal_bash")
        terminal_bash.start()
        await self.send_message("ls\n")
        await self.send_message("export HF_ENDPOINT=https://hf-mirror.com\n")
        await self.send_message("echo $HF_ENDPOINT\n")

    async def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
        await self.send_message("echo $HF_ENDPOINT\n")

    async def on_hugging_face_send_command(self, event: HuggingFace.SendCommand) -> None:
        await self.send_message("echo $HF_ENDPOINT\n")


if __name__ == "__main__":
    app = PaperReproducer()
    # app = DashBoard()
    app.run()