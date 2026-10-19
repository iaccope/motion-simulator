
import math
import unittest

from main import MotionSimulator


class TestSimulationData(unittest.TestCase):

    def setUp(self):
        # Create an instance without opening the Tkinter window.
        self.simulator = object.__new__(MotionSimulator)

    def test_landing_time_for_downward_launch(self):
        y0 = 100.0
        v0 = -10.0
        gravity = 9.81

        flight_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        self.assertAlmostEqual(
            flight_time, 3.60950562, places=7
        )

    def test_final_height_is_zero(self):
        y0 = 100.0
        v0 = -10.0
        gravity = 9.81

        flight_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        final_height = self.simulator.calculate_height(
            y0, v0, gravity, flight_time
        )

        self.assertAlmostEqual(final_height, 0.0, places=8)

    def test_final_velocity_is_downward(self):
        y0 = 100.0
        v0 = -10.0
        gravity = 9.81

        flight_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        final_velocity = self.simulator.calculate_velocity(
            v0, gravity, flight_time
        )

        self.assertAlmostEqual(
            final_velocity, -45.40925016, places=7
        )
        self.assertLess(final_velocity, 0)

    def test_object_at_ground_with_zero_velocity(self):
        flight_time = self.simulator.calculate_landing_time(
            0.0, 0.0, 9.81
        )

        self.assertAlmostEqual(flight_time, 0.0)

    def test_object_at_ground_moving_downward(self):
        flight_time = self.simulator.calculate_landing_time(
            0.0, -5.0, 9.81
        )

        self.assertAlmostEqual(flight_time, 0.0)

    def test_height_and_velocity_follow_equations(self):
        y0 = 25.0
        v0 = 15.0
        gravity = 9.81
        time = 1.25

        expected_height = (
            y0 + v0 * time - 0.5 * gravity * time**2
        )
        expected_velocity = v0 - gravity * time

        height = self.simulator.calculate_height(
            y0, v0, gravity, time
        )
        velocity = self.simulator.calculate_velocity(
            v0, gravity, time
        )

        self.assertAlmostEqual(height, expected_height)
        self.assertAlmostEqual(velocity, expected_velocity)

    def test_generated_data_starts_at_initial_height(self):
        landing_time = self.simulator.calculate_landing_time(
            100.0, -10.0, 9.81
        )

        data = self.simulator.generate_simulation_data(
            100.0, -10.0, 9.81, 0.1, landing_time
        )

        self.assertAlmostEqual(data[0]["time"], 0.0)
        self.assertAlmostEqual(data[0]["height"], 100.0)

    def test_generated_data_ends_at_ground(self):
        y0, v0, gravity = 100.0, -10.0, 9.81
        landing_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        data = self.simulator.generate_simulation_data(
            y0, v0, gravity, 0.1, landing_time
        )

        self.assertAlmostEqual(data[-1]["time"], landing_time)
        self.assertEqual(data[-1]["height"], 0.0)
        self.assertLess(data[-1]["velocity"], 0.0)

    def test_generated_data_has_constant_acceleration(self):
        y0, v0, gravity = 100.0, 20.0, 9.81
        landing_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        data = self.simulator.generate_simulation_data(
            y0, v0, gravity, 0.1, landing_time
        )

        for row in data:
            self.assertAlmostEqual(
                row["acceleration"], -gravity
            )

    def test_generated_data_times_are_increasing(self):
        y0, v0, gravity = 100.0, 20.0, 9.81
        landing_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        data = self.simulator.generate_simulation_data(
            y0, v0, gravity, 0.1, landing_time
        )
        times = [row["time"] for row in data]

        self.assertTrue(
            all(
                current > previous
                for previous, current in zip(times, times[1:])
            )
        )

    # New tests: edge cases and data validation.

    def test_no_negative_heights(self):
        """No generated sample should be below ground."""
        y0, v0, gravity, dt = 100.0, 0.0, 9.81, 0.1
        landing_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        data = self.simulator.generate_simulation_data(
            y0, v0, gravity, dt, landing_time
        )

        for row in data:
            self.assertGreaterEqual(row["height"], 0.0)

    def test_all_generated_values_are_finite(self):
        """Generated values must not be NaN or infinite."""
        y0, v0, gravity, dt = 100.0, 0.0, 9.81, 0.1
        landing_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        data = self.simulator.generate_simulation_data(
            y0, v0, gravity, dt, landing_time
        )

        for row in data:
            for key in ("time", "height", "velocity", "acceleration"):
                with self.subTest(key=key, row=row):
                    self.assertTrue(math.isfinite(row[key]))

    def test_landing_time_is_zero_at_ground_when_moving_down(self):
        """An object at ground moving downward has zero flight time."""
        flight_time = self.simulator.calculate_landing_time(
            0.0, -10.0, 9.81
        )

        self.assertEqual(flight_time, 0.0)

    def test_landing_height_is_exactly_zero(self):
        """The last sample must be exactly at ground level."""
        y0, v0, gravity, dt = 100.0, 0.0, 9.81, 0.1
        landing_time = self.simulator.calculate_landing_time(
            y0, v0, gravity
        )

        data = self.simulator.generate_simulation_data(
            y0, v0, gravity, dt, landing_time
        )

        self.assertEqual(data[-1]["height"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
