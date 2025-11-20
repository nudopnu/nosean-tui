import sys

from textual.app import App
from textual.widgets import Label, Collapsible, Markdown
from textual.color import Color
from textual.events import Key

from nosean.vault import Entry


class MyApp(App):

    CSS = """
    Tooltip {
        background: $primary;
    }
    """

    def __init__(self, entries: list[Entry], driver_class = None, css_path = None, watch_css = False, ansi_color = False):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.entries: list[Entry] = entries

    def compose(self):
        self.screen.styles.background = Color(0, 0, 0, 0)
        self.lbl_debug = Label("Hello")
        yield self.lbl_debug
        for entry in self.entries[:5]:
            collapsible = Collapsible(title=entry.name)
            collapsible.styles.background = Color(0, 0, 0, 0)
            collapsible.styles.border = ("none", "orange")
            collapsible.styles.padding = (0, 0)
            with collapsible:
                md = Markdown(markdown=entry.content)
                md.styles.padding = (0, 0)
                yield md

    def _on_key(self, event: Key):
        self.lbl_debug.update(event.key)
        focused_widget = self.screen.focused
        if event.key in "XQ":
            sys.exit()
        elif event.key == "J":
            self.action_focus_next()
        elif event.key == "K":
            self.action_focus_previous()
        elif event.key == "L" and focused_widget:
            focused_widget.action_toggle_collapsible()
            
