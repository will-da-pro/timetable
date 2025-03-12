#!/usr/bin/env python

# Copyright 2025 William D'Olier

import json
# import re
import curses
from curses import panel
from abc import ABC, abstractmethod
import glob
from dataclasses import dataclass


# Time regex
# ^([0-1][0-9]|2[0-3])[0-5][0-9]$

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


# Data Structures

@dataclass
class Subject:
    """
    Class for each unique subject.

    e.g. Maths, English, Science, etc.
    """

    subject_id: str
    name: str
    teacher: str

    def __str__(self) -> str:
        return f"Period Type - name: {self.name}, teacher: {self.teacher}"


@dataclass
class Period:
    """
    Class for a period during the day, has a subject and room.

    Created for every period time on every day.
    """

    subject: Subject
    room: str

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
                 subjects: dict[str, Subject_t],
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
        self.subjects: dict[str, Subject_t] = subjects
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


# Windows


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
                 x_index: int, y_index: int,
                 parent: curses.window) -> None:

        super().__init__(width, height, x_pos, y_pos, parent)

        self.period: Period = period

        self.x_index: int = x_index
        self.y_index: int = y_index

    def display(self, selected: bool = False) -> None:
        self.window.erase()

        if selected:
            self.window.bkgd(' ', curses.color_pair(3))
            self.border_window.bkgd(' ', curses.color_pair(3))

        else:
            self.window.bkgd(' ', curses.color_pair(1))
            self.border_window.bkgd(' ', curses.color_pair(1))

        self.window.addstr(0, 1, self.period.subject.name)
        self.window.addstr(1, 1, self.period.subject.teacher)
        self.window.addstr(2, 1, self.period.room)
        self.window.refresh()

        self.border_window.border(0)
        self.border_window.refresh()


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

        self.border_window.border(0)
        self.border_window.refresh()


# Menus


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

        header: str = "TIMETABLE APP"

        self.border_window = stdscreen.subwin(height + 2, width + 2, self.y_pos - 1, self.x_pos - 1)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        self.border_window.addch(0, (self.width - len(header)) // 2 - 1, "┤")
        self.border_window.addch(0, (self.width + len(header)) // 2 + 2, "├")
        self.border_window.addstr(0, (self.width - len(header)) // 2, f" {header} ", curses.color_pair(4))
        self.border_window.refresh()

        self.window = stdscreen.subwin(height, width, self.y_pos, self.x_pos)
        self.window.keypad(1)
        self.window.bkgd(' ', curses.color_pair(1))

    def exit(self):
        self.window.clear()
        curses.doupdate()

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

        self.items.append(("Exit", "Exit"))

    def navigate(self, position_change) -> None:
        self.position += position_change

        if self.position < 0:
            self.position = 0

        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def exit(self):
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

    def display_items(self) -> None:
        self.window.clear()
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

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.display_items()

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    self.exit()
                    return

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


class TimetableMenu(Menu):
    def __init__(self, timetable: TimeTable, stdscreen) -> None:
        super().__init__(timetable.name, stdscreen)

        self.states: dict[int, str] = {
            -1: "Exiting",
            0: "Viewing",
            1: "Editing",
            2: "Editing Period",
            3: "Selecting Subject",
        }

        self.state: int = 0

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

        self.cell_x_count: int = 5
        self.cell_y_count: int = len(self.timetable.period_times)

        self.selected_period_x: int = 0
        self.selected_period_y: int = 0

        self.selected_period: Period | None = None

        self.selected_list_item: int = 0
        self.list_size: int = 0

    def create_period_windows(self) -> None:
        self.period_windows = []

        for day_num, day in self.timetable.periods.items():
            for period_id, period in day.items():
                day_index = list(self.timetable.period_times.keys()).index(period_id)

                window_x = self.x_pos + self.margin + day_num * self.period_width + self.side_info_width
                window_y = self.y_pos + self.margin + day_index * self.period_height

                period_window: PeriodWindow = PeriodWindow(period, self.period_width, self.period_height,
                                                           window_x, window_y,
                                                           day_num, day_index, self.window)

                self.period_windows.append(period_window)

    def create_side_info_windows(self) -> None:
        for index, period_data in enumerate(self.timetable.period_times.values()):
            window_x = self.x_pos + self.margin
            window_y = self.y_pos + self.margin + index * self.period_height

            period_time_window: PeriodTimeWindow = PeriodTimeWindow(period_data, self.side_info_width,
                                                                    self.period_height,
                                                                    window_x, window_y,
                                                                    self.window)

            self.side_info_windows.append(period_time_window)

    def render_timetable(self, **kwargs) -> None:
        self.window.clear()
        self.window.addstr(0, 2, self.title)
        self.window.addstr(self.height - 1, 2, self.shortcut_info)
        self.window.refresh()
        curses.doupdate()

        highlighted: tuple[int, int] | None = kwargs.get("highlighted")
        selection_found: bool = False

        for period_window in self.period_windows:
            if (highlighted is not None
                    and highlighted[0] == period_window.x_index
                    and highlighted[1] == period_window.y_index):

                period_window.display(True)
                selection_found = True

            else:
                period_window.display()

        if highlighted is not None and not selection_found:
            window_x = self.margin + highlighted[0] * self.period_width + self.side_info_width + 1
            window_y = self.margin + highlighted[1] * self.period_height + 1

            self.window.addstr(window_y, window_x, "<Add New>", curses.color_pair(3))

        for period_time_window in self.side_info_windows:
            period_time_window.display()

        for i, day in enumerate(self.days):
            self.window.addstr(self.margin - 2, self.margin + i * self.period_width + self.side_info_width + 2,
                               day,
                               curses.color_pair(4))

    def navigate_timetable(self, x_change: int, y_change: int) -> None:
        self.selected_period_x += x_change
        self.selected_period_y += y_change

        if self.selected_period_x < 0:
            self.selected_period_x = 0

        elif self.selected_period_x >= self.cell_x_count:
            self.selected_period_x = self.cell_x_count - 1

        if self.selected_period_y < 0:
            self.selected_period_y = 0

        elif self.selected_period_y >= self.cell_y_count:
            self.selected_period_y = self.cell_y_count - 1

    def navigate_list(self, change: int) -> None:
        self.selected_list_item += change

        if self.selected_list_item < 0:
            self.selected_list_item = 0

        elif self.selected_list_item >= self.list_size:
            self.selected_list_item = self.list_size - 1

    def process_input_viewing(self, key: int) -> None:
        if key == ord("e"):
            self.state = 1

    def process_input_editing(self, key: int):
        if key in [curses.KEY_ENTER, ord("\n")]:
            selected_period_id: str = list(self.timetable.period_times.keys())[self.selected_period_y]
            self.selected_period = self.timetable.periods[self.selected_period_x].get(selected_period_id)

            self.state = 2

        # Escape key
        elif key == 27:
            self.state = 0

        elif key == curses.KEY_UP:
            self.navigate_timetable(0, -1)

        elif key == curses.KEY_DOWN:
            self.navigate_timetable(0, 1)

        elif key == curses.KEY_LEFT:
            self.navigate_timetable(-1, 0)

        elif key == curses.KEY_RIGHT:
            self.navigate_timetable(1, 0)

    def process_input_editing_period(self, key: int) -> None:
        pass

    def process_input_selecting_subject(self, key: int) -> None:
        pass

    def process_input(self, key: int) -> None:
        if key in [ord('q'), ord('Q')]:
            raise ExitCurses("Exiting")

        elif key in [ord('s'), ord('S')]:
            self.timetable.save_file()
            raise ExitCurses("Saved, Exiting")

        else:
            if self.state == 0:
                self.process_input_viewing(key)

            elif self.state == 1:
                self.process_input_editing(key)

            elif self.state == 2:
                self.process_input_editing_period(key)

            elif self.state == 3:
                self.process_input_selecting_subject(key)

            else:
                raise ExitCurses("Invalid state")

    def display_viewing(self):
        pass

    def display_editing(self):
        pass

    def display_editing_period(self):
        pass

    def display_selecting_subject(self):
        pass

    def display(self) -> None:
        if self.state == -1:
            self.exit()
            return

        self.panel.top()
        self.panel.show()
        self.window.clear()

        self.create_period_windows()
        self.create_side_info_windows()

        while True:
            if self.state == 0:
                self.render_timetable()

            elif self.state == 1:
                self.render_timetable(highlighted=(self.selected_period_x, self.selected_period_y))

            key = self.window.getch()

            self.process_input(key)


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


class SubjectEditMenu(ListMenu):
    def __init__(self, subject: Subject | None, timetable_factory: TimeTableFactory, stdscreen):
        self.original_subject: Subject | None = subject
        self.subject: Subject | None = subject
        self.timetable_factory: TimeTableFactory = timetable_factory

        self.subject_id: str | None = None
        self.name: str | None = None
        self.teacher: str | None = None

        self.max_input_size = 20

        if self.original_subject is not None:
            self.subject_id = self.original_subject.subject_id
            self.name = self.original_subject.name
            self.teacher = self.original_subject.teacher

        else:
            self.subject_id = ""
            self.name = ""
            self.teacher = ""

        items: list[tuple] = [
            (f"Name: {self.name}", "name"),
            (f"Teacher: {self.teacher}", "teacher"),
            ("Delete", "Delete"),
            (f"Save and Exit", "save and exit"),
        ]

        super().__init__("Edit Subject", items, stdscreen)

    def refresh_items(self):
        items: list[tuple] = [
            (f"Name: {self.name}", "name"),
            (f"Teacher: {self.teacher}", "teacher"),
            ("Delete", "Delete"),
            (f"Save and Exit", "save and exit"),
            ("Exit", "Exit"),
        ]

        self.items = items

    def generate_subject(self) -> None:
        if len(self.subject_id) == 0 or len(self.name) == 0 or len(self.teacher) == 0:
            self.subject = None

        elif self.subject_id is not None and self.name is not None and self.teacher is not None:
            self.subject = Subject(self.subject_id, self.name, self.teacher)

        else:
            self.subject = None

    def process_input(self, key: int, current: str) -> str | None:
        if (ord('!') <= key <= ord('~') or key == ord(' ')) and len(current) < self.max_input_size:
            return current + chr(key)

        elif key in [curses.KEY_BACKSPACE, 127] and len(current) > 0:
            return current[:-1]

        return current

    def display(self) -> Subject | None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.display_items()

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == 4:
                    self.exit()

                    return self.original_subject

                elif self.position == 3:
                    self.exit()

                    self.generate_subject()

                    if self.subject is not None:
                        return self.subject

                    else:
                        curses.beep()

                elif self.position == 2:
                    self.exit()

                    return None

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

            else:
                if self.position == 0:
                    self.name = self.process_input(key, self.name)
                    self.subject_id = self.name.lower().replace(" ", "_")
                    self.refresh_items()

                elif self.position == 1:
                    self.teacher = self.process_input(key, self.teacher)
                    self.refresh_items()


class SubjectCreatorMenu(ListMenu):
    def __init__(self, timetable_factory: TimeTableFactory, stdscreen: curses.window) -> None:
        self.subjects: list[Subject_t] = []
        self.stdscreen: curses.window = stdscreen
        self.timetable_factory: TimeTableFactory = timetable_factory

        items: list[tuple] = [
            ("Create New", "create new"),
        ]

        super().__init__("Subject Creator", items, stdscreen)

    def refresh_items(self) -> None:
        items: list[tuple] = []

        for subject in self.subjects:
            items.append((f"{subject.name}", subject))

        items.append(("Create New", "create new"))
        items.append(("Exit", "Exit"))

        self.items = items

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.display_items()

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    self.exit()
                    return

                elif self.position == len(self.items) - 2:
                    subject_edit_menu = SubjectEditMenu(None, self.timetable_factory, self.stdscreen)
                    new_subject: Subject_t | None = subject_edit_menu.display()

                    if new_subject is not None:
                        self.subjects.append(new_subject)
                        self.refresh_items()

                else:
                    subject_edit_menu = SubjectEditMenu(self.subjects[self.position],
                                                        self.timetable_factory, self.stdscreen)

                    new_subject: Subject_t | None = subject_edit_menu.display()

                    if new_subject is not None:
                        self.subjects[self.position] = new_subject

                    self.refresh_items()

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)


class PeriodTimeSelectorMenu(ListMenu):
    def __init__(self, timetable_factory: TimeTableFactory, stdscreen: curses.window) -> None:
        self.timetable_factory: TimeTableFactory = timetable_factory
        self.stdscreen: curses.window = stdscreen

        self.max_input_size = 4

        self.input_buffer: list[list[str]] = []
        items: list[tuple] = []

        for i in range(timetable_factory.period_count):
            self.input_buffer.append(["", ""])
            items.append((f"Period {i}", i))
            items.append((f"Start Time: {self.input_buffer[i][0]}", i))
            items.append((f"End Time: {self.input_buffer[i][1]}", i))

        items.append(("Next", "next"))

        super().__init__("Enter Period Times", items, self.stdscreen)

    def refresh_items(self) -> None:
        items: list[tuple] = []

        for i in range(self.timetable_factory.period_count):
            self.input_buffer.append(["", ""])
            items.append((f"Period {i}", i))
            items.append((f"Start Time: {self.input_buffer[i][0]}", i))
            items.append((f"End Time: {self.input_buffer[i][1]}", i))

        items.append(("Next", "next"))
        items.append(("Exit", "Exit"))

        self.items = items

    def process_input(self, key: int, current: str) -> str:
        if ord('0') <= key <= ord('9') and len(current) < self.max_input_size:
            return current + chr(key)

        elif key in [curses.KEY_BACKSPACE, 127] and len(current) > 0:
            return current[:-1]

        return current

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.display_items()

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    self.exit()
                    return

                elif self.position == len(self.items) - 2:
                    curses.beep()

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

            else:
                if self.position % 3 == 0:
                    pass

                else:
                    index: int = self.position // 3

                    new_time = self.process_input(key, self.input_buffer[index][self.position % 3 - 1])
                    self.input_buffer[index][self.position % 3 - 1] = new_time
                    self.refresh_items()


class App:
    def __init__(self, stdscreen: curses.window) -> None:
        self.current_timetable: TimeTable | None = None

        self.screen = stdscreen
        curses.curs_set(0)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)

        stdscreen.bkgd(' ', curses.color_pair(2))

        files = glob.glob("data/*.json")
        file_items = []
        for file in files:
            file_items.append((file, self.open_file, file))

        if len(file_items) == 0:
            file_items.append(
                ("No files found! Are you sure they are in the correct directory? (data/[name].json)", curses.beep))

        files_menu = ListMenu("Select a file to open", file_items, self.screen)

        period_count_selector_menu: PeriodCountSelectorMenu = PeriodCountSelectorMenu(timetable_factory, stdscreen)

        main_menu_items = [
            ("Open Existing", files_menu.display),
            ("Create New", period_count_selector_menu.display),
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
        # Makes the terminal reset properly if it crashes for whatever reason
        # If this line is omitted, crashing will result in the curses windows remaining on the screen which is bad
        curses.wrapper(App)

    except ExitCurses as e:
        print(e)

    except InvalidDataException as e:
        print(e)
