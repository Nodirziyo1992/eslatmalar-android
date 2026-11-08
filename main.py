"""ESLATMALAR Android application (Kivy): mobile-first, offline SQLite."""
from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform

from storage import NotesDB, CATEGORIES, current_date, validate_date

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
BG = (0.968, 0.964, 0.992, 1)
SURFACE = (1, 1, 1, 1)
INK = (0.10, 0.105, 0.17, 1)
MUTED = (0.50, 0.51, 0.60, 1)
PURPLE = (0.43, 0.35, 0.75, 1)
LAVENDER = (0.79, 0.79, 0.99, 1)
LINE = (0.86, 0.85, 0.92, 1)
MONTHS = ("Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr")


def label(text, size=14, color=INK, bold=False, height=32, halign="left"):
    w = Label(text=str(text), color=color, font_size=sp(size), bold=bold,
              size_hint_y=None, height=dp(height), halign=halign,
              valign="middle", shorten=True, shorten_from="right")
    w.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, inst.height)))
    return w


def clear_button(text, on_release, width=None, height=44, size=14, fg=INK, bold=False):
    b = Button(text=text, background_normal="", background_down="",
               background_color=(0, 0, 0, 0), color=fg,
               font_size=sp(size), bold=bold, size_hint_y=None, height=dp(height))
    if width:
        b.size_hint_x = None
        b.width = dp(width)
    b.bind(on_release=lambda *_: on_release())
    return b


def icon_button(name, on_release=None, size=38):
    path = str(ASSETS / f"{name}.png")
    b = Button(text="", background_normal=path, background_down=path,
               border=(0, 0, 0, 0), size_hint=(None, None), size=(dp(size), dp(size)))
    if on_release:
        b.bind(on_release=lambda *_: on_release())
    return b


def pill_button(text, on_release, bg=PURPLE, fg=SURFACE, height=46):
    b = Button(text=text, background_normal="", background_down="",
               background_color=bg, color=fg, bold=True, font_size=sp(13),
               size_hint_y=None, height=dp(height))
    b.bind(on_release=lambda *_: on_release())
    return b


class RoundedBox(BoxLayout):
    def __init__(self, bg=SURFACE, radius=14, **kwargs):
        super().__init__(**kwargs)
        self.bg = bg
        with self.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size


class EslatmalarApp(App):
    title = "Eslatmalar — Mingqulova Rayhona"

    def build(self):
        if platform not in ("android", "ios"):
            Window.size = (424, 810)
            Window.minimum_width = 350
            Window.minimum_height = 600
        Window.clearcolor = LAVENDER
        self.db = NotesDB(Path(self.user_data_dir) / "eslatmalar.sqlite3")
        self.search_text = ""
        self.category_filter = None
        self.favorites_only = False
        self.view_mode = "list"
        self.sort_mode = "updated_desc"
        self.active_id = None
        self.active_day = current_date()
        self.active_category = "Shaxsiy"
        self.is_favorite = False
        self.main_screen = None
        self.root_ui = FloatLayout()
        self.show_main()
        Window.bind(on_keyboard=self.on_keyboard)
        return self.root_ui

    def on_stop(self):
        self.db.close()

    def on_keyboard(self, _win, key, *_args):
        if key == 27 and self.main_screen == "editor":
            self.show_main()
            return True
        return False

    def page(self):
        self.root_ui.clear_widgets()
        page = RoundedBox(bg=BG, radius=0, orientation="vertical",
                          padding=(dp(19), dp(20), dp(19), dp(5)), spacing=dp(12),
                          size_hint=(1, 1))
        self.root_ui.add_widget(page)
        return page

    def show_main(self):
        self.main_screen = "main"
        page = self.page()
        header = BoxLayout(size_hint_y=None, height=dp(51), spacing=dp(14))
        header.add_widget(icon_button("menu", self.open_menu, 38))
        header.add_widget(label("Barcha qaydlar" if not self.favorites_only else "Sevimli qaydlar", 19, INK, True, 48))
        header.add_widget(icon_button("grid" if self.view_mode == "list" else "list", self.toggle_view, 38))
        page.add_widget(header)

        search = RoundedBox(orientation="horizontal", height=dp(49), size_hint_y=None,
                            padding=(dp(11), 0, dp(8), 0), spacing=dp(7), radius=10)
        search.add_widget(icon_button("search", size=28))
        self.search_input = TextInput(text=self.search_text, hint_text="Qaydlarni qidirish...",
                                      multiline=False, font_size=sp(14), foreground_color=INK,
                                      hint_text_color=MUTED, background_normal="",
                                      background_active="", background_color=(0, 0, 0, 0),
                                      cursor_color=PURPLE, padding=[dp(4), dp(13), dp(4), 0])
        self.search_input.bind(text=self.on_search)
        search.add_widget(self.search_input)
        page.add_widget(search)
        section = BoxLayout(size_hint_y=None, height=dp(28))
        section.add_widget(label("Toifalar", 15, INK, True, 28))
        section.add_widget(clear_button("Barchasi", self.all_categories, width=70, height=28, size=11, fg=PURPLE))
        page.add_widget(section)

        cats = BoxLayout(size_hint_y=None, height=dp(92), spacing=dp(10))
        for category, icon in zip(CATEGORIES, ("personal", "work", "travel", "health")):
            item = BoxLayout(orientation="vertical", spacing=dp(3))
            b = icon_button(icon, lambda c=category: self.select_category(c), 57)
            holder = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=dp(59))
            holder.add_widget(b)
            item.add_widget(holder)
            item.add_widget(label(category, 10, PURPLE if self.category_filter == category else INK,
                                  self.category_filter == category, 22, "center"))
            cats.add_widget(item)
        page.add_widget(cats)

        row = BoxLayout(size_hint_y=None, height=dp(29))
        row.add_widget(label("So‘nggi qaydlar", 15, INK, True, 29))
        self.count_text = label("", 11, MUTED, height=29, halign="right")
        row.add_widget(self.count_text)
        page.add_widget(row)

        self.scroller = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=1 if self.view_mode == "list" else 2,
                               spacing=dp(10), size_hint_y=None, padding=(0, 0, 0, dp(60)))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroller.add_widget(self.grid)
        page.add_widget(self.scroller)
        page.add_widget(self.bottom_navigation())

        fab = icon_button("plus-fab", lambda: self.edit_note(None), 60)
        fab.pos_hint = {"right": .96, "y": .125}
        self.root_ui.add_widget(fab)
        self.populate_notes()

    def all_categories(self):
        self.category_filter = None
        self.show_main()

    def select_category(self, cat):
        self.category_filter = cat if cat != self.category_filter else None
        self.show_main()

    def on_search(self, _instance, value):
        self.search_text = value
        self.populate_notes()

    def toggle_view(self):
        self.view_mode = "grid" if self.view_mode == "list" else "list"
        self.show_main()

    def populate_notes(self):
        if not hasattr(self, "grid"):
            return
        notes = self.db.list_notes(self.search_text, self.sort_mode,
                                   category=self.category_filter, favorites=self.favorites_only)
        self.count_text.text = f"{len(notes)} ta"
        self.grid.clear_widgets()
        self.grid.cols = 1 if self.view_mode == "list" else 2
        if not notes:
            empty = RoundedBox(size_hint_y=None, height=dp(188), orientation="vertical",
                               padding=dp(21), spacing=dp(12), radius=14)
            empty.add_widget(label("Hozircha qayd yo‘q", 17, INK, True, 40, "center"))
            empty.add_widget(label("+ tugmasi orqali birinchi qaydni yarating.", 12, MUTED, height=45, halign="center"))
            self.grid.add_widget(empty)
            return
        for note in notes:
            self.grid.add_widget(self.note_card(note))

    def note_card(self, note):
        compact = self.view_mode == "list"
        card = RoundedBox(orientation="vertical", radius=12, padding=(dp(13), dp(8), dp(10), dp(8)),
                          spacing=dp(3), size_hint_y=None, height=dp(99 if compact else 165))
        line = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(3))
        title = clear_button(note["title"], lambda n=note: self.edit_note(n["id"]), height=28, size=13, bold=True)
        line.add_widget(title)
        line.add_widget(icon_button("star-active" if note["is_favorite"] else "star",
                                    lambda n=note: self.toggle_favorite(n["id"]), 26))
        card.add_widget(line)
        desc = note["content"].replace("\n", " ")
        preview = (desc[:100] + "…") if len(desc) > 100 else desc
        card.add_widget(label(preview or "Matn kiritilmagan", 11, MUTED, height=26 if compact else 67))
        footer = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(3))
        footer.add_widget(label(self.pretty_date(note["event_date"]), 10, MUTED, height=28))
        footer.add_widget(icon_button("edit", lambda n=note: self.edit_note(n["id"]), 28))
        footer.add_widget(icon_button("trash", lambda n=note: self.ask_delete(n["id"]), 28))
        card.add_widget(footer)
        return card

    @staticmethod
    def pretty_date(value):
        try:
            d = date.fromisoformat(value)
            return f"{d.day:02d}.{d.month:02d}.{d.year}"
        except ValueError:
            return value

    def bottom_navigation(self):
        nav = BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(7))
        buttons = [
            ("notes", "Qaydlar", self.reset_main),
            ("star", "Sevimlilar", self.show_favorites),
            ("grid", "Ko‘rinish", self.toggle_view),
            ("settings", "Sozlamalar", self.open_menu),
        ]
        for name, text, callback in buttons:
            group = BoxLayout(orientation="vertical", spacing=0)
            img = icon_button(name, callback, 36)
            holder = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=dp(39))
            holder.add_widget(img)
            group.add_widget(holder)
            group.add_widget(label(text, 10, PURPLE if ((name=="notes" and not self.favorites_only) or (name=="star" and self.favorites_only)) else MUTED,
                                   height=24, halign="center"))
            nav.add_widget(group)
        return nav

    def reset_main(self):
        self.favorites_only = False
        self.category_filter = None
        self.show_main()

    def show_favorites(self):
        self.favorites_only = True
        self.category_filter = None
        self.show_main()

    def toggle_favorite(self, identifier):
        self.db.favorite(identifier)
        self.populate_notes()

    def edit_note(self, identifier):
        old = self.db.get(identifier) if identifier else None
        self.active_id = identifier
        self.active_day = old["event_date"] if old else current_date()
        self.active_category = old["category"] if old else (self.category_filter or "Shaxsiy")
        self.main_screen = "editor"
        page = self.page()
        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(13))
        header.add_widget(icon_button("back", self.show_main, 40))
        header.add_widget(label("Qaydni tahrirlash" if old else "Qayd qo‘shish", 19, INK, True, 50))
        header.add_widget(icon_button("check", self.save_editor, 40))
        page.add_widget(header)

        title_top = BoxLayout(size_hint_y=None, height=dp(38))
        title_top.add_widget(label("Sarlavha", 13, INK, True, 38))
        self.date_text = clear_button(self.pretty_date(self.active_day) + "  ▾", self.pick_date,
                                       width=132, height=38, fg=PURPLE, size=12)
        title_top.add_widget(self.date_text)
        page.add_widget(title_top)
        self.title_input = TextInput(text=old["title"] if old else "", multiline=False,
                                     hint_text="Qayd sarlavhasini kiriting",
                                     font_size=sp(13), size_hint_y=None, height=dp(49),
                                     foreground_color=INK, cursor_color=PURPLE,
                                     background_color=SURFACE, padding=[dp(11), dp(13), dp(7), 0])
        page.add_widget(self.title_input)
        page.add_widget(label("Tavsif", 13, INK, True, 34))
        self.content_input = TextInput(text=old["content"] if old else "", multiline=True,
                                       hint_text="Fikrlaringiz, rejalaringiz va qaydlaringiz...",
                                       font_size=sp(14), foreground_color=INK,
                                       cursor_color=PURPLE, background_color=SURFACE,
                                       padding=[dp(12), dp(17), dp(12), dp(12)])
        page.add_widget(self.content_input)
        page.add_widget(label("Toifa", 12, INK, True, 29))
        self.category_buttons = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        page.add_widget(self.category_buttons)
        self.refresh_categories()
        tools = BoxLayout(size_hint_y=None, height=dp(61), spacing=dp(8))
        tools.add_widget(clear_button("☑ Ro‘yxat", self.insert_checklist, size=12, fg=PURPLE))
        tools.add_widget(clear_button("▣ Kalendar", self.pick_date, size=12, fg=PURPLE))
        if identifier:
            tools.add_widget(clear_button("O‘chirish", lambda: self.ask_delete(identifier, editor=True), size=12, fg=(.76,.23,.32,1)))
        else:
            tools.add_widget(clear_button("Tozalash", self.clear_editor, size=12, fg=MUTED))
        page.add_widget(tools)

    def refresh_categories(self):
        self.category_buttons.clear_widgets()
        for cat in CATEGORIES:
            chosen = cat == self.active_category
            self.category_buttons.add_widget(
                pill_button(cat, lambda c=cat: self.set_editor_category(c),
                            bg=PURPLE if chosen else (.88, .87, .94, 1),
                            fg=SURFACE if chosen else INK, height=40))

    def set_editor_category(self, cat):
        self.active_category = cat
        self.refresh_categories()

    def insert_checklist(self):
        self.content_input.insert_text("\n☐ " if self.content_input.text.strip() else "☐ ")
        self.content_input.focus = True

    def clear_editor(self):
        self.title_input.text = ""
        self.content_input.text = ""

    def save_editor(self):
        title = self.title_input.text
        content = self.content_input.text
        try:
            if self.active_id:
                if not self.db.update(self.active_id, title, content,
                                      event_date=self.active_day, category=self.active_category):
                    raise ValueError("Qayd topilmadi.")
            else:
                self.db.create(title, content, event_date=self.active_day,
                               category=self.active_category)
        except Exception as err:
            self.message("Saqlab bo‘lmadi", str(err))
            return
        self.show_main()

    def pick_date(self):
        current = date.fromisoformat(self.active_day)
        year, month = current.year, current.month
        container = RoundedBox(orientation="vertical", padding=dp(13), spacing=dp(7))
        popup = Popup(title="Qayd sanasini tanlash", content=container, size_hint=(.92, None),
                      height=dp(420), auto_dismiss=True)
        top = BoxLayout(size_hint_y=None, height=dp(39))
        container.add_widget(top)
        days_grid = GridLayout(cols=7, spacing=dp(2), size_hint_y=1)
        container.add_widget(days_grid)

        def render():
            top.clear_widgets()
            top.add_widget(clear_button("‹", lambda: move(-1), width=44, size=24))
            top.add_widget(label(f"{MONTHS[month-1]} {year}", 16, INK, True, 39, "center"))
            top.add_widget(clear_button("›", lambda: move(1), width=44, size=24))
            days_grid.clear_widgets()
            for text in ("Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"):
                days_grid.add_widget(label(text, 11, MUTED, True, 30, "center"))
            for week in calendar.Calendar(firstweekday=0).monthdayscalendar(year, month):
                for day in week:
                    if day:
                        b = clear_button(str(day), lambda d=day: choose(d), size=13,
                                         fg=PURPLE if f"{year:04d}-{month:02d}-{day:02d}" == self.active_day else INK)
                        days_grid.add_widget(b)
                    else:
                        days_grid.add_widget(Label(text=""))

        def move(delta):
            nonlocal year, month
            month += delta
            if month < 1:
                year -= 1
                month = 12
            elif month > 12:
                year += 1
                month = 1
            render()

        def choose(day):
            self.active_day = validate_date(f"{year:04d}-{month:02d}-{day:02d}")
            self.date_text.text = self.pretty_date(self.active_day) + "  ▾"
            popup.dismiss()

        render()
        popup.open()

    def ask_delete(self, identifier, editor=False):
        note = self.db.get(identifier)
        if not note:
            self.message("Qayd topilmadi", "Ushbu qayd o‘chirib yuborilgan.")
            return
        box = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(15))
        box.add_widget(label(f"«{note['title']}» qaydi butunlay o‘chirilsinmi?", 14, INK, height=92, halign="center"))
        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        pop = Popup(title="O‘chirishni tasdiqlang", content=box,
                    size_hint=(.93, None), height=dp(235))
        buttons.add_widget(pill_button("Bekor qilish", pop.dismiss, bg=(.86,.85,.91,1), fg=INK))
        def remove():
            self.db.delete(identifier)
            pop.dismiss()
            self.show_main() if editor else self.populate_notes()
        buttons.add_widget(pill_button("Butunlay o‘chirish", remove, bg=(.80,.26,.35,1)))
        box.add_widget(buttons)
        pop.open()

    def message(self, title, content):
        box = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(14))
        box.add_widget(label(content, 13, INK, height=82, halign="center"))
        pop = Popup(title=title, content=box, size_hint=(.89, None), height=dp(210))
        box.add_widget(pill_button("Yopish", pop.dismiss))
        pop.open()

    def open_menu(self):
        box = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10))
        pop = Popup(title="Sozlamalar", content=box, size_hint=(.91, None), height=dp(440))
        def do(action):
            pop.dismiss()
            action()
        box.add_widget(pill_button("Qayd sanasi bo‘yicha saralash", lambda: do(lambda: self.set_sort("date"))))
        box.add_widget(pill_button("Sarlavha bo‘yicha saralash", lambda: do(lambda: self.set_sort("title")), bg=(.80,.76,.92,1), fg=INK))
        box.add_widget(pill_button("JSON zaxira nusxasi", lambda: do(self.export_backup), bg=(.80,.76,.92,1), fg=INK))
        box.add_widget(pill_button("Oxirgi zaxiradan tiklash", lambda: do(self.import_last_backup), bg=(.80,.76,.92,1), fg=INK))
        box.add_widget(label("Muallif: Mingqulova Rayhona  •  v1.0", 12, MUTED, height=34, halign="center"))
        box.add_widget(clear_button("Yopish", pop.dismiss, fg=PURPLE))
        pop.open()

    def set_sort(self, mode):
        self.sort_mode = mode
        self.show_main()

    def backup_dir(self):
        folder = Path(self.user_data_dir) / "backups"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def export_backup(self):
        from datetime import datetime
        target = self.backup_dir() / f"eslatmalar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            num = self.db.export_json(target)
            self.message("Zaxira saqlandi", f"{num} ta qayd saqlandi. Fayl: {target.name} (ilova ma’lumotlari papkasida)")
        except Exception as err:
            self.message("Xatolik", str(err))

    def import_last_backup(self):
        files = sorted(self.backup_dir().glob("eslatmalar_*.json"), reverse=True)
        if not files:
            self.message("Zaxira topilmadi", "Avval JSON zaxira nusxasini yarating.")
            return
        try:
            count, skipped = self.db.import_json(files[0])
            self.show_main()
            self.message("Zaxira tiklandi", f"{count} ta qo‘shildi, {skipped} ta mavjud edi.")
        except Exception as err:
            self.message("Tiklashda xatolik", str(err))


if __name__ == "__main__":
    EslatmalarApp().run()
