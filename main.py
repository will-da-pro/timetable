#!/usr/bin/env python3

# Copyright 2025 William D'Olier

import json
import curses
from collections.abc import Callable
from curses import panel
import os
from abc import ABC, abstractmethod
import glob
from dataclasses import dataclass
from random import randint
import argparse
from pathlib import Path


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


class InvalidFileException(Exception):
    """
    Raised when invalid JSON file is encountered.
    """

    def __init__(self, message: str):
        self.message: str = message


# Data Structures
# Allows for much clearer type hints, and easier to work with than dictionaries.


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
        return f"{self.name} | {self.teacher}"


@dataclass
class Period:
    """
    Class for a period during the day, has a subject and room.

    Created for every period time on every day.
    """

    subject: Subject
    room: str

    def __str__(self) -> str:
        return f"Subject: {self.subject}, Room: {self.room}"


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
        for day in self.periods.values():
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

        # Adds all data to one dict
        json_data["name"] = self.name
        json_data["timetable"] = timetable_raw
        json_data["subjects"] = subjects_raw
        json_data["period_times"] = period_times_raw

        # Turns said dict into JSON
        json_object = json.dumps(json_data, indent=4)

        # Writes JSON data to file
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

        # Separate window for the border
        self.border_window = parent.subwin(height, width, self.y_pos, self.x_pos)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        self.border_window.refresh()

        # Main window for all content
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
    """
    Class for a period window with a border which displays the subject, teacher and room.
    """

    def __init__(self, period: Period,
                 width: int, height: int,
                 x_pos: int, y_pos: int,
                 x_index: int, y_index: int,
                 parent) -> None:
        """
        Initializes a period window object.

        :param period: The period to render.
        :param width: The width of the window.
        :param height: The height of the window.
        :param x_pos: The x position of the window, relative to the entire screen.
        :param y_pos: The y position of the window, relative to the entire screen.
        :param x_index: The day index of the period.
        :param y_index: The index of the period during the day.
        :param parent: The parent window object.
        """

        super().__init__(width, height, x_pos, y_pos, parent)

        self.period: Period = period

        self.x_index: int = x_index
        self.y_index: int = y_index

    def display(self, selected: bool = False) -> None:
        self.window.erase()

        # Checks if the window is being selected by the user
        if selected:
            self.window.bkgd(' ', curses.color_pair(3))
            self.border_window.bkgd(' ', curses.color_pair(3))

        else:
            self.window.bkgd(' ', curses.color_pair(1))
            self.border_window.bkgd(' ', curses.color_pair(1))

        # Adds all info
        self.window.addstr(0, 1, self.period.subject.name)
        self.window.addstr(1, 1, self.period.subject.teacher)
        self.window.addstr(2, 1, self.period.room)
        self.window.refresh()

        # Refreshes the border window for colors to change
        self.border_window.border(0)
        self.border_window.refresh()


class PeriodTimeWindow(ContentWindow):
    """
    Class for period time windows, displaying the start and end time of each period.
    """

    def __init__(self, period_times: PeriodTimeStruct,
                 width: int, height: int,
                 x_pos: int, y_pos: int,
                 parent) -> None:

        super().__init__(width, height, x_pos, y_pos, parent)
        self.period_times = period_times

    def display(self) -> None:
        self.window.erase()

        # Displays all info
        self.window.addstr(0, 1, self.period_times.name)
        self.window.addstr(1, 1, self.period_times.start_time)
        self.window.addstr(2, 1, self.period_times.end_time)

        self.window.refresh()

        self.border_window.border(0)
        self.border_window.refresh()


class TempPopupWindow(ContentWindow):
    """
    A temporary popup window, used for displaying info messages and such.
    """

    def __init__(self, message: str, stdscreen: curses.window) -> None:
        """
        Initializes a temporary popup window object.
        :param message: The message to display.
        :param stdscreen: The parent window object.
        """

        self.message: str = message
        self.secondary_message: str = "Any key to continue..."

        width: int = max(len(self.message), len(self.secondary_message)) + 4
        height: int = 4

        x_pos: int = (curses.COLS - width) // 2
        y_pos: int = (curses.LINES - height) // 2

        super().__init__(width, height, x_pos, y_pos, stdscreen)

    def display(self) -> None:
        self.window.erase()

        # Display info
        self.window.addstr(0, 1, self.message)
        self.window.addstr(1, 1, self.secondary_message)

        self.window.refresh()

        self.window.getch()


# Menus


class Menu(ABC):
    """
    Class for all major menus.

    Creates a border window, shadow window and main window for rendering content.
    """

    def __init__(self, title: str, stdscreen: curses.window,
                 width: int = 150, height: int = 40,
                 header: str = "TIMETABLE APP") -> None:
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

        # A separate window for displaying a black shadow behind the window.
        self.shadow_window = stdscreen.subwin(height + 2, width + 2, self.y_pos, self.x_pos)
        self.shadow_window.bkgd(' ', curses.color_pair(3))
        self.shadow_window.refresh()

        # A separate window for displaying a border and header.
        self.border_window = stdscreen.subwin(height + 2, width + 2, self.y_pos - 1, self.x_pos - 1)
        self.border_window.bkgd(' ', curses.color_pair(1))
        self.border_window.border(0)
        self.border_window.addstr(0, (self.width - len(header)) // 2 - 1, "┤")
        self.border_window.addstr(0, (self.width + len(header)) // 2 + 2, "├")
        self.border_window.addstr(0, (self.width - len(header)) // 2, f" {header} ", curses.color_pair(4))
        self.border_window.refresh()

        # The main window for content to be displayed on
        self.window = stdscreen.subwin(height, width, self.y_pos, self.x_pos)
        self.window.keypad(True)
        self.window.bkgd(' ', curses.color_pair(1))

        # Attributes used for displaying a navigable list on screen
        self.selected_list_item: int = 0
        self.top_list_item: int = 0
        self.max_list_items: int = self.height - 8

        self.list_items: list[tuple] = []

        # Used to disable shortcuts when the user is editing text
        self.editing: bool = False

    def display_list(self) -> None:
        """
        Displays a navigable list of items on screen.

        :return:
        """

        if self.list_items[self.selected_list_item][1] == "editor":
            self.editing = True

        else:
            self.editing = False

        # Shorten the list to only display less than the maximum number of items, starting at the top item
        display_list: list[tuple] = self.list_items[self.top_list_item:self.top_list_item + self.max_list_items]

        # Displays the list on screen
        for index, item in enumerate(display_list):
            if index + self.top_list_item == self.selected_list_item:
                self.window.addstr(index + 2, 1, f"› {item[0]} ", curses.A_REVERSE)

            else:
                self.window.addstr(index + 2, 1, item[0])

        # Check if there are additional list items that have been cut off
        if self.top_list_item > 0:
            self.window.addstr(1, 1, " More ", curses.A_REVERSE)

        if len(self.list_items) - self.top_list_item > self.max_list_items:
            self.window.addstr(self.max_list_items + 2, 1, " More ", curses.A_REVERSE)

    def navigate_list(self, change: int) -> None:
        """
        Used to change the user's position in the navigation list.

        :param change: The amount to change by.
        :return:
        """

        self.selected_list_item += change

        if self.selected_list_item < 0:
            self.selected_list_item = 0

        elif self.selected_list_item >= len(self.list_items):
            self.selected_list_item = len(self.list_items) - 1

        # Get the position relative to the top displayed element, and adjust if necessary
        relative_pos: int = self.selected_list_item - self.top_list_item

        if relative_pos >= self.max_list_items:
            self.top_list_item = self.selected_list_item - self.max_list_items + 1

        elif relative_pos < 0:
            self.top_list_item = self.selected_list_item

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


class QuickListMenu(Menu):
    """
    Allows for the quick creation of a simple list menu.
    """

    def __init__(self, title: str, items, stdscreen):
        super().__init__(title, stdscreen)

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.list_items = items
        self.list_items.append(("Exit", "Exit"))

        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [return] Select"

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.erase()
            self.display_list()
            self.window.addstr(self.height - 1, 2, self.shortcut_info)
            self.window.addstr(0, 2, self.title)
            self.window.refresh()

            key = self.window.getch()

            # Check if the user has pressed enter to select an item
            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.list_items[self.selected_list_item][1] == "Exit":
                    self.exit()
                    return

                # Check if the second item in the tuple is a function, if so call it with parameters
                elif isinstance(self.list_items[self.selected_list_item][1], Callable):
                    if len(self.list_items[self.selected_list_item]) <= 2:
                        self.list_items[self.selected_list_item][1]()

                    else:
                        self.list_items[self.selected_list_item][1](*self.list_items[self.selected_list_item][2:])

            # Exit the program
            elif key == ord("q"):
                raise ExitCurses("Exiting")

            # Escape key
            elif key == 27:
                self.exit()
                return

            # Navigate the list
            elif key == curses.KEY_UP:
                self.navigate_list(-1)

            elif key == curses.KEY_DOWN:
                self.navigate_list(1)


class TimetableMenu(Menu):
    """
    Main class for viewing and editing timetable objects.

    Has 4 different states:

    - Viewing
    - Editing
    - Editing Period
    - Selecting Subject

    Each state has its own sub-menu, and input handling.
    """

    def __init__(self, timetable: Timetable, stdscreen: curses.window) -> None:
        """
        Creates a menu for rendering a timetable, with an editor.

        :param timetable: The timetable object to view.
        :param stdscreen: Curses screen to use.
        """

        super().__init__(timetable.name, stdscreen)

        # Attributes for states
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

        # Will be rendered onscreen
        self.days: list[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.shortcut_info: str = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable, [return] Select"

        # Windows for periods and period times
        self.period_windows: list[PeriodWindow] = []
        self.period_time_windows: list[PeriodTimeWindow] = []

        # More info for displaying windows
        self.margin: int = 5
        self.period_times_window_width: int = self.margin * 3

        self.period_height: int = 5
        self.period_width: int = (self.width - self.period_times_window_width - 2 * self.margin) // 5

        self.cell_x_count: int = 5
        self.cell_y_count: int = len(self.timetable.period_times)

        self.selected_period_x: int = 0
        self.selected_period_y: int = 0

        # Used to edit the selected period or subject
        self.selected_period: Period | None = None
        self.selected_subject: Subject | None = None

        # Input handling
        self.input_buffer: str = ""
        self.max_input_size: int = 20

    def create_period_windows(self) -> None:
        """
        Creates the windows used to display the periods.

        :return:
        """

        self.period_windows = []

        for day_num, day in self.timetable.periods.items():
            for period_id, period in day.items():
                day_index = list(self.timetable.period_times.keys()).index(period_id)

                # Position of the new window
                window_x = self.x_pos + self.margin + day_num * self.period_width + self.period_times_window_width
                window_y = self.y_pos + self.margin + day_index * self.period_height

                period_window: PeriodWindow = PeriodWindow(period, self.period_width, self.period_height,
                                                           window_x, window_y,
                                                           day_num, day_index, self.window)

                self.period_windows.append(period_window)

    def create_period_time_windows(self) -> None:
        """
        Creates the windows used to display the period times.

        :return:
        """

        for index, period_data in enumerate(self.timetable.period_times.values()):
            # Position of the new window
            window_x: int = self.x_pos + self.margin
            window_y: int = self.y_pos + self.margin + index * self.period_height

            period_time_window: PeriodTimeWindow = PeriodTimeWindow(period_data, self.period_times_window_width,
                                                                    self.period_height,
                                                                    window_x, window_y,
                                                                    self.window)

            self.period_time_windows.append(period_time_window)

    def render_timetable(self, **kwargs) -> None:
        """
        Renders the timetable on the screen.

        :param kwargs:
        :return:
        """

        highlighted: tuple[int, int] | None = kwargs.get("highlighted")
        selection_found: bool = False

        # Render each period window
        for period_window in self.period_windows:
            if (highlighted is not None
                    and highlighted[0] == period_window.x_index
                    and highlighted[1] == period_window.y_index):

                period_window.display(True)
                selection_found = True

            else:
                period_window.display()

        # If the highlighted window does not exist, display the option to create a new one at the selected position
        if highlighted is not None and not selection_found:
            window_x = self.margin + highlighted[0] * self.period_width + self.period_times_window_width + 1
            window_y = self.margin + highlighted[1] * self.period_height + 1

            self.window.addstr(window_y, window_x, "<Add New>", curses.color_pair(3))

        # Display period time windows
        for period_time_window in self.period_time_windows:
            period_time_window.display()

        for i, day in enumerate(self.days):
            self.window.addstr(self.margin - 2, self.margin + i * self.period_width +
                               self.period_times_window_width + 2, day,
                               curses.color_pair(4))

    def navigate_timetable(self, x_change: int, y_change: int) -> None:
        self.selected_period_x += x_change
        self.selected_period_y += y_change

        # Ensure the selected period is within the boundaries of the timetable
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

            # Load the subject of the selected period
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
            # Select a subject
            if self.list_items[self.selected_list_item][1] == "subject":
                self.selected_list_item = 0

                self.state = 3

            # Delete the period
            elif self.list_items[self.selected_list_item][1] == "delete":
                period_id: str = list(self.timetable.period_times.keys())[self.selected_period_y]

                if self.timetable.periods[self.selected_period_x].get(period_id) is not None:
                    del self.timetable.periods[self.selected_period_x][period_id]

                self.create_period_windows()

                self.state = 1

            # Save the period ad exit
            elif self.list_items[self.selected_list_item][1] == "save_exit":
                if self.selected_subject is not None:
                    period_id: str = list(self.timetable.period_times.keys())[self.selected_period_y]
                    new_period = Period(self.selected_subject, self.input_buffer)

                    self.timetable.periods[self.selected_period_x][period_id] = new_period

                    self.create_period_windows()

                    self.state = 1

                else:
                    popup_window = TempPopupWindow("Please select a subject.", self.stdscreen)
                    popup_window.display()

            # Exit without saving
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

            saved_popup = TempPopupWindow("Successfully Saved Timetable", self.stdscreen)
            saved_popup.display()

        else:
            # Process input based on state
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
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable, [return] Edit Period"

        self.render_timetable(highlighted=(self.selected_period_x, self.selected_period_y))

    def display_editing_period(self) -> None:
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable, [return] Select"

        self.list_items = [
            (f"Subject: {self.selected_subject}", "subject"),
            (f"Room: {self.input_buffer}", "editor"),
            ("Delete", "delete"),
            ("Save and Exit", "save_exit"),
            ("Back", "back"),
        ]

        self.display_list()

    def display_selecting_subject(self) -> None:
        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [s] Save Timetable, [return] Select"

        self.list_items = []

        for subject in self.timetable.subjects.values():
            self.list_items.append((str(subject), subject))

        self.list_items.append(("Back", "back"))

        self.display_list()

    def display(self) -> None:
        self.panel.top()
        self.panel.show()
        self.window.clear()

        if self.state == 0 or self.state == 1:
            self.create_period_windows()
            self.create_period_time_windows()

        while True:
            self.window.clear()

            # Display State

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

            self.title = f"{self.states.get(self.state)} | {self.timetable.name}"

            self.window.addstr(0, 2, self.title)

            if self.editing:
                self.shortcut_info = "(Editing)"

            self.window.addstr(self.height - 1, 2, self.shortcut_info)
            self.window.refresh()
            curses.doupdate()

            key = self.window.getch()

            self.process_input(key)


class TimetableCreatorMenu(Menu):
    """
    Main menu used for creating timetables.

    Has 4 different states:

    - Editing Basic Info
    - Creating Period Times
    - Viewing Subjects
    - Editing Subject

    Each state has its own sub-menu, and input handling.
    """

    def __init__(self, stdscreen: curses.window) -> None:
        super().__init__("Creating New Timetable", stdscreen)

        self.states: dict[int, str] = {
            -1: "Exiting",
            0: "Editing Basic Info",
            1: "Creating Period Times",
            2: "Viewing Subjects",
            3: "Editing Subject"
        }

        self.state: int = 0

        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.shortcut_info: str = "Shortcuts: [esc] Back, [q] Quit, [return] Select"

        self.input_buffer: list[str] = ["", ""]
        self.max_input_size: int = 20

        self.timetable_name: str = ""
        self.num_periods: int = 4

        self.editing: bool = True

        self.include_period_zero: bool = False

        self.period_times: dict[str, PeriodTimeStruct] = {}
        self.subjects: dict[str, Subject] = {}

        self.subject_editing_id: str | None = None

        self.timetable: Timetable | None = None

    def create_timetable(self) -> None:
        periods: dict[int, dict[str, Period]] = {}

        for i in range(6):
            periods[i] = {}

        filename: str = f"{data_dir}/{self.timetable_name.lower().replace(' ', '_')}.json"

        self.timetable = Timetable(periods, self.subjects, self.period_times, self.timetable_name, filename)

    def process_period_times(self) -> None:
        if self.state != 1:
            return

        self.period_times = {}

        start_index: int = int(not self.include_period_zero)

        for index in range(len(self.input_buffer) // 2):
            self.period_times[str(index)] = PeriodTimeStruct(f"Period {index + start_index}",
                                                             self.input_buffer[index * 2],
                                                             self.input_buffer[index * 2 + 1])

    # Input Processing

    def process_input_basic_info(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "Back":
                self.state = -1

            elif self.list_items[self.selected_list_item][1] == "Next":
                if self.input_buffer[0] == "":
                    popup_window = TempPopupWindow("Please enter a name for the timetable.", self.stdscreen)
                    popup_window.display()

                elif self.input_buffer[1] == "":
                    popup_window = TempPopupWindow("Please select the number of periods", self.stdscreen)
                    popup_window.display()

                else:
                    self.timetable_name = self.input_buffer[0]
                    self.num_periods = int(self.input_buffer[1])

                    self.input_buffer = []

                    for _ in range(self.num_periods):
                        self.input_buffer.append("")
                        self.input_buffer.append("")

                    self.selected_list_item = 0

                    self.state = 1

        elif key == 27:
            self.state = -1

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

        elif self.list_items[self.selected_list_item][1] == "editor":
            if self.list_items[self.selected_list_item][2] == "name":
                if ((ord('!') <= key <= ord('~') or key == ord(' ')) and  # See an ascii chart for context
                        key != ord('/') and  # Illegal character in unix filenames so must be filtered out
                        len(self.input_buffer[0]) < self.max_input_size):
                    self.input_buffer[0] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer[0]) > 0:
                    self.input_buffer[0] = self.input_buffer[0][:-1]

            elif self.list_items[self.selected_list_item][2] == "periods":
                if ord('3') <= key <= ord('6') and len(self.input_buffer[1]) < 1:
                    self.input_buffer[1] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer[1]) > 0:
                    self.input_buffer[1] = self.input_buffer[1][:-1]

        elif self.list_items[self.selected_list_item][1] == "period_zero":
            if key in [ord("y"), ord("Y")]:
                self.include_period_zero = True

            elif key in [ord("n"), ord("N")]:
                self.include_period_zero = False

    def process_input_creating_period_times(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "Back":
                self.input_buffer = [self.timetable_name, str(self.num_periods)]
                self.selected_list_item = 0

                self.state = 0

            elif self.list_items[self.selected_list_item][1] == "Next":
                self.process_period_times()

                self.input_buffer = []
                self.selected_list_item = 0

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

                for _ in range(self.num_periods):
                    self.input_buffer.append("")
                    self.input_buffer.append("")

                self.selected_list_item = 0

                self.state = 1

            elif self.list_items[self.selected_list_item][1] == "New":
                self.input_buffer = [
                    "",
                    ""
                ]

                self.selected_list_item = 0

                new_id: str = str(randint(0, 9999999999))

                while self.subjects.get(new_id) is not None:
                    new_id = str(randint(0, 9999999999))

                self.subject_editing_id = new_id

                self.state = 3

            elif self.list_items[self.selected_list_item][1] == "Create":
                if len(self.subjects) == 0:
                    popup_window = TempPopupWindow("Create at least one subject to proceed.", self.stdscreen)
                    popup_window.display()

                    return

                self.create_timetable()

                if self.timetable is not None:
                    timetable_view_menu = TimetableMenu(self.timetable, self.stdscreen)

                    timetable_view_menu.display()

            else:
                self.subject_editing_id = list(self.subjects.keys())[self.selected_list_item]

                self.input_buffer = [
                    self.subjects[self.subject_editing_id].name,
                    self.subjects[self.subject_editing_id].teacher
                ]

                self.state = 3

        if key == 27:
            self.input_buffer = []

            for _ in range(self.num_periods):
                self.input_buffer.append("")
                self.input_buffer.append("")

            self.selected_list_item = 0

            self.state = 1

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

    def process_input_editing_subject(self, key: int) -> None:
        if key in [curses.KEY_ENTER, ord("\n")]:
            if self.list_items[self.selected_list_item][1] == "Delete" and self.subject_editing_id is not None:
                if self.subjects.get(self.subject_editing_id) is not None:
                    del self.subjects[self.subject_editing_id]

                self.input_buffer = []
                self.selected_list_item = 0
                self.state = 2

            elif self.list_items[self.selected_list_item][1] == "Save" and self.subject_editing_id is not None:
                if self.input_buffer[0] == "":
                    popup_window = TempPopupWindow("Please enter a name for the period.", self.stdscreen)
                    popup_window.display()

                    return

                new_subject = Subject(self.subject_editing_id, self.input_buffer[0], self.input_buffer[1])

                self.subjects[self.subject_editing_id] = new_subject

                self.input_buffer = []
                self.selected_list_item = 0

                self.state = 2

            elif self.list_items[self.selected_list_item][1] == "Back":
                self.input_buffer = []
                self.selected_list_item = 0

                self.state = 2

        elif key == 27:
            self.selected_list_item = 0
            self.state = 2

        elif key == curses.KEY_UP:
            self.navigate_list(-1)

        elif key == curses.KEY_DOWN:
            self.navigate_list(1)

        elif self.list_items[self.selected_list_item][1] == "editor":
            if self.list_items[self.selected_list_item][2] == "name":
                if ((ord('!') <= key <= ord('~') or key == ord(' ')) and
                        len(self.input_buffer[0]) < self.max_input_size):
                    self.input_buffer[0] += chr(key)

                elif key in [127, curses.KEY_BACKSPACE] and len(self.input_buffer[0]) > 0:
                    self.input_buffer[0] = self.input_buffer[0][:-1]

            elif self.list_items[self.selected_list_item][2] == "teacher":
                if ((ord('!') <= key <= ord('~') or key == ord(' ')) and
                        len(self.input_buffer[1]) < self.max_input_size):
                    self.input_buffer[1] += chr(key)

                elif key in [curses.KEY_BACKSPACE, 127] and len(self.input_buffer[1]) > 0:
                    self.input_buffer[1] = self.input_buffer[1][:-1]

    def process_input(self, key: int) -> None:
        if key in [ord('q'), ord('Q')] and self.editing is False:
            raise ExitCurses("Exiting")

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

    # Displaying Windows

    def display_basic_info(self) -> None:
        self.list_items = [
            (f"Timetable Name: {self.input_buffer[0]}", "editor", "name"),
            (f"Number of Periods per Day (3 - 6): {self.input_buffer[1]}", "editor", "periods"),
            (f"Include Period Zero (y/n): {'y' if self.include_period_zero else 'n'}", "period_zero"),
            ("Next", "Next"),
            ("Back", "Back"),
        ]

        self.display_list()

        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [return] Select"

    def display_creating_period_times(self) -> None:
        self.list_items = []

        start_index: int = int(not self.include_period_zero)

        for i in range(self.num_periods):
            self.list_items.append((f"Period {i + start_index}", "title"))
            self.list_items.append((f"Start Time: {self.input_buffer[2 * i]}", "editor", "start"))
            self.list_items.append((f"End Time: {self.input_buffer[2 * i + 1]}", "editor", "end"))

        self.list_items.append(("Next", "Next"))
        self.list_items.append(("Back", "Back"))

        self.display_list()

        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [return] Select"

    def display_viewing_subjects(self) -> None:
        self.list_items = []

        for subject in self.subjects.values():
            self.list_items.append((str(subject), subject))

        self.list_items.append(("Create New Subject", "New"))
        self.list_items.append(("Create Timetable", "Create"))
        self.list_items.append(("Back", "Back"))

        self.display_list()

        if isinstance(self.list_items[self.selected_list_item][1], Subject):
            self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [return] Edit Subject"

        else:
            self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [return] Select"

    def display_editing_subject(self) -> None:
        self.list_items = []

        self.list_items = [
            (f"Name: {self.input_buffer[0]}", "editor", "name"),
            (f"Teacher: {self.input_buffer[1]}", "editor", "teacher"),
            ("Delete", "Delete"),
            ("Save and Exit", "Save"),
            ("Back", "Back"),
        ]

        self.display_list()

        self.shortcut_info = "Shortcuts: [esc] Back, [q] Quit, [return] Select"

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

            self.title = f"{self.states.get(self.state)} | Creating Timetable"

            if self.editing:
                self.shortcut_info = "(Editing)"

            self.window.addstr(0, 2, self.title)
            self.window.addstr(self.height - 1, 2, self.shortcut_info)
            self.window.refresh()

            key = self.window.getch()

            self.process_input(key)


class App:
    """
    Main class for launching the application.
    """

    def __init__(self, stdscreen: curses.window) -> None:
        """
        Initialize and run the application.

        :param stdscreen: The curses window instance.
        """

        # Timetable to use
        self.current_timetable: Timetable | None = None

        # Curses window instance to use
        self.screen: curses.window = stdscreen

        # Disable cursor visibility
        curses.curs_set(0)

        # Color initialization
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)

        # Set background color
        stdscreen.bkgd(' ', curses.color_pair(2))

        # Check the data/ directory exists, if not create one
        self.check_data_dir()

        # Check if the user used the opt_file argument
        file: str | None = opts.opt_file

        # If they did, make sure it exists, then open it
        if file is not None:
            if not os.path.isfile(file):
                raise InvalidFileException(f"File '{file}' does not exist")

            self.open_file(file)

        # Search the data/ directory for .json files
        files = glob.glob(f"{data_dir}/*.json")
        file_items = []
        for file in files:
            file_name: str = Path(file).stem
            file_items.append((file_name, self.open_file, file))

        # No .json files found
        if len(file_items) == 0:
            file_items.append(
                ("No files found! Are you sure they are in the correct directory? (data/[name].json)", curses.beep))

        # Instance of ListMenu for selecting a file to open
        files_menu = QuickListMenu("Select a file to open", file_items, self.screen)

        main_menu_items = [
            ("Open Existing", files_menu.display),
            ("Create New", self.create_new_timetable),
        ]

        # ListMenu instance for selecting whether to view or edit a timetable
        main_menu = QuickListMenu("Open an existing timetable or create a new one", main_menu_items, self.screen)
        main_menu.display()

    @staticmethod
    def check_data_dir() -> None:
        """
        Checks if the data/ directory exists. If not, creates it.

        :return:
        """

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def load_file(self, filename: str) -> None:
        """
        Loads a JSON file from the given path, and turns it into a Timetable object.

        :param filename: The path to the JSON file to load.
        :return:
        """

        # Uses the JSON module to load data into python objects
        with open(filename) as f:
            try:
                json_data: dict | None = json.load(f)
            except json.decoder.JSONDecodeError as exception:
                raise InvalidDataException("Invalid JSON") from exception

        if json_data is None:
            raise InvalidDataException("No data found!")

        # Tries to extract timetable data from the json data
        try:
            timetable_name: str = json_data["name"]
            timetable_raw: list[dict[str, dict[str, str]]] = json_data["timetable"]
            subjects_raw: dict[str, dict[str, str]] = json_data["subjects"]
            period_times_raw: dict[str, dict[str, str]] = json_data["period_times"]

        # Occurs if there is a missing field in the JSON data
        except KeyError as exception:
            raise InvalidDataException("Invalid configuration (Missing Data)") from exception

        # Creating subject objects
        subjects: dict[str, Subject] = {}
        for subject_id, subject_raw in subjects_raw.items():
            name: str | None = subject_raw.get("name")
            teacher: str | None = subject_raw.get("teacher")

            if name is None or teacher is None:
                raise InvalidDataException(f"{subject_id} has no name or teacher")

            subjects[subject_id] = Subject(subject_id, name, teacher)

        # Creating timetable of periods
        periods: dict[int, dict[str, Period]] = {}
        for i, day in enumerate(timetable_raw):
            periods[i] = {}
            for period_id, val in day.items():
                subject_id: str | None = val.get("subject")

                if subject_id is None:
                    raise InvalidDataException("No subject ID found")

                subject: Subject | None = subjects.get(subject_id)
                room: str | None = val.get("room")

                if subject is None or room is None:
                    raise InvalidDataException(f"{period_id} has no subject or room for day {day}")

                period: Period = Period(subject, room)

                periods[i][period_id] = period

        # Creating period time objects
        period_times: dict[str, PeriodTimeStruct] = {}
        for period_num, period_time_data in period_times_raw.items():
            name: str | None = period_time_data.get("name")
            start_time: str | None = period_time_data.get("start")
            end_time: str | None = period_time_data.get("end")

            if name is None or start_time is None or end_time is None:
                raise InvalidDataException(f"Period {period_num} is missing data")

            period_time_struct = PeriodTimeStruct(name, start_time, end_time)
            period_times[period_num] = period_time_struct

        # Creates Timetable
        self.current_timetable = Timetable(periods, subjects, period_times, timetable_name, filename)

    def open_file(self, filename: str) -> None:
        """
        Loads and runs the given file.

        :param filename: The path to the JSON file to load.
        :return:
        """

        self.load_file(filename)

        if self.current_timetable is not None:
            timetable_menu = TimetableMenu(self.current_timetable, self.screen)
            timetable_menu.display()

    def create_new_timetable(self) -> None:
        """
        Opens the menu to create a new timetable.

        :return:
        """

        timetable_creator_menu = TimetableCreatorMenu(self.screen)
        timetable_creator_menu.display()


# Ensures the script doesn't run if it is being imported as a library
if __name__ == "__main__":
    # Get the directory of the script
    # Allows for the script to be run from /usr/local/bin via a symlink
    data_dir: str = f"{os.path.dirname(os.path.realpath(os.path.abspath(__file__)))}/data"

    # Argument Handling, allows for the user to open straight into a timetable to view
    parser = argparse.ArgumentParser(description='Simple timetable creator and viewer written in Python')
    parser.add_argument('opt_file', type=str, nargs='?',
                        help='Timetable file path to view')

    opts = parser.parse_args()

    try:
        # Makes the terminal reset properly if it crashes for whatever reason
        # If this is omitted, crashing will result in the curses content remaining on the screen which is not wanted
        curses.wrapper(App)

    # Various exceptions that may be called by the program
    except ExitCurses as e:
        print(e)

    except InvalidDataException as exc:
        print("Error: Invalid JSON Data!")
        raise exc

    except InvalidFileException as e:
        parser.error(str(e))

    except curses.error:
        print("Terminal may be too small! Make sure you are running it in full screen!")
