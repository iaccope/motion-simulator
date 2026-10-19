
import math
import unittest

from main import MotionSimulator


class TestMotionPhysics(unittest.TestCase):
    """Tests for the simulator's mathematical calculations."""

    def setUp(self):
        # Create an instance without initializing the Tkinter interface.
        self.physics = object.__new__(MotionSimulator)

    def test_height_at_initial_time(self):
        height = self.physics.calculate_height(
            100.0, -10.0, 9.81, 0.0
        )
        self.assertAlmostEqual(height, 100.0, places=8)

    def test_velocity_changes_with_gravity(self):
        velocity = self.physics.calculate_velocity(
            -10.0, 9.81, 1.0
        )
        self.assertAlmostEqual(velocity, -19.81, places=8)

    def test_upward_launch_returns_to_initial_level(self):
        flight_time = self.physics.calculate_landing_time(
            0.0, 40.0, 9.81
        )
        self.assertAlmostEqual(
            flight_time, 80.0 / 9.81, places=8
        )

        final_velocity = self.physics.calculate_velocity(
            40.0, 9.81, flight_time
        )
        self.assertAlmostEqual(final_velocity, -40.0, places=8)

    def test_downward_launch_from_height(self):
        flight_time = self.physics.calculate_landing_time(
            100.0, -10.0, 9.81
        )
        self.assertAlmostEqual(flight_time, 3.60950562, places=7)

        final_height = self.physics.calculate_height(
            100.0, -10.0, 9.81, flight_time
        )
        self.assertAlmostEqual(final_height, 0.0, places=8)

        final_velocity = self.physics.calculate_velocity(
            -10.0, 9.81, flight_time
        )
        self.assertAlmostEqual(
            final_velocity, -45.40925016, places=7
        )

    def test_object_already_on_ground_and_moving_down(self):
        flight_time = self.physics.calculate_landing_time(
            0.0, -5.0, 9.81
        )
        self.assertAlmostEqual(flight_time, 0.0, places=8)

    def test_height_formula(self):
        # h = h0 + v0*t - 0.5*g*t²
        height = self.physics.calculate_height(
            20.0, 15.0, 9.81, 1.0
        )
        expected = 20.0 + 15.0 - 0.5 * 9.81
        self.assertAlmostEqual(height, expected, places=8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
