#!/usr/bin/env python

import json
# import re
import curses
from curses import panel
from abc import ABC, abstractmethod
import glob

# Time regex
# ^([0-1][0-9]|2[0-3]):[0-5][0-9]$

# Color regex
# ^#(?:[0-9a-fA-F]{3}){1,2}$

# Exception Handling


class ExitCurses(Exception):
    """
    Allows for the exiting of the curses window gracefully.
    """

    def __init__(self, message: str):
        self.message: str = message


class InvalidDataException(Exception):
    """
    Raised when an invalid JSON data is encountered.
    """

    def __init__(self, message: str):
        self.message: str = message


class Subject:
    """
    Class for each unique subject.

    e.g. Maths, English, Science, etc.
    """

    def __init__(self, subject_id: str, name: str, teacher: str) -> None:
        """
        Initializes a Subject object.

        :param str subject_id: ID of the subject.
        :param str name: Name of the subject.
        :param str teacher: Teacher of the subject.
        """

        self.subject_id: str = subject_id
        self.name: str = name
        self.teacher: str = teacher

    def __str__(self) -> str:
        return f"Period Type - name: {self.name}, teacher: {self.teacher}"


class Period:
    """
    Class for a period during the day, has a subject and room.

    Created for every period time on every day.
    """

    def __init__(self, subject: Subject, room: str) -> None:
        """
        Initializes a Period object.

        :param subject: Subject of the period.
        :param room: Room of the period.
        """

        self.subject: Subject = subject
        self.room: str = room

    def __str__(self) -> str:
        return f"{self.subject}; Period - room: {self.room}"


class PeriodTimeStruct:
    """
    Class for defining period times and names.

    e.g. Period 0, start at 0800, end at 0845.
    """

    def __init__(self, name: str, start_time: str, end_time: str) -> None:
        """
        Initializes a PeriodTimeStruct object.

        :param name: The name of the period, e.g. Period 0.
        :param start_time: The time at which the period starts, in HHMM format, 24h time.
        :param end_time: The time at which the period ends, in HHMM format, 24h time.
        """
        self.name = name
        self.start_time = start_time
        self.end_time = end_time


class TimeTable:
    """
    Class for an entire timetable object

    Includes:

    An array containing a dictionary of periods for each day

    A dictionary of all subjects

    A dictionary of all period times
    """
    def __init__(self, periods: dict[int, dict[str, Period]], 
                 subjects: dict[str, Subject], 
                 period_times: dict[str, PeriodTimeStruct], 
                 name: str,
                 filename: str) -> None:
        """
        Initializes a TimeTable object.

        :param periods: A dictionary of periods for each day.
        :param subjects: A dictionary of all subjects.
        :param period_times: A dictionary of all period times.
        :param name: The name of the timetable.
        :param filename: The filename of the timetable.
        """

        self.periods: dict[int, dict[str, Period]] = periods
        self.subjects: dict[str, Subject] = subjects
        self.period_times: dict[str, PeriodTimeStruct] = period_times
        self.name: str = name
        self.filename: str = filename

    def save_file(self) -> None:
        """
        Saves the timetable to a file.

        :return: None
        """

        json_data: dict = {}

        # The raw Python data structures consisting of dictionaries and lists, that will get turned into JSON
        timetable_raw: list[dict[str, dict[str, str]]] = []
        subjects_raw: dict[str, dict[str, str]] = {}
        period_times_raw: dict[str, dict[str, str]] = {}

        # Converts all periods into Python dicts
        for day_index, day in self.periods.items():
            day_data: dict[str, dict[str, str]] = {}

            for period_index, period in day.items():
                subject_id: str = period.subject.subject_id
                room: str = period.room

                day_data[period_index] = {"subject": subject_id, "room": room}

            timetable_raw.append(day_data)

        # Converts all subjects into Python dicts
        for subject_index, subject in self.subjects.items():
            name: str = subject.name
            teacher: str = subject.teacher

            subjects_raw[subject_index] = {"name": name, "teacher": teacher}

        # Converts all period times into Python dicts
        for period_times_index, period_times in self.period_times.items():
            name: str = period_times.name
            start_time: str = period_times.start_time
            end_time: str = period_times.end_time

            period_times_raw[period_times_index] = {"name": name, "start": start_time, "end": end_time}

        json_data["name"] = self.name
        json_data["timetable"] = timetable_raw
        json_data["subjects"] = subjects_raw
        json_data["period_times"] = period_times_raw

        json_object = json.dumps(json_data, indent=4)

        with open(self.filename, "w") as outfile:
            outfile.write(json_object)


class ContentWindow(ABC):
    def __init__(self, width: int, height: int,
                 x_pos: int, y_pos: int,
                 parent: curses.window) -> None:

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
    def __init__(self, period: Period,
                 width: int, height: int,
                 x_pos: int, y_pos: int,
                 parent: curses.window) -> None:

        super().__init__(width, height, x_pos, y_pos, parent)
        self.period: Period = period

    def display(self) -> None:
        self.window.erase()
        self.window.addstr(0, 1, self.period.subject.name)
        self.window.addstr(1, 1, self.period.subject.teacher)
        self.window.addstr(2, 1, self.period.room)
        self.window.refresh()


class PeriodTimeWindow(ContentWindow):
    def __init__(self, period_times: PeriodTimeStruct,
                 width: int, height: int,
                 x_pos: int, y_pos: int,
                 parent: curses.window) -> None:

        super().__init__(width, height, x_pos, y_pos, parent)
        self.period_times = period_times

    def display(self) -> None:
        self.window.erase()
        self.window.addstr(0, 1, self.period_times.name)
        self.window.addstr(1, 1, self.period_times.start_time)
        self.window.addstr(2, 1, self.period_times.end_time)
        self.window.refresh()


class Menu(ABC):
    def __init__(self, title: str, stdscreen,
                 width: int = 150, height: int = 40) -> None:
        self.width = width
        self.height = height

        self.x_pos: int = (curses.COLS - width) // 2
        self.y_pos: int = (curses.LINES - height) // 2

        self.title = title

        self.stdscreen = stdscreen

        self.shadow_window = stdscreen.subwin(height + 2, width + 2, self.y_pos, self.x_pos)
        self.shadow_window.bkgd(' ', curses.color_pair(3))
        self.shadow_window.refresh()

        self.border_window = stdscreen.subwin(height + 2, width + 2, self.y_pos - 1, self.x_pos - 1)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        header: str = "TIMETABLE APP"
        self.border_window.addch(0, (self.width - len(header)) // 2 - 1, "┤")
        self.border_window.addch(0, (self.width + len(header)) // 2 + 2, "├")
        self.border_window.addstr(0, (self.width - len(header)) // 2, f" {header} ", curses.color_pair(4))
        self.border_window.refresh()

        self.window = stdscreen.subwin(height, width, self.y_pos, self.x_pos)
        self.window.keypad(1)
        self.window.bkgd(' ', curses.color_pair(1))

    @abstractmethod
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


class TimetableMenu(Menu):
    def __init__(self, timetable: TimeTable, stdscreen) -> None:
        super().__init__(timetable.name, stdscreen)

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.timetable = timetable
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.shortcut_info = ""

        self.period_windows: list[PeriodWindow] = []
        self.side_info_windows: list[PeriodTimeWindow] = []

        self.margin: int = 5
        self.side_info_width: int = self.margin * 3

        self.period_height: int = 5
        self.period_width: int = (self.width - self.side_info_width - 2 * self.margin) // 5

    def create_period_windows(self) -> None:
        for day_num, day in self.timetable.periods.items():
            for period_id, period in day.items():
                day_index = list(self.timetable.period_times.keys()).index(period_id)
                period_window: PeriodWindow = PeriodWindow(period, self.period_width, self.period_height,
                                                           self.x_pos + self.margin +
                                                           day_num * self.period_width + self.side_info_width,
                                                           self.y_pos + self.margin + day_index * self.period_height,
                                                           self.window)

                self.period_windows.append(period_window)

    def create_side_info_windows(self) -> None:
        for index, period_data in enumerate(self.timetable.period_times.values()):
            period_time_window: PeriodTimeWindow = PeriodTimeWindow(period_data, self.side_info_width, self.period_height,
                                                                    self.x_pos + self.margin,
                                                                    self.y_pos + self.margin + index * self.period_height,
                                                                    self.window)

            self.side_info_windows.append(period_time_window)

    def render_timetable(self) -> None:
        self.window.addstr(0, 2, self.title)
        self.window.addstr(self.height - 1, 2, self.shortcut_info)
        self.window.refresh()
        curses.doupdate()

        for period_window in self.period_windows:
            period_window.display()

        for period_time_window in self.side_info_windows:
            period_time_window.display()

        for i, day in enumerate(self.days):
            self.window.addstr(self.margin - 2, self.margin + i * self.period_width + self.side_info_width + 2,
                               day,
                               curses.color_pair(4))

    @abstractmethod
    def display(self) -> None:
        pass


class TimetableEditMenu(TimetableMenu):
    def __init__(self, timetable: TimeTable, stdscreen) -> None:
        super().__init__(timetable, stdscreen)

        self.shortcut_info = "Shortcuts: [q] Quit, [s] Save and Exit"
        self.title = f"{self.timetable.name} (editing)"

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        self.create_period_windows()
        self.create_side_info_windows()

        while True:
            self.render_timetable()

            key = self.window.getch()
            # 'Q' and 'q'
            if key == 113 or key == 81:
                raise ExitCurses("Exiting")

            elif key == 115 or key == 83:
                curses.beep()


class TimetableViewMenu(TimetableMenu):
    def __init__(self, timetable: TimeTable, stdscreen):
        super().__init__(timetable, stdscreen)

        self.shortcut_info = "Shortcuts: [e] Edit, [esc] Back, [q] Quit"

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        self.create_period_windows()
        self.create_side_info_windows()

        key: str | None = None

        # Escape key ascii value
        while key != 27:
            self.render_timetable()

            key = self.window.getch()
            # 'Q' and 'q'
            if key == 113 or key == 81:
                raise ExitCurses("Exiting")

            elif key == 101 or key == 69:
                TimetableEditMenu(self.timetable, self.stdscreen).display()

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


class App:
    def __init__(self, stdscreen: curses.window) -> None:
        self.current_timetable: TimeTable | None = None

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
            try:
                json_data: dict | None = json.load(f)
            except json.decoder.JSONDecodeError:
                raise InvalidDataException("Invalid JSON")

        if json_data is None:
            raise InvalidDataException("No data found!")

        try:
            timetable_name: str = json_data["name"]
            timetable_raw: list[dict[str, dict[str, str]]] = json_data["timetable"]
            subjects_raw: dict[str, dict[str, str]] = json_data["subjects"]
            period_times_raw: dict[str, dict[str, str]] = json_data["period_times"]
        except KeyError:
            print("Invalid configuration (Missing Data)")
            raise InvalidDataException("Data field not found")

        subjects: dict[str, Subject] = {}
        for subject_id, subject_raw in subjects_raw.items():
            name: str | None = subject_raw.get("name")
            teacher: str | None = subject_raw.get("teacher")

            if name is None or teacher is None:
                raise InvalidDataException(f"{subject_id} has no name or teacher")

            subjects[subject_id] = Subject(subject_id, name, teacher)

        periods: dict[int, dict[str, Period]] = {}
        for i, day in enumerate(timetable_raw):
            periods[i] = {}
            for period_id, val in day.items():
                subject: Subject | None = subjects.get(val.get("subject"))
                room: str | None = val.get("room")
 
                if subject is None or room is None:
                    raise InvalidDataException(f"{period_id} has no subject or room for day {day}")

                period: Period = Period(subject, room)

                periods[i][period_id] = period

        period_times: dict[str, PeriodTimeStruct] = {}
        for period_num, period_time_data in period_times_raw.items():
            name: str | None = period_time_data.get("name")
            start_time: str | None = period_time_data.get("start")
            end_time: str | None = period_time_data.get("end")

            if name is None or start_time is None or end_time is None:
                raise InvalidDataException(f"Period {period_num} is missing data")

            period_time_struct = PeriodTimeStruct(name, start_time, end_time)
            period_times[period_num] = period_time_struct

        self.current_timetable = TimeTable(periods, subjects, period_times, timetable_name, filename)


if __name__ == "__main__":
    try:
        curses.wrapper(App)

    except ExitCurses as e:
        print(e)

    except InvalidDataException as e:
        print(e)
