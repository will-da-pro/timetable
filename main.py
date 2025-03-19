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
    Raised when invalid JSON data is encountered.
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


@dataclass
class PeriodTimeStruct:
    """
    Class for defining period times and names.

    e.g. Period 0, start at 0800, end at 0845.
    """

    name: str
    start_time: str
    end_time: str


class Timetable:
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
        Initializes a Timetable object.

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

        :return None:
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
    """
    Abstract class for a window with a border which displays content.
    """

    def __init__(self, width: int, height: int,
                 x_pos: int, y_pos: int,
                 parent) -> None:

        """
        Initializes a content window object.

        :param width: The width of the window.
        :param height: The height of the window.
        :param x_pos: The x position of the window, relative to the entire screen.
        :param y_pos: The y position of the window, relative to the entire screen.
        :param parent: The parent window object.
        """

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
        """
        Displays the content of the window.

        :return None:
        """

        pass


class PeriodWindow(ContentWindow):
    def __init__(self, period: Period,
                 width: int, height: int,
                 x_pos: int, y_pos: int,
                 x_index: int, y_index: int,
                 parent) -> None:

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
                 parent) -> None:

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
    """
    Class for all major menus.

    Creates a border window, shadow window and main window for rendering content.
    """
    def __init__(self, title: str, stdscreen: curses.window,
                 width: int = 150, height: int = 40) -> None:
        """
        Initializes a menu object.

        :param title: The title of the menu.
        :param stdscreen: The curses window to use.
        :param width: The width of the main window.
        :param height: The height of the main window.
        """
        self.width: int = width
        self.height: int = height

        self.x_pos: int = (curses.COLS - width) // 2
        self.y_pos: int = (curses.LINES - height) // 2

        self.title: str = title

        self.stdscreen: curses.window = stdscreen

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
        self.window.keypad(True)
        self.window.bkgd(' ', curses.color_pair(1))

        self.selected_list_item: int = 0
        self.list_size: int = 0

        self.list_items: list[tuple] = []

        self.editing: bool = False

    def display_list(self) -> None:
        for index, item in enumerate(self.list_items):
            if index == self.selected_list_item:
                self.window.addstr(index + 2, 1, f"{index + 1}. {item[0]}", curses.A_REVERSE)

            else:
                self.window.addstr(index + 2, 1, f"{index + 1}. {item[0]}")

    def navigate_list(self, change: int) -> None:
        self.selected_list_item += change

        if self.selected_list_item < 0:
            self.selected_list_item = 0

        elif self.selected_list_item >= self.list_size:
            self.selected_list_item = self.list_size - 1

        if self.list_items[self.selected_list_item][1] == "editor":
            self.editing = True

        else:
            self.editing = False

    def exit(self) -> None:
        """
        Used before exiting the menu, clears the window to prepare for exiting.

        :return None:
        """

        self.window.clear()
        curses.doupdate()

    @abstractmethod
    def display(self) -> None:
        """
        Method for displaying the contents of the menu.

        :return None:
        """

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

        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit"

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

            msg: str = f"{index}. {item[0]}"
            self.window.addstr(2 + index, 1, msg, mode)

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.display_items()
            self.window.addstr(self.height - 1, 2, self.shortcut_info)
            self.window.refresh()

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

            elif key == ord("q"):
                raise ExitCurses("Exiting")

            elif key == 27:
                self.exit()
                return

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)


class TimetableMenu(Menu):
    def __init__(self, timetable: Timetable, stdscreen: curses.window) -> None:
        """
        Creates a menu for rendering a timetable, with an editor.

        :param timetable: The timetable object to view.
        :param stdscreen: Curses screen to use.
        """

        super().__init__(timetable.name, stdscreen)

        self.states: dict[int, str] = {
            -1: "Exiting",
            0: "Viewing",
            1: "Editing",
            2: "Editing Period",
            3: "Selecting Subject"
        }

        self.state: int = 0

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.timetable = timetable
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable"

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
        self.selected_subject: Subject | None = None

        self.input_buffer: str = ""
        self.max_input_size: int = 20

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

    # Input Processing

    def process_input_viewing(self, key: int) -> None:
        if key == ord("e"):
            self.state = 1

        # Escape key
        elif key == 27:
            self.state = -1

    def process_input_editing(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            selected_period_id: str = list(self.timetable.period_times.keys())[self.selected_period_y]
            self.selected_period = self.timetable.periods[self.selected_period_x].get(selected_period_id)

            if self.selected_period is not None:
                self.selected_subject = self.selected_period.subject
                self.input_buffer = self.selected_period.room

            else:
                self.selected_subject = None
                self.input_buffer = ""

            self.selected_list_item = 0
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
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "subject":
                self.selected_list_item = 0

                self.state = 3

            elif self.list_items[self.selected_list_item][1] == "delete":
                period_id: str = list(self.timetable.period_times.keys())[self.selected_period_y]

                if self.timetable.periods[self.selected_period_x].get(period_id) is not None:
                    del self.timetable.periods[self.selected_period_x][period_id]

                self.create_period_windows()

                self.state = 1

            elif self.list_items[self.selected_list_item][1] == "save_exit":
                if self.selected_subject is not None:
                    period_id: str = list(self.timetable.period_times.keys())[self.selected_period_y]
                    new_period = Period(self.selected_subject, self.input_buffer)

                    self.timetable.periods[self.selected_period_x][period_id] = new_period

                    self.create_period_windows()

                    self.state = 1

                else:
                    curses.beep()

            elif self.list_items[self.selected_list_item][1] == "back":
                self.state = 1

        elif key == 27:
            self.state = 1
            self.editing = False

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

        elif self.list_items[self.selected_list_item][1] == "editor":
            if (ord('!') <= key <= ord('~') or key == ord(' ')) and len(self.input_buffer) < self.max_input_size:
                self.input_buffer += chr(key)

            elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer) > 0:
                self.input_buffer = self.input_buffer[:-1]

    def process_input_selecting_subject(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "back":
                self.state = 2

            else:
                self.selected_subject = self.list_items[self.selected_list_item][1]

                self.state = 2

            self.selected_list_item = 0

        elif key == 27:
            self.selected_list_item = 0

            self.state = 2

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

    def process_input(self, key: int) -> None:
        if key in [ord('q'), ord('Q')] and self.editing is False:
            raise ExitCurses("Exiting")

        elif key in [ord('s'), ord('S')] and self.editing is False:
            self.timetable.save_file()
            self.stdscreen.addstr(curses.LINES - 1, 1, "Successfully saved")
            self.stdscreen.refresh()

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

    # Displaying Windows

    def display_viewing(self) -> None:
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable, [e] Edit Timetable"

        self.render_timetable()

    def display_editing(self) -> None:
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable"

        self.render_timetable(highlighted=(self.selected_period_x, self.selected_period_y))

    def display_editing_period(self) -> None:
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable"

        self.list_items = [
            (f"Subject: {self.selected_subject.name if self.selected_subject is not None else 'None'}", "subject"),
            (f"Room: {self.input_buffer}", "editor"),
            ("Delete", "delete"),
            ("Save and Exit", "save_exit"),
            ("Back", "back"),
        ]

        self.list_size = len(self.list_items)

        self.display_list()

    def display_selecting_subject(self) -> None:
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable"

        self.list_items = []

        for subject in self.timetable.subjects.values():
            self.list_items.append((subject.name, subject))

        self.list_items.append(("Back", "back"))

        self.list_size = len(self.list_items)

        self.display_list()

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        if self.state == 0 or self.state == 1:
            self.create_period_windows()
            self.create_side_info_windows()

        while True:
            self.window.clear()
            if self.state == -1:
                self.exit()
                return

            if self.state == 0:
                self.display_viewing()

            elif self.state == 1:
                self.display_editing()

            elif self.state == 2:
                self.display_editing_period()

            elif self.state == 3:
                self.display_selecting_subject()

            self.window.addstr(0, 2, self.title)
            self.window.addstr(self.height - 1, 2, self.shortcut_info)
            self.window.refresh()
            curses.doupdate()

            key = self.window.getch()

            self.process_input(key)


class TimetableCreatorMenu(Menu):
    def __init__(self, stdscreen: curses.window) -> None:
        super().__init__("Creating New Timetable", stdscreen)

        self.states: dict[int, str] = {
            -1: "Exiting",
            0: "Basic Info",
            1: "Creating Period Times",
            2: "Viewing Subjects",
            3: "Editing Subject"
        }

        self.state: int = 0

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.shortcut_info: str = "Shortcuts: [esc] Back, [q] Quit"

        self.input_buffer: list[str] = ["", ""]
        self.max_input_size: int = 20

        self.timetable_name: str = ""
        self.num_periods: int = 4

        self.editing: bool = True

        self.include_period_zero: bool = False

        self.period_times: dict[str, PeriodTimeStruct] = {}
        self.subjects: list[Subject] = []

    def process_period_times(self) -> None:
        if self.state != 1:
            return

        self.period_times = {}

        for index in range(len(self.input_buffer) // 2):
            self.period_times[str(index)] = PeriodTimeStruct(f"Period {index}",
                                                             self.input_buffer[index * 2],
                                                             self.input_buffer[index * 2 + 1])

    def process_input_basic_info(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "Back":
                self.state = -1

            elif self.list_items[self.selected_list_item][1] == "Next":
                if self.input_buffer[0] == "" or self.input_buffer[1] == "":
                    curses.beep()

                else:
                    self.timetable_name = self.input_buffer[0]
                    self.num_periods = int(self.input_buffer[1])

                    self.input_buffer = []

                    for i in range(self.num_periods):
                        self.input_buffer.append("")
                        self.input_buffer.append("")

                    self.selected_list_item = 0

                    self.state = 1

            elif self.list_items[self.selected_list_item][1] == "period_zero":
                self.include_period_zero = not self.include_period_zero

        elif key == 27:
            self.state = -1

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

        elif self.list_items[self.selected_list_item][1] == "editor":
            if self.list_items[self.selected_list_item][2] == "name":
                if ((ord('!') <= key <= ord('~') or key == ord(' ')) and
                        len(self.input_buffer[0]) < self.max_input_size):
                    self.input_buffer[0] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer) > 0:
                    self.input_buffer[0] = self.input_buffer[0][:-1]

            elif self.list_items[self.selected_list_item][2] == "periods":
                if ord('3') <= key <= ord('6') and len(self.input_buffer[1]) < 1:
                    self.input_buffer[1] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer) > 0:
                    self.input_buffer[1] = self.input_buffer[1][:-1]

    def process_input_creating_period_times(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "Back":
                self.input_buffer = [self.timetable_name, str(self.num_periods)]
                self.selected_list_item = 0

                self.state = 0

            elif self.list_items[self.selected_list_item][1] == "Next":
                self.input_buffer = []
                self.selected_list_item = 0

                self.process_period_times()

                self.state = 2

        elif key == 27:
            self.input_buffer = [self.timetable_name, str(self.num_periods)]
            self.selected_list_item = 0

            self.state = 0

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

        elif self.list_items[self.selected_list_item][1] == "editor":
            start_index: int = self.selected_list_item // 3

            if self.list_items[self.selected_list_item][2] == "start":
                if ord('0') <= key <= ord('9') and len(self.input_buffer[2 * start_index]) < 4:
                    self.input_buffer[2 * start_index] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer[2 * start_index]) > 0:
                    self.input_buffer[2 * start_index] = self.input_buffer[2 * start_index][:-1]

            elif self.list_items[self.selected_list_item][2] == "end":
                if ord('0') <= key <= ord('9') and len(self.input_buffer[2 * start_index + 1]) < 4:
                    self.input_buffer[2 * start_index + 1] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer[2 * start_index + 1]) > 0:
                    self.input_buffer[2 * start_index + 1] = self.input_buffer[2 * start_index + 1][:-1]

    def process_input_viewing_subjects(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "Back":
                self.input_buffer = []

                for i in range(self.num_periods):
                    self.input_buffer.append("")
                    self.input_buffer.append("")

                self.selected_list_item = 0

                self.state = 1

            elif self.list_items[self.selected_list_item][1] == "New":
                subject_edit_menu = SubjectEditMenu(None, self.stdscreen)
                new_subject: Subject | None = subject_edit_menu.display()

                if new_subject is not None:
                    self.subjects.append(new_subject)

            elif self.list_items[self.selected_list_item][1] == "Next":
                curses.beep()

            else:
                subject_edit_menu = SubjectEditMenu(self.subjects[self.selected_list_item],
                                                    self.stdscreen)

                new_subject: Subject | None = subject_edit_menu.display()

                if new_subject is not None:
                    self.subjects[self.selected_list_item] = new_subject

        if key == 27:
            self.input_buffer = []

            for i in range(self.num_periods):
                self.input_buffer.append("")
                self.input_buffer.append("")

            self.selected_list_item = 0

            self.state = 1

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

    def process_input_editing_subject(self, key: int) -> None:
        if key == 27:
            self.selected_list_item = 0
            self.state = 2

    def process_input(self, key: int) -> None:
        if key in [ord('q'), ord('Q')] and self.editing is False:
            raise ExitCurses("Exiting")

        else:
            if self.state == 0:
                self.process_input_basic_info(key)

            elif self.state == 1:
                self.process_input_creating_period_times(key)

            elif self.state == 2:
                self.process_input_viewing_subjects(key)

            elif self.state == 3:
                self.process_input_editing_subject(key)

            else:
                raise ExitCurses("Invalid state")

    def display_basic_info(self) -> None:
        self.list_items = [
            (f"Timetable Name: {self.input_buffer[0]}", "editor", "name"),
            (f"Number of Periods per Day (3 - 6): {self.input_buffer[1]}", "editor", "periods"),
            (f"Include Period Zero [{'x' if self.include_period_zero else ' '}]", "period_zero"),
            ("Next", "Next"),
            ("Back", "Back"),
        ]

        self.list_size = len(self.list_items)
        self.display_list()

    def display_creating_period_times(self) -> None:
        self.list_items = []

        start_index: int = int(not self.include_period_zero)

        for i in range(self.num_periods):
            self.list_items.append((f"Period {i + start_index}", "title"))
            self.list_items.append((f"Start: {self.input_buffer[2 * i]}", "editor", "start"))
            self.list_items.append((f"End: {self.input_buffer[2 * i + 1]}", "editor", "end"))

        self.list_items.append(("Next", "Next"))
        self.list_items.append(("Back", "Back"))

        self.list_size = len(self.list_items)
        self.display_list()

    def display_viewing_subjects(self) -> None:
        self.list_items = []

        for subject in self.subjects:
            self.list_items.append((f"{subject.name}", subject))

        self.list_items.append(("Create New", "New"))
        self.list_items.append(("Next", "Next"))
        self.list_items.append(("Back", "Back"))

        self.display_list()

    def display_editing_subject(self) -> None:
        self.list_items = []

        self.list_items = [
            (f"Name: {self.input_buffer[0]}", "name"),
            (f"Teacher: {self.input_buffer[1]}", "teacher"),
            ("Delete", "Delete"),
            (f"Save and Exit", "save"),
            (f"Back", "Back"),
        ]

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.clear()
            if self.state == -1:
                self.exit()
                return

            if self.state == 0:
                self.display_basic_info()

            elif self.state == 1:
                self.display_creating_period_times()

            elif self.state == 2:
                self.display_viewing_subjects()

            elif self.state == 3:
                self.display_editing_subject()

            self.window.addstr(0, 2, self.title)
            self.window.addstr(self.height - 1, 2, self.shortcut_info)
            self.window.refresh()

            key = self.window.getch()

            self.process_input(key)


class SubjectEditMenu(ListMenu):
    def __init__(self, subject: Subject | None, stdscreen):
        self.original_subject: Subject | None = subject
        self.subject: Subject | None = subject

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


class App:
    def __init__(self, stdscreen: curses.window) -> None:
        self.current_timetable: Timetable | None = None

        self.screen: curses.window = stdscreen
        curses.curs_set(0)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
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

        main_menu_items = [
            ("Open Existing", files_menu.display),
            ("Create New", self.create_new_timetable),
        ]

        main_menu = ListMenu("Open an existing timetable or create a new one", main_menu_items, self.screen)
        main_menu.display()

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
            raise InvalidDataException("Invalid configuration (Missing Data)")

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

        self.current_timetable = Timetable(periods, subjects, period_times, timetable_name, filename)

    def open_file(self, filename: str) -> None:
        self.load_file(filename)
        if self.current_timetable is not None:
            timetable_menu = TimetableMenu(self.current_timetable, self.screen)
            timetable_menu.display()

    def create_new_timetable(self) -> None:
        timetable_creator_menu = TimetableCreatorMenu(self.screen)
        timetable_creator_menu.display()


if __name__ == "__main__":
    try:
        # Makes the terminal reset properly if it crashes for whatever reason
        # If this is omitted, crashing will result in the curses content remaining on the screen which is not wanted
        curses.wrapper(App)

    except ExitCurses as e:
        print(e)

    except InvalidDataException as e:
        print("Error: Invalid JSON Data!")
        print(e)
