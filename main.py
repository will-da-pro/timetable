#!/usr/bin/env python

import json
import re
import curses
from curses import panel
from abc import ABC, abstractmethod
import glob

# Time regex
# ^([0-1][0-9]|2[0-3]):[0-5][0-9]$

# Color regex
# ^#(?:[0-9a-fA-F]{3}){1,2}$


class ExitCurses(Exception):
    def __init__(self, message: str):
        self.message: str = message

    def __str__(self):
        return self.message


class Subject:
    def __init__(self, id: str, name: str, teacher: str) -> None:
        self.id: str = id
        self.name: str = name
        self.teacher: str = teacher

    def __str__(self) -> str:
        return f"Period Type - name: {self.name}, teacher: {self.teacher}"


class Period:
    def __init__(self, period_type: Subject, room: str) -> None:
        self.period_type: Subject = period_type
        self.room: str = room

    def __str__(self) -> str:
        return f"{self.period_type}; Period - room: {self.room}"


class PeriodTimeStruct:
    def __init__(self, name: str, start_time: str, end_time: str) -> None:
        self.name = name
        self.start_time = start_time
        self.end_time = end_time


class TimeTable:
    def __init__(self, periods: dict[int, dict[str, Period]], 
                 subjects: dict[str, Subject], 
                 period_times: dict[str, PeriodTimeStruct], 
                 name: str) -> None:

        self.periods: dict[int, dict[str, Period]] = periods
        self.subjects: dict[str, Subject] = subjects
        self.period_times: dict = period_times
        self.name: str = name

    def save_file(self, filename: str) -> None:
        pass


class ContentWindow(ABC):
    def __init__(self, width: int, height: int, x_pos: int, y_pos: int, parent: curses.window) -> None:
        self.width: int = width
        self.height: int = height
        self.x_pos: int = x_pos
        self.y_pos: int = y_pos

        self.border_window = parent.subwin(height, width, self.y_pos, self.x_pos)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        self.border_window.refresh()

        self.window = parent.subwin(height - 2, width - 2, self.y_pos + 1, self.x_pos + 1)
        self.window.bkgd(' ', curses.color_pair(1))

    @abstractmethod
    def display(self) -> None:
        pass


class PeriodWindow(ContentWindow):
    def __init__(self, period: Period, width: int, height: int, x_pos: int, y_pos: int, parent: curses.window) -> None:
        super().__init__(width, height, x_pos, y_pos, parent)
        self.period = period

    def display(self) -> None:
        self.window.erase()
        self.window.addstr(0, 1, self.period.period_type.name)
        self.window.addstr(1, 1, self.period.period_type.teacher)
        self.window.addstr(2, 1, self.period.room)
        self.window.refresh()


class PeriodTimeWindow(ContentWindow):
    def __init__(self, period_times: PeriodTimeStruct, width: int, height: int, x_pos: int, y_pos: int, parent: curses.window) -> None:
        super().__init__(width, height, x_pos, y_pos, parent)
        self.period_times = period_times

    def display(self) -> None:
        self.window.erase()
        self.window.addstr(0, 1, self.period_times.name)
        self.window.addstr(1, 1, self.period_times.start_time)
        self.window.addstr(2, 1, self.period_times.end_time)
        self.window.refresh()


class Menu(object):
    def __init__(self, title: str, stdscreen, width: int = 150, height: int = 40) -> None:
        self.width = width
        self.height = height

        self.x_pos: int = (curses.COLS - width) // 2
        self.y_pos: int = (curses.LINES - height) // 2

        self.title = title

        self.shadow_window = stdscreen.subwin(height + 2, width + 2, self.y_pos, self.x_pos)
        self.shadow_window.bkgd(' ', curses.color_pair(3))
        self.shadow_window.refresh()

        self.border_window = stdscreen.subwin(height + 2, width + 2, self.y_pos - 1, self.x_pos - 1)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        header: str = "TIMETABLE APP"
        self.border_window.addch(0, (self.width - len(header)) // 2 - 1, "┤")
        self.border_window.addch(0, (self.width + len(header)) // 2 + 2, "├")
        self.border_window.addstr(0 , (self.width - len(header)) // 2, f" {header} ", curses.color_pair(4))
        self.border_window.refresh()

        self.window = stdscreen.subwin(height, width, self.y_pos, self.x_pos)
        self.window.keypad(1)
        self.window.bkgd(' ', curses.color_pair(1))

    def display(self):
        pass


class ListMenu(Menu):
    def __init__(self, title: str, items, stdscreen):
        super().__init__(title, stdscreen)

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
                        self.panel.hide()
                        self.items[self.position][1](*self.items[self.position][2:])

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


class TimetableViewMenu(Menu):
    def __init__(self, timetable: TimeTable, stdscreen):
        super().__init__(timetable.name, stdscreen)

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.timetable = timetable
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        period_windows: list[PeriodWindow] = []

        margin: int = 5
        side_info_width: int = margin * 3

        period_height: int = 5
        period_width: int = (self.width - side_info_width - 2 * margin) // 5

        for day_num, day in self.timetable.periods.items():
            for period_id, period in day.items():
                day_index = list(self.timetable.period_times.keys()).index(period_id)
                period_window: PeriodWindow = PeriodWindow(period, period_width, period_height,
                                                           self.x_pos + margin + day_num * period_width + side_info_width,
                                                           self.y_pos + margin + day_index * period_height,
                                                           self.window)

                period_windows.append(period_window)

        side_info_windows: list[PeriodTimeWindow] = []

        for index, period_data in enumerate(self.timetable.period_times.values()):
            period_time_window: PeriodTimeWindow = PeriodTimeWindow(period_data, side_info_width, period_height,
                                                                    self.x_pos + margin,
                                                                    self.y_pos + margin + index * period_height,
                                                                    self.window)

            side_info_windows.append(period_time_window)

        while True:
            self.window.addstr(0, 2, self.title)
            self.window.refresh()
            curses.doupdate()

            for period_window in period_windows:
                period_window.display()

            for period_time_window in side_info_windows:
                period_time_window.display()

            for i, day in enumerate(self.days):
                self.window.addstr(margin - 2, margin + i * period_width + side_info_width + 2, day, curses.color_pair(4))

            key = self.window.getch()
            if key == 113 or key == 81:
                raise ExitCurses("Exiting")
            elif key == 27:
                break

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


class App:
    def __init__(self, stdscreen: curses.window) -> None:
        self.current_timetable: TimeTable | None = None
        self.load_file("data/test1.json")

        self.screen = stdscreen
        curses.curs_set(0)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)

        stdscreen.bkgd(' ', curses.color_pair(2))

        files = glob.glob("data/*.json")
        file_items = []
        for file in files:
            file_items.append((file, self.open_file, file))

        if len(file_items) == 0:
            file_items.append(
                ("No files found! Are you sure they are in the correct directory? (data/name.json)", curses.beep))

        files_menu = ListMenu("Select a file to open", file_items, self.screen)

        main_menu_items = [
            ("Open Existing", files_menu.display),
            ("Create New", curses.beep),
        ]
        main_menu = ListMenu("Open an existing timetable or create a new one", main_menu_items, self.screen)
        main_menu.display()

    def open_file(self, filename: str) -> None:
        self.load_file(filename)
        if self.current_timetable is not None:
            timetable_view = TimetableViewMenu(self.current_timetable, self.screen)
            timetable_view.display()

    def load_file(self, filename: str) -> None:
        with open(filename) as f:
            json_data: dict | None = json.load(f)

        if json_data is None:
            return

        #print("JSON found")

        try:
            timetable_raw: list[dict] = json_data["timetable"]
            subjects_raw: dict = json_data["subjects"]
            period_times_raw = json_data["period_times"]
            timetable_name: str = json_data["name"]
        except KeyError:
            print("Invalid configuration (Missing Data)")
            return
    

        subjects: dict[str, Subject] = {}
        for subject_id, subject_raw in subjects_raw.items():
            name: str | None = subject_raw.get("name")
            teacher: str | None = subject_raw.get("teacher")

            if name is None or teacher is None:
                return

            subjects[subject_id] = Subject(subject_id, name, teacher)


        periods: dict[int, dict[str, Period]] = {}
        for i, day in enumerate(timetable_raw):
            periods[i] = {}
            for period_id, val in day.items():
                subject: Subject | None = subjects.get(val.get("subject"))
                room: str | None = val.get("room")
 
                if subject is None or room is None:
                    #print("Invalid subject name")
                    return

                period: Period = Period(subject, room)

                periods[i][period_id] = period


        period_times: dict[str, PeriodTimeStruct] = {}
        for period_num, period_time_data in period_times_raw.items():
            name: str | None = period_time_data.get("name")
            start_time: str | None = period_time_data.get("start")
            end_time: str | None = period_time_data.get("end")

            if name is None or start_time is None or end_time is None:
                return

            period_time_struct = PeriodTimeStruct(name, start_time, end_time)
            period_times[period_num] = period_time_struct


        self.current_timetable = TimeTable(periods, subjects, period_times, timetable_name)
        
        #print(f"Timetable at {filename} successfully loaded")


if __name__ == "__main__":
    try:
        curses.wrapper(App)
    except ExitCurses as e:
        print(e)
