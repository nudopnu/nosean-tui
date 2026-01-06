from textual import on
from textual.suggester import SuggestFromList, Suggester
from textual.app import App
from textual.widgets import Input, Label
from textual.binding import Binding


class CustomSuggester(Suggester):

    async def get_suggestion(self, value):
        return "xxx"


class AppTwo(App[None]):

    CSS = """
    Tooltip {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", tooltip="Quit the app and return to the command prompt.", show=False),
    ]

    def compose(self):
        self.suggester = CustomSuggester()
        self.input = Input(suggester=self.suggester)
        self.lbl = Label()
        yield Label("Search something:")
        yield self.input
        yield self.lbl
    
    async def on_key(self, event):
        match event.key:
            case "tab":
                suggestion = await self.suggester.get_suggestion(self.lbl.content)
                self.input.value = f"{suggestion}."
                self.input.cursor_position = len(suggestion)
    
    @on(Input.Changed)
    def update_label(self, event: Input.Changed):
        text_value = event.value
        self.lbl.update(text_value)