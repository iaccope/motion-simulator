
"""Numerical convergence study for the aerodynamic motion simulator."""

import math

from aerodynamics import simulate_with_air_resistance


def estimate_peak(data):
    """Estimate the maximum height using parabolic interpolation.

    The data must contain time, height, and velocity fields.
    The estimated peak is calculated around the sample where velocity
    changes from positive to non-positive.
    """
    if not data:
        raise ValueError("Simulation data cannot be empty.")

    peak_index = max(
        range(len(data)),
        key=lambda index: data[index]["height"],
    )

    # If the maximum is at an endpoint, no two-sided interpolation
    # is possible.
    if peak_index == 0 or peak_index == len(data) - 1:
        sample = data[peak_index]
        return sample["time"], sample["height"]

    before = data[peak_index - 1]
    peak = data[peak_index]
    after = data[peak_index + 1]

    t1, h1 = before["time"], before["height"]
    t2, h2 = peak["time"], peak["height"]
    t3, h3 = after["time"], after["height"]

    # Fit a parabola through three points using a local time coordinate.
    # This formula works for equally or unequally spaced time samples.
    x1 = t1 - t2
    x3 = t3 - t2

    denominator = x1 * x3 * (x1 - x3)

    if abs(denominator) < 1e-15:
        return t2, h2

    # h(x) = a*x^2 + b*x + c, with x = t - t2 and c = h2.
    a = (
        x3 * (h1 - h2) - x1 * (h3 - h2)
    ) / denominator

    b = (
        x1**2 * (h3 - h2) - x3**2 * (h1 - h2)
    ) / denominator

    if a >= 0:
        return t2, h2

    peak_offset = -b / (2.0 * a)

    # Only accept the estimated peak if it lies between the neighbors.
    if not x1 <= peak_offset <= x3:
        return t2, h2

    estimated_height = a * peak_offset**2 + b * peak_offset + h2
    estimated_time = t2 + peak_offset

    return estimated_time, estimated_height


def run_simulation(dt, parameters):
    """Run one aerodynamic simulation and summarize its results."""
    data = simulate_with_air_resistance(
        initial_height=parameters["initial_height"],
        initial_velocity=parameters["initial_velocity"],
        gravity=parameters["gravity"],
        mass=parameters["mass"],
        drag_coefficient=parameters["drag_coefficient"],
        area=parameters["area"],
        dt=dt,
    )

    peak_time, peak_height = estimate_peak(data)

    return {
        "dt": dt,
        "samples": len(data),
        "peak_time": peak_time,
        "maximum_height": peak_height,
        "flight_time": data[-1]["time"],
        "impact_speed": abs(data[-1]["velocity"]),
        "landing_height": data[-1]["height"],
    }


def run_validation():
    """Compare results for progressively smaller time steps."""
    parameters = {
        "initial_height": 100.0,   # m
        "initial_velocity": 20.0,  # m/s, upward
        "gravity": 9.81,           # m/s²
        "mass": 1.0,                # kg
        "drag_coefficient": 0.47,
        "area": 0.1,                # m²
    }

    time_steps = [0.2, 0.1, 0.05, 0.01]
    results = []

    print("\nAERODYNAMIC SIMULATOR - CONVERGENCE STUDY")
    print("=" * 105)
    print(
        f"{'dt (s)':>8} | {'Samples':>8} | {'Peak time (s)':>14} | "
        f"{'Max height (m)':>16} | {'Flight time (s)':>16} | "
        f"{'Impact speed (m/s)':>19}"
    )
    print("-" * 105)

    for dt in time_steps:
        result = run_simulation(dt, parameters)
        results.append(result)

        print(
            f"{dt:8.3f} | {result['samples']:8d} | "
            f"{result['peak_time']:14.6f} | "
            f"{result['maximum_height']:16.6f} | "
            f"{result['flight_time']:16.6f} | "
            f"{result['impact_speed']:19.6f}"
        )

    reference = results[-1]

    print("\nDIFFERENCE FROM THE FINEST TIME STEP")
    print("=" * 105)
    print(
        f"{'dt (s)':>8} | {'Peak time error (s)':>20} | "
        f"{'Height error (m)':>18} | {'Flight time error (s)':>22} | "
        f"{'Impact speed error (m/s)':>25}"
    )
    print("-" * 105)

    for result in results:
        print(
            f"{result['dt']:8.3f} | "
            f"{abs(result['peak_time'] - reference['peak_time']):20.10f} | "
            f"{abs(result['maximum_height'] - reference['maximum_height']):18.10f} | "
            f"{abs(result['flight_time'] - reference['flight_time']):22.10f} | "
            f"{abs(result['impact_speed'] - reference['impact_speed']):25.10f}"
        )

    print("\nVALIDATION CHECKS")
    print("=" * 60)

    all_landings_valid = all(
        math.isclose(
            result["landing_height"],
            0.0,
            abs_tol=1e-12,
        )
        for result in results
    )

    print(f"All simulations end at ground level: {all_landings_valid}")

    # Check whether errors relative to the reference do not increase
    # as the time step is reduced.
    metrics = (
        "peak_time",
        "maximum_height",
        "flight_time",
        "impact_speed",
    )

    for metric in metrics:
        errors = [
            abs(result[metric] - reference[metric])
            for result in results
        ]

        converges = all(
            errors[index + 1] <= errors[index] + 1e-10
            for index in range(len(errors) - 2)
        )

        print(f"{metric.replace('_', ' ').capitalize()} converges: {converges}")

    print(
        "\nNote: dt = 0.01 s is a numerical reference, not an exact solution."
    )
    print(
        "Parabolic interpolation improves the peak estimate, but "
        "does not replace independent numerical validation."
    )


if __name__ == "__main__":
    run_validation()
