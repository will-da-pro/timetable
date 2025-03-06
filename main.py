#!/usr/bin/env python

import json
import re
import curses
from curses import wrapper, panel
from abc import ABC, abstractmethod
import glob

# Time regex
# ^([0-1][0-9]|2[0-3]):[0-5][0-9]$

# Color regex
# ^#(?:[0-9a-fA-F]{3}){1,2}$

class Menu(object):
    def __init__(self, title: str, items, stdscreen):
        width = 150
        height = 40

        x_pos = (curses.COLS - width) // 2
        y_pos = (curses.LINES - height) // 2

        self.title = title

        self.shadow_window = stdscreen.subwin(height + 2, width + 2, y_pos, x_pos)
        self.shadow_window.bkgd(' ', curses.color_pair(3))
        self.shadow_window.refresh()

        self.border_window = stdscreen.subwin(height + 2, width + 2, y_pos - 1, x_pos - 1)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        self.border_window.addstr(0, 3, " Timetable App ")
        self.border_window.refresh()

        self.window = stdscreen.subwin(height, width, y_pos, x_pos)
        self.window.keypad(1)
        self.window.bkgd(' ', curses.color_pair(1))

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.items = items
        self.items.append(("exit", "exit"))

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.addstr(0, 2, self.title)
            self.window.refresh()
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = "%d. %s" % (index, item[0])
                self.window.addstr(2 + index, 1, msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    break
                else:
                    if len(self.items[self.position]) <= 2:
                        self.items[self.position][1]()
                    else:
                        self.items[self.position][1](self.items[self.position][2])

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


class Window(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def render(self) -> None:
        pass

    @abstractmethod
    def hide(self) -> None:
        pass

    @abstractmethod
    def __del__(self) -> None:
        pass


class ContentWindow(Window):
    def __init__(self) -> None:
        super().__init__()


class TimetableViewWindow(ContentWindow):
    def __init__(self) -> None:
        super().__init__()


class TimetableEditWindow(ContentWindow):
    def __init__(self) -> None:
        super().__init__()


class PeriodWindow(ContentWindow):
    def __init__(self) -> None:
        super().__init__()


class PeriodInfoWindow(ContentWindow):
    def __init__(self) -> None:
        super().__init__()


class MainWindowFactory():
    def __init__(self) -> None:
        pass


class Subject:
    def __init__(self, id: str, name: str, teacher: str | None, color: str = "#FFFFFF") -> None:
        self.id: str = id
        self.name: str = name
        self.teacher: str | None = teacher
        self.color: str = color

    def __str__(self) -> str:
        return f"Period Type - name: {self.name}, teacher: {self.teacher}, color: {self.color}"


class Period:
    def __init__(self, period_type: Subject, room: str | None) -> None:
        self.period_type: Subject = period_type
        self.room: str | None = room

    def render(self, x_pos, y_pos) -> None:
        pass

    def __str__(self) -> str:
        return f"{self.period_type}; Period - room: {self.room}"


class TimeTable:
    def __init__(self, periods: dict[int, dict[str, Period]], subjects: dict[str, Subject], period_data: dict, name: str) -> None:
        self.periods: dict[int, dict[str, Period]] = periods
        self.subjects: dict[str, Subject] = subjects
        self.period_data: dict = period_data
        self.name: str = name

    def save_file(self, filename: str) -> None:
        pass

    def render(self) -> None:

        for i, day in self.periods.items():
            for j, period in day.items():
                period.render(i, list(self.period_data.keys()).index(j))


class App:
    def __init__(self, stdscreen) -> None:
        self.current_timetable: TimeTable | None = None
        self.load_file("data/test1.json")

        self.screen = stdscreen
        curses.curs_set(0)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

        stdscreen.bkgd(' ', curses.color_pair(2))

        files = glob.glob("data/*.json")
        file_items = []
        for file in files:
            file_items.append((file, self.load_file, file))

        if len(file_items) == 0:
            file_items.append(
                ("No files found! Are you sure they are in the correct directory? (data/name.json)", curses.beep))

        files_menu = Menu("Select a file to open", file_items, self.screen)

        main_menu_items = [
            ("Open Existing", files_menu.display),
            ("Create New", curses.beep),
        ]
        main_menu = Menu("Open an existing timetable or create a new one", main_menu_items, self.screen)
        main_menu.display()

    def load_file(self, filename: str) -> None:
        json_data: dict | None = None
        with open(filename) as f:
            json_data = json.load(f)

        if json_data is None:
            return

        print("JSON found")

        try:
            timetable_raw: list[dict] = json_data["timetable"]
            subjects_raw: dict = json_data["subjects"]
            period_data = json_data["period_data"]
            timetable_name: str = json_data["name"]
        except:
            print("Invalid configuration (Missing Data)")
            return
    

        subjects: dict[str, Subject] = {}
        for id, subject_raw in subjects_raw.items():
            name: str = subject_raw.get("name")
            teacher: str | None = subject_raw.get("teacher")
            color: str = subject_raw.get("accent_color")
            subjects[id] = Subject(id, name, teacher, color)


        periods: dict[int, dict[str, Period]] = {}
        for i, day in enumerate(timetable_raw):
            periods[i] = {}
            for period_id, val in day.items():
                subject: Subject | None = subjects.get(val.get("subject"))
                room: str | None = val.get("room")
 
                if subject is None:
                    print("Invalid subject name")
                    return

                period: Period = Period(subject, room)

                periods[i][period_id] = period

        self.current_timetable = TimeTable(periods, subjects, period_data, timetable_name)
        
        print(f"Timetable at {filename} successfully loaded")


if __name__ == "__main__":
    curses.wrapper(App)
