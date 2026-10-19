
"""Tests for vertical motion with quadratic air resistance."""

import math
import unittest

from aerodynamics import (
    AIR_DENSITY,
    calculate_acceleration,
    simulate_with_air_resistance,
)


class TestAerodynamics(unittest.TestCase):
    """Validate aerodynamic calculations and numerical integration."""

    def test_drag_reduces_upward_acceleration(self):
        """Drag should reduce upward acceleration."""
        gravity = 9.81
        velocity = 20.0

        acceleration_without_drag = calculate_acceleration(
            velocity=velocity,
            gravity=gravity,
            mass=1.0,
            drag_coefficient=0.47,
            area=0.01,
            air_density=0.0,
        )

        acceleration_with_drag = calculate_acceleration(
            velocity=velocity,
            gravity=gravity,
            mass=1.0,
            drag_coefficient=0.47,
            area=0.01,
            air_density=AIR_DENSITY,
        )

        self.assertLess(
            acceleration_with_drag,
            acceleration_without_drag,
        )

    def test_drag_reduces_downward_acceleration_magnitude(self):
        """Drag should oppose downward motion."""
        gravity = 9.81
        velocity = -20.0

        acceleration_without_drag = calculate_acceleration(
            velocity=velocity,
            gravity=gravity,
            mass=1.0,
            drag_coefficient=0.47,
            area=0.01,
            air_density=0.0,
        )

        acceleration_with_drag = calculate_acceleration(
            velocity=velocity,
            gravity=gravity,
            mass=1.0,
            drag_coefficient=0.47,
            area=0.01,
            air_density=AIR_DENSITY,
        )

        self.assertGreater(
            acceleration_with_drag,
            acceleration_without_drag,
        )

        self.assertLess(acceleration_with_drag, 0.0)

    def test_zero_drag_matches_ideal_motion(self):
        """With zero drag, flight time should match the analytical result."""
        initial_height = 100.0
        initial_velocity = 20.0
        gravity = 9.81

        exact_landing_time = (
            initial_velocity
            + math.sqrt(
                initial_velocity**2
                + 2.0 * gravity * initial_height
            )
        ) / gravity

        result = simulate_with_air_resistance(
            initial_height=initial_height,
            initial_velocity=initial_velocity,
            gravity=gravity,
            mass=1.0,
            drag_coefficient=0.0,
            area=0.0,
            dt=0.2,
        )

        self.assertAlmostEqual(
            result[-1]["time"],
            exact_landing_time,
            delta=0.002,
        )

    def test_simulation_lands_at_ground(self):
        """The final sample should be at ground level."""
        result = simulate_with_air_resistance(
            initial_height=100.0,
            initial_velocity=20.0,
            gravity=9.81,
            mass=1.0,
            drag_coefficient=0.47,
            area=0.01,
            dt=0.05,
        )

        self.assertEqual(result[-1]["height"], 0.0)

        for sample in result:
            self.assertGreaterEqual(sample["height"], 0.0)

        times = [sample["time"] for sample in result]
        self.assertTrue(
            all(
                later > earlier
                for earlier, later in zip(times, times[1:])
            )
        )

    def test_drag_parameters_must_be_valid(self):
        """Invalid physical parameters should raise ValueError."""
        invalid_cases = [
            {"gravity": 0.0},
            {"mass": 0.0},
            {"drag_coefficient": -0.1},
            {"area": -0.1},
            {"air_density": -0.1},
            {"velocity": math.inf},
        ]

        defaults = {
            "velocity": 10.0,
            "gravity": 9.81,
            "mass": 1.0,
            "drag_coefficient": 0.47,
            "area": 0.01,
            "air_density": AIR_DENSITY,
        }

        for overrides in invalid_cases:
            parameters = {**defaults, **overrides}

            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    calculate_acceleration(**parameters)

    def test_simulation_rejects_zero_time_step(self):
        """The integration time step must be positive."""
        with self.assertRaises(ValueError):
            simulate_with_air_resistance(
                initial_height=100.0,
                initial_velocity=20.0,
                gravity=9.81,
                mass=1.0,
                drag_coefficient=0.47,
                area=0.01,
                dt=0.0,
            )

    def test_zero_drag_matches_analytical_trajectory(self):
        """RK4 should reproduce the ideal trajectory without drag."""
        initial_height = 100.0
        initial_velocity = 20.0
        gravity = 9.81
        dt = 0.1

        result = simulate_with_air_resistance(
            initial_height=initial_height,
            initial_velocity=initial_velocity,
            gravity=gravity,
            mass=1.0,
            drag_coefficient=0.0,
            area=0.0,
            dt=dt,
        )

        # Exclude the final ground-impact sample because its time
        # is event-localized and may not be a multiple of dt.
        for sample in result[:-1]:
            time = sample["time"]

            expected_height = (
                initial_height
                + initial_velocity * time
                - 0.5 * gravity * time**2
            )

            expected_velocity = initial_velocity - gravity * time

            with self.subTest(time=time):
                self.assertAlmostEqual(
                    sample["height"],
                    expected_height,
                    delta=1e-8,
                )

                self.assertAlmostEqual(
                    sample["velocity"],
                    expected_velocity,
                    delta=1e-8,
                )

    def test_smaller_time_step_improves_landing_time(self):
        """A smaller time step should improve landing-time accuracy."""
        parameters = {
            "initial_height": 100.0,
            "initial_velocity": 20.0,
            "gravity": 9.81,
            "mass": 1.0,
            "drag_coefficient": 0.47,
            "area": 0.01,
        }

        landing_times = {}

        for dt in (0.2, 0.1, 0.05, 0.005):
            result = simulate_with_air_resistance(
                **parameters,
                dt=dt,
            )
            landing_times[dt] = result[-1]["time"]

        reference_time = landing_times[0.005]
        coarse_error = abs(landing_times[0.2] - reference_time)
        fine_error = abs(landing_times[0.05] - reference_time)

        self.assertLess(
            fine_error,
            coarse_error,
            msg=(
                "Reducing dt from 0.2 s to 0.05 s should reduce "
                "the landing-time error relative to the reference."
            ),
        )


if __name__ == "__main__":
    unittest.main()
