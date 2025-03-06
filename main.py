#!/usr/bin/env python
import tkinter as tk
from tkinter import ttk
import json
import re
import curses
from curses import wrapper
from abc import ABC, abstractmethod
window: tk.Tk = tk.Tk()

# Time regex
# ^([0-1][0-9]|2[0-3]):[0-5][0-9]$

# Color regex
# ^#(?:[0-9a-fA-F]{3}){1,2}$


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
        frame = tk.Frame(window, padx=10, pady=10, highlightbackground=self.period_type.color, highlightthickness=5, bd=0)
        frame.config(width=1000)
        frame.grid(column=x_pos, row=y_pos, sticky="nsew", pady=2, padx=2)

        name_label = tk.Label(frame, text=self.period_type.name)
        name_label.pack()

        if self.period_type.teacher is not None:
            teacher_label = tk.Label(frame, text=self.period_type.teacher)
            teacher_label.pack()

        if self.room is not None:
            room_label = tk.Label(frame, text=self.room)
            room_label.pack()

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
    def __init__(self, cell_width, cell_height) -> None:
        self.current_timetable: TimeTable | None = None

        self.cell_width = cell_width
        self.cell_height = cell_height
        
        self.total_width = cell_width * 7
        self.total_height = 100

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
            timetabe_name: str = json_data["name"]
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

                periods[i][period_id] = period;

        self.current_timetable = TimeTable(periods, subjects, period_data, timetabe_name)
        self.total_height = len(period_data) * self.cell_height
        
        print(f"Timetable at {filename} successfully loaded")


def main():
    # Create the app's main window
    window.title("Timetable")

    cell_width = 125
    cell_height = 75

    app: App = App(cell_width, cell_height)
    app.load_file("data/test1.json")
    print(app.total_height)

    window.geometry(f"{app.total_width}x{app.total_height}")
    window.minsize(app.total_width, app.total_height)

    if app.current_timetable is not None:
        app.current_timetable.render()

    style = ttk.Style()
    style.theme_use("aqua")
    style.configure("aqua", background="#FFFFFF")

    # Start the event loop
    window.mainloop()


if __name__ == "__main__":
    main()
