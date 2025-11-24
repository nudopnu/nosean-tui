import sys

from textual.app import App
from textual.widgets import Label, Collapsible, Markdown
from textual.color import Color
from textual.events import Key

from nosean.vault import Entry
from nosean.fuzzy_search import FuzzySearch


class MyApp(App):

    CSS = """
    Tooltip {
        background: $primary;
    }
    """

    def __init__(self, entries: list[Entry], driver_class = None, css_path = None, watch_css = False, ansi_color = False):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.entries: list[Entry] = entries
        self.fuzzy_search = FuzzySearch([e.name for e in entries])
        self.search_buffer = ""

    def compose(self):
        self.screen.styles.background = Color(0, 0, 0, 0)
        self.lbl_search = Label()
        self.lbl_debug = Label("Hello")
        yield self.lbl_search
        yield self.lbl_debug
        self.collapsibles: list[Collapsible] = []
        for entry in self.entries[:5]:
            collapsible = Collapsible(title=entry.name)
            collapsible.styles.background = Color(0, 0, 0, 0)
            collapsible.styles.border = ("none", "orange")
            collapsible.styles.padding = (0, 0)
            self.collapsibles.append(collapsible)
            with collapsible:
                md = Markdown(markdown=entry.content)
                md.styles.padding = (0, 0)
                yield md

    def _on_key(self, event: Key):
        self.lbl_debug.update(event.key)
        focused_widget = self.screen.focused
        if event.key in "XQ":
            sys.exit()
        elif event.key == "backspace":
            self.search_buffer = self.search_buffer[:-1]
            self.lbl_search.update(self.search_buffer)
            return
        elif event.key == "D":
            self.search_buffer = ""
            self.lbl_search.update(self.search_buffer)
            return
        elif event.key in ["J", "down"]:
            self.action_focus_next()
            return
        elif event.key in ["K", "up"]:
            self.action_focus_previous()
            return
        elif event.key in ["L", "H"] and focused_widget:
            focused_widget.action_toggle_collapsible()
            return
        
        if c := event.character:
            self.search_buffer += c
        self.lbl_search.update(self.search_buffer)
        entry_names = self.fuzzy_search.fuzzy_search(self.search_buffer)
        for name, collapsible in zip(entry_names, self.collapsibles):
            collapsible.title = name + f"{len(entry_names)}"
        for i in range(len(entry_names), 5):
            self.collapsibles[i].title = ""




            
