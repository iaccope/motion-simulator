
"""Motion Simulator - Aerospace Lab.

Vertical motion with either:
1. Constant gravitational acceleration without air resistance.
2. Quadratic air resistance integrated using RK4.
"""

import csv
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from physics import (
    calculate_height,
    calculate_velocity,
    calculate_landing_time,
    generate_simulation_data,
)
from aerodynamics import simulate_with_air_resistance


class MotionSimulator:
    MAX_FLIGHT_TIME = 100000.0
    MAX_DATA_POINTS = 20000
    MIN_TIME_STEP = 0.01
    MAX_TIME_STEP = 10.0

    IDEAL_MODEL = "Ideal (no air resistance)"
    AERO_MODEL = "With air resistance"

    def __init__(self, root):
        self.root = root
        self.root.title("Motion Simulator | Aerospace Lab")
        self.root.geometry("1150x820")
        self.root.minsize(950, 700)
        self.root.configure(bg="#101820")

        self.data = []
        self.parameters = None
        self.animation_index = 0
        self.animation_job = None
        self.is_playing = False

        self.setup_style()
        self.create_interface()

        self.status.set("Ready. Configure the parameters and click Simulate.")

    # --------------------------------------------------------
    # INTERFACE
    # --------------------------------------------------------

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#101820")
        style.configure("Panel.TFrame", background="#182630")
        style.configure(
            "TLabel",
            background="#101820",
            foreground="#EAF2F8",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Panel.TLabel",
            background="#182630",
            foreground="#EAF2F8",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background="#101820",
            foreground="#FFFFFF",
            font=("Segoe UI", 21, "bold"),
        )
        style.configure(
            "Metric.TLabel",
            background="#182630",
            foreground="#66E3C4",
            font=("Segoe UI", 15, "bold"),
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=7)
        style.configure("TNotebook", background="#101820", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#263945",
            foreground="#FFFFFF",
            padding=(14, 8),
        )
        style.map("TNotebook.Tab", background=[("selected", "#008F75")])
        style.configure(
            "Treeview",
            background="#182630",
            fieldbackground="#182630",
            foreground="#EAF2F8",
            rowheight=25,
        )
        style.configure(
            "Treeview.Heading",
            background="#263945",
            foreground="#FFFFFF",
        )

    def create_interface(self):
        header = ttk.Frame(self.root, padding=20)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="MOTION SIMULATOR",
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Aerospace Lab | Vertical motion | Ideal and aerodynamic models",
        ).pack(anchor="w", pady=(5, 0))

        controls = ttk.Frame(
            self.root,
            style="Panel.TFrame",
            padding=12,
        )
        controls.pack(fill="x", padx=20, pady=(0, 12))

        # Initial conditions
        self.height_var = tk.StringVar(value="0")
        self.velocity_var = tk.StringVar(value="40")
        self.gravity_var = tk.StringVar(value="9.81")
        self.step_var = tk.StringVar(value="0.1")

        # Aerodynamic parameters
        self.model_var = tk.StringVar(value=self.IDEAL_MODEL)
        self.mass_var = tk.StringVar(value="1.0")
        self.drag_var = tk.StringVar(value="0.47")
        self.area_var = tk.StringVar(value="0.1")

        fields = [
            ("Initial height (m)", self.height_var),
            ("Initial velocity (m/s)", self.velocity_var),
            ("Gravity (m/s²)", self.gravity_var),
            ("Time step (s)", self.step_var),
        ]

        for column, (label, variable) in enumerate(fields):
            self.add_entry(controls, label, variable, 0, column)

        ttk.Label(
            controls,
            text="Physical model",
            style="Panel.TLabel",
        ).grid(row=1, column=0, padx=6, pady=(12, 4), sticky="w")

        self.model_box = ttk.Combobox(
            controls,
            textvariable=self.model_var,
            values=(self.IDEAL_MODEL, self.AERO_MODEL),
            state="readonly",
            width=22,
        )
        self.model_box.grid(
            row=2, column=0, padx=6, pady=(0, 4), sticky="ew"
        )
        self.model_box.bind("<<ComboboxSelected>>", self.on_model_changed)

        self.mass_entry = self.add_entry(
            controls, "Mass (kg)", self.mass_var, 1, 1
        )
        self.drag_entry = self.add_entry(
            controls, "Drag coefficient (Cd)", self.drag_var, 1, 2
        )
        self.area_entry = self.add_entry(
            controls, "Frontal area (m²)", self.area_var, 1, 3
        )

        for column in range(4):
            controls.columnconfigure(column, weight=1)

        buttons = ttk.Frame(controls, style="Panel.TFrame")
        buttons.grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(12, 0)
        )

        ttk.Button(
            buttons, text="Simulate", command=self.simulate
        ).pack(side="left", padx=3)

        self.play_button = ttk.Button(
            buttons,
            text="Pause",
            command=self.toggle_play,
            state="disabled",
        )
        self.play_button.pack(side="left", padx=3)

        ttk.Button(
            buttons, text="Reset", command=self.reset
        ).pack(side="left", padx=3)

        ttk.Button(
            buttons, text="Export CSV", command=self.export_csv
        ).pack(side="left", padx=3)

        self.on_model_changed()

        # Summary metrics
        metrics = ttk.Frame(self.root)
        metrics.pack(fill="x", padx=20, pady=(0, 12))

        definitions = [
            ("max_height", "MAX HEIGHT"),
            ("peak_time", "TIME TO PEAK"),
            ("flight_time", "FLIGHT TIME"),
            ("landing_speed", "LANDING SPEED"),
        ]

        self.metric_labels = {}

        for index, (key, title) in enumerate(definitions):
            card = ttk.Frame(
                metrics, style="Panel.TFrame", padding=10
            )
            card.grid(row=0, column=index, padx=4, sticky="ew")
            metrics.columnconfigure(index, weight=1)

            ttk.Label(
                card, text=title, style="Panel.TLabel"
            ).pack(anchor="w")

            label = ttk.Label(
                card, text="—", style="Metric.TLabel"
            )
            label.pack(anchor="w", pady=(5, 0))
            self.metric_labels[key] = label

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(
            fill="both", expand=True, padx=20, pady=(0, 10)
        )

        self.trajectory_tab = ttk.Frame(self.tabs)
        self.graph_tab = ttk.Frame(self.tabs)
        self.table_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.trajectory_tab, text="Trajectory")
        self.tabs.add(self.graph_tab, text="Graphs")
        self.tabs.add(self.table_tab, text="Data table")

        self.trajectory_canvas = tk.Canvas(
            self.trajectory_tab,
            bg="#0B131A",
            highlightthickness=0,
        )
        self.trajectory_canvas.pack(
            fill="both", expand=True, padx=8, pady=8
        )
        self.trajectory_canvas.bind(
            "<Configure>", lambda event: self.draw_trajectory()
        )

        self.graph_canvas = tk.Canvas(
            self.graph_tab,
            bg="#0B131A",
            highlightthickness=0,
        )
        self.graph_canvas.pack(
            fill="both", expand=True, padx=8, pady=8
        )
        self.graph_canvas.bind(
            "<Configure>", lambda event: self.draw_graphs()
        )

        table_frame = ttk.Frame(self.table_tab, padding=8)
        table_frame.pack(fill="both", expand=True)

        columns = ("time", "height", "velocity", "acceleration")
        self.table = ttk.Treeview(
            table_frame, columns=columns, show="headings"
        )

        headings = [
            ("time", "Time (s)", 130),
            ("height", "Height (m)", 170),
            ("velocity", "Velocity (m/s)", 180),
            ("acceleration", "Acceleration (m/s²)", 210),
        ]

        for column, heading, width in headings:
            self.table.heading(column, text=heading)
            self.table.column(
                column, width=width, anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview,
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        footer = ttk.Frame(self.root, padding=(20, 0, 20, 12))
        footer.pack(fill="x")

        self.status = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.status).pack(anchor="w")

        self.draw_empty_message(
            self.trajectory_canvas,
            "Trajectory will appear here\nClick Simulate to begin",
        )
        self.draw_empty_message(
            self.graph_canvas,
            "Position, velocity and acceleration graphs\n"
            "will appear after a simulation",
        )

    def add_entry(self, parent, label, variable, row, column):
        field = ttk.Frame(parent, style="Panel.TFrame")
        field.grid(
            row=row, column=column, padx=6, pady=(4, 0), sticky="ew"
        )

        ttk.Label(
            field, text=label, style="Panel.TLabel"
        ).pack(anchor="w", pady=(0, 5))

        entry = ttk.Entry(field, textvariable=variable, width=15)
        entry.pack(fill="x")
        return entry

    def on_model_changed(self, event=None):
        """Enable aerodynamic fields only for the aerodynamic model."""
        enabled = self.model_var.get() == self.AERO_MODEL
        state = "normal" if enabled else "disabled"

        for entry in (self.mass_entry, self.drag_entry, self.area_entry):
            entry.configure(state=state)

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    def read_parameters(self):
        try:
            y0 = float(self.height_var.get().strip())
            v0 = float(self.velocity_var.get().strip())
            gravity = float(self.gravity_var.get().strip())
            dt = float(self.step_var.get().strip())
        except (ValueError, OverflowError) as error:
            raise ValueError(
                "Enter valid numbers for height, velocity, gravity and time step."
            ) from error

        if not all(math.isfinite(x) for x in (y0, v0, gravity, dt)):
            raise ValueError("All physical parameters must be finite.")

        if y0 < 0:
            raise ValueError("Initial height cannot be below ground.")

        if gravity <= 0:
            raise ValueError("Gravity must be greater than zero.")

        if not self.MIN_TIME_STEP <= dt <= self.MAX_TIME_STEP:
            raise ValueError("Time step must be between 0.01 and 10 seconds.")

        model = self.model_var.get()
        if model not in (self.IDEAL_MODEL, self.AERO_MODEL):
            raise ValueError("Select a valid physical model.")

        mass = 1.0
        drag_coefficient = 0.47
        area = 0.1

        if model == self.AERO_MODEL:
            try:
                mass = float(self.mass_var.get().strip())
                drag_coefficient = float(self.drag_var.get().strip())
                area = float(self.area_var.get().strip())
            except (ValueError, OverflowError) as error:
                raise ValueError(
                    "Enter valid numbers for mass, drag coefficient and area."
                ) from error

            if not all(
                math.isfinite(x)
                for x in (mass, drag_coefficient, area)
            ):
                raise ValueError("Aerodynamic parameters must be finite.")

            if mass <= 0:
                raise ValueError("Mass must be greater than zero.")

            if drag_coefficient < 0:
                raise ValueError("Drag coefficient cannot be negative.")

            if area < 0:
                raise ValueError("Frontal area cannot be negative.")

        return {
            "y0": y0,
            "v0": v0,
            "gravity": gravity,
            "dt": dt,
            "model": model,
            "mass": mass,
            "drag_coefficient": drag_coefficient,
            "area": area,
        }

    # --------------------------------------------------------
    # IDEAL PHYSICS WRAPPERS
    # --------------------------------------------------------

    def calculate_landing_time(self, y0, v0, gravity):
        return calculate_landing_time(y0, v0, gravity)

    def calculate_height(self, y0, v0, gravity, time):
        return calculate_height(y0, v0, gravity, time)

    def calculate_velocity(self, v0, gravity, time):
        return calculate_velocity(v0, gravity, time)

    def generate_simulation_data(self, y0, v0, gravity, dt, landing_time):
        if landing_time > self.MAX_FLIGHT_TIME:
            raise ValueError("Flight time exceeds the supported limit.")

        data = generate_simulation_data(
            y0, v0, gravity, dt, landing_time
        )

        if len(data) > self.MAX_DATA_POINTS:
            raise OverflowError(
                "Too many data points. Choose a larger time step."
            )

        return data

    # --------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------

    def simulate(self):
        self.reset()

        try:
            p = self.read_parameters()
            y0 = p["y0"]
            v0 = p["v0"]
            gravity = p["gravity"]
            dt = p["dt"]

            if p["model"] == self.IDEAL_MODEL:
                landing_time = self.calculate_landing_time(
                    y0, v0, gravity
                )

                data = self.generate_simulation_data(
                    y0, v0, gravity, dt, landing_time
                )

                if v0 > 0:
                    max_height = y0 + v0**2 / (2.0 * gravity)
                    peak_time = v0 / gravity
                else:
                    max_height = y0
                    peak_time = 0.0

            else:
                data = simulate_with_air_resistance(
                    initial_height=y0,
                    initial_velocity=v0,
                    gravity=gravity,
                    mass=p["mass"],
                    drag_coefficient=p["drag_coefficient"],
                    area=p["area"],
                    dt=dt,
                    max_steps=self.MAX_DATA_POINTS - 1,
                )

                landing_time = data[-1]["time"]

                if landing_time > self.MAX_FLIGHT_TIME:
                    raise ValueError(
                        "Flight time exceeds the supported limit."
                    )

                max_row = max(data, key=lambda row: row["height"])
                max_height = max_row["height"]
                peak_time = max_row["time"]

            if len(data) > self.MAX_DATA_POINTS:
                raise OverflowError(
                    "Too many data points. Choose a larger time step."
                )

            landing_velocity = data[-1]["velocity"]

            if not all(
                math.isfinite(value)
                for value in (
                    landing_time,
                    max_height,
                    peak_time,
                    landing_velocity,
                )
            ):
                raise ValueError("The simulation produced invalid results.")

        except (ValueError, OverflowError, RuntimeError) as error:
            messagebox.showerror("Simulation error", str(error))
            self.status.set("Simulation failed. Check the parameters.")
            return

        self.data = data
        self.parameters = {
            **p,
            "landing_time": landing_time,
            "max_height": max_height,
            "peak_time": peak_time,
        }
        self.animation_index = 0

        self.metric_labels["max_height"].configure(
            text=f"{max_height:.2f} m"
        )
        self.metric_labels["peak_time"].configure(
            text=f"{peak_time:.2f} s" if peak_time > 0 else "At start"
        )
        self.metric_labels["flight_time"].configure(
            text=f"{landing_time:.2f} s"
        )
        self.metric_labels["landing_speed"].configure(
            text=f"{abs(landing_velocity):.2f} m/s"
        )

        self.populate_table()
        self.draw_graphs()
        self.tabs.select(self.trajectory_tab)
        self.draw_trajectory()

        if len(data) <= 1 or landing_time == 0:
            self.play_button.configure(state="disabled")
            self.status.set("The object is already on the ground.")
            return

        self.play_button.configure(text="Pause", state="normal")
        self.status.set(
            f"{p['model']} | {len(data)} data points"
        )

        self.is_playing = True
        self.animate()

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    def animate(self):
        if not self.is_playing or not self.data:
            self.animation_job = None
            return

        self.draw_trajectory()

        if self.animation_index >= len(self.data) - 1:
            self.is_playing = False
            self.animation_job = None
            self.play_button.configure(text="Play")
            self.status.set(
                "Simulation complete. Review graphs or export CSV."
            )
            return

        self.animation_index += 1
        self.animation_job = self.root.after(45, self.animate)

    def toggle_play(self):
        if not self.data or not self.parameters:
            return

        if self.is_playing:
            self.is_playing = False
            self.stop_animation()
            self.play_button.configure(text="Play")
            self.status.set("Animation paused.")
        else:
            if self.animation_index >= len(self.data) - 1:
                self.animation_index = 0

            self.is_playing = True
            self.play_button.configure(text="Pause")
            self.status.set("Animation running.")
            self.animate()

    def stop_animation(self):
        self.is_playing = False

        if self.animation_job is not None:
            try:
                self.root.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            self.animation_job = None

    def reset(self):
        self.stop_animation()
        self.data = []
        self.parameters = None
        self.animation_index = 0

        for label in self.metric_labels.values():
            label.configure(text="—")

        for item in self.table.get_children():
            self.table.delete(item)

        self.play_button.configure(text="Pause", state="disabled")

        self.draw_empty_message(
            self.trajectory_canvas,
            "Trajectory will appear here\nClick Simulate to begin",
        )
        self.draw_empty_message(
            self.graph_canvas,
            "Position, velocity and acceleration graphs\n"
            "will appear after a simulation",
        )

        self.status.set("Reset complete. Ready for a new simulation.")

    # --------------------------------------------------------
    # TRAJECTORY VISUALIZATION
    # --------------------------------------------------------

    def draw_empty_message(self, canvas, text):
        canvas.delete("all")
        canvas.create_text(
            max(200, canvas.winfo_width() // 2),
            max(150, canvas.winfo_height() // 2),
            text=text,
            fill="#A9BDC9",
            font=("Segoe UI", 15),
            justify="center",
        )

    def draw_trajectory(self):
        canvas = self.trajectory_canvas
        if not self.data or not self.parameters:
            return

        canvas.delete("all")
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 300)

        max_height = max(max(row["height"] for row in self.data), 1.0)
        left, right = 85, width - 45
        top, bottom = 45, height - 55
        plot_height = max(bottom - top, 1)
        plot_width = max(right - left, 1)
        duration = max(self.data[-1]["time"], 1e-9)

        for index in range(6):
            fraction = index / 5
            y = bottom - plot_height * fraction

            canvas.create_line(left, y, right, y, fill="#233541")
            canvas.create_text(
                left - 10, y,
                text=f"{max_height * fraction:.1f}",
                fill="#A9BDC9",
                anchor="e",
            )

        canvas.create_line(left, top, left, bottom, fill="#718896", width=2)
        canvas.create_line(left, bottom, right, bottom, fill="#718896", width=2)

        canvas.create_text(
            left, 18,
            text="VERTICAL TRAJECTORY",
            fill="#FFFFFF",
            anchor="w",
            font=("Segoe UI", 12, "bold"),
        )
        canvas.create_text(
            22, (top + bottom) / 2,
            text="Height (m)",
            fill="#A9BDC9",
            angle=90,
        )
        canvas.create_text(
            (left + right) / 2, height - 20,
            text="Time (s) →",
            fill="#A9BDC9",
        )

        points = []
        for row in self.data:
            x = left + plot_width * row["time"] / duration
            y = bottom - plot_height * row["height"] / max_height
            points.extend([x, y])

        if len(points) >= 4:
            canvas.create_line(*points, fill="#00D6A3", width=3)

        current = self.data[
            min(self.animation_index, len(self.data) - 1)
        ]
        x = left + plot_width * current["time"] / duration
        y = bottom - plot_height * current["height"] / max_height

        canvas.create_oval(
            x - 8, y - 8, x + 8, y + 8,
            fill="#FFCC66", outline="#FFFFFF", width=2,
        )
        canvas.create_text(
            right, top + 5,
            text=f"Time: {current['time']:.2f} s",
            fill="#FFCC66",
            anchor="e",
            font=("Segoe UI", 11, "bold"),
        )
        canvas.create_text(
            right, top + 25,
            text=f"Height: {current['height']:.2f} m",
            fill="#A9BDC9",
            anchor="e",
        )

    # --------------------------------------------------------
    # GRAPHS
    # --------------------------------------------------------

    def draw_graphs(self):
        canvas = self.graph_canvas
        if not self.data:
            return

        canvas.delete("all")
        width = max(canvas.winfo_width(), 500)
        height = max(canvas.winfo_height(), 350)
        left, right = 85, width - 25
        plot_width = max(right - left, 1)
        section_height = max((height - 35) / 3, 1)
        duration = max(self.data[-1]["time"], 1e-9)

        specs = [
            ("height", "Position (m)", "#00D6A3"),
            ("velocity", "Velocity (m/s)", "#66B5FF"),
            ("acceleration", "Acceleration (m/s²)", "#FFCC66"),
        ]

        for index, (key, label, color) in enumerate(specs):
            section_top = 12 + index * section_height
            section_bottom = section_top + section_height - 22
            values = [row[key] for row in self.data]
            value_min, value_max = min(values), max(values)

            if abs(value_max - value_min) < 1e-9:
                value_min -= 1
                value_max += 1

            padding = (value_max - value_min) * 0.08
            value_min -= padding
            value_max += padding

            inner_top = section_top + 25
            inner_bottom = max(section_bottom, inner_top + 1)
            inner_height = inner_bottom - inner_top

            canvas.create_text(
                12, section_top + 8,
                text=label,
                fill=color,
                anchor="w",
                font=("Segoe UI", 10, "bold"),
            )

            for tick in range(3):
                fraction = tick / 2
                y = inner_bottom - inner_height * fraction
                value = value_min + (value_max - value_min) * fraction

                canvas.create_line(left, y, right, y, fill="#233541")
                canvas.create_text(
                    left - 8, y,
                    text=f"{value:.1f}",
                    fill="#A9BDC9",
                    anchor="e",
                    font=("Segoe UI", 8),
                )

            points = []
            for row in self.data:
                x = left + plot_width * row["time"] / duration
                y = inner_bottom - (
                    (row[key] - value_min)
                    / (value_max - value_min)
                ) * inner_height
                points.extend([x, y])

            if len(points) >= 4:
                canvas.create_line(*points, fill=color, width=2)

            canvas.create_line(
                left, inner_top, left, inner_bottom, fill="#718896"
            )
            canvas.create_line(
                left, inner_bottom, right, inner_bottom, fill="#718896"
            )

        canvas.create_text(
            right, height - 8,
            text="Time (s) →",
            fill="#A9BDC9",
            anchor="e",
        )

    # --------------------------------------------------------
    # DATA TABLE
    # --------------------------------------------------------

    def populate_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

        for row in self.data:
            self.table.insert(
                "",
                "end",
                values=(
                    f"{row['time']:.3f}",
                    f"{row['height']:.3f}",
                    f"{row['velocity']:.3f}",
                    f"{row['acceleration']:.3f}",
                ),
            )

    # --------------------------------------------------------
    # CSV EXPORT
    # --------------------------------------------------------

    def export_csv(self):
        if not self.data:
            messagebox.showinfo(
                "No data",
                "Run a simulation before exporting.",
            )
            return

        path = filedialog.asksaveasfilename(
            title="Export simulation data",
            defaultextension=".csv",
            initialfile="motion_simulation.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(
                path, "w", newline="", encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    "time_s",
                    "height_m",
                    "velocity_m_s",
                    "acceleration_m_s2",
                ])

                for row in self.data:
                    writer.writerow([
                        f"{row['time']:.8f}",
                        f"{row['height']:.8f}",
                        f"{row['velocity']:.8f}",
                        f"{row['acceleration']:.8f}",
                    ])

        except (OSError, csv.Error, ValueError) as error:
            messagebox.showerror("Export failed", str(error))
            self.status.set("CSV export failed.")
            return

        self.status.set(f"CSV exported successfully: {path}")
        messagebox.showinfo(
            "Export complete",
            "Simulation data exported successfully.",
        )


def main():
    root = tk.Tk()
    MotionSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
