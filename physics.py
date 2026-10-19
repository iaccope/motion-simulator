
"""Physical calculations for the Motion Simulator.

Vertical motion under constant gravity, without air resistance.
The positive direction is upward.
"""

import math


MAX_DATA_POINTS = 20000
MIN_TIME_STEP = 0.01
MAX_TIME_STEP = 10.0


def calculate_height(y0, v0, gravity, time):
    """Return the object's height at a given time."""
    return y0 + v0 * time - 0.5 * gravity * time**2


def calculate_velocity(v0, gravity, time):
    """Return the object's vertical velocity at a given time."""
    return v0 - gravity * time


def calculate_landing_time(y0, v0, gravity):
    """Calculate the first nonnegative time when the object reaches ground."""
    values = (y0, v0, gravity)

    if not all(math.isfinite(value) for value in values):
        raise ValueError("All physical parameters must be finite.")

    if y0 < 0:
        raise ValueError("Initial height cannot be negative.")

    if gravity <= 0:
        raise ValueError("Gravity must be greater than zero.")

    if y0 == 0 and v0 <= 0:
        return 0.0

    try:
        discriminant = v0**2 + 2.0 * gravity * y0

        if not math.isfinite(discriminant):
            raise ValueError("The calculated values are too large.")

        root = math.sqrt(discriminant)

        # The rationalized form avoids loss of precision for v0 < 0.
        if v0 < 0:
            denominator = root - v0
            landing_time = 2.0 * y0 / denominator
        else:
            landing_time = (v0 + root) / gravity

    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("Unable to calculate landing time.") from exc

    if not math.isfinite(landing_time) or landing_time < 0:
        raise ValueError("The calculated landing time is invalid.")

    return landing_time


def generate_simulation_data(y0, v0, gravity, dt, landing_time):
    """Generate time, height, velocity and acceleration samples."""
    values = (y0, v0, gravity, dt, landing_time)

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Simulation parameters must be finite.")

    if y0 < 0:
        raise ValueError("Initial height cannot be negative.")

    if gravity <= 0:
        raise ValueError("Gravity must be greater than zero.")

    if not MIN_TIME_STEP <= dt <= MAX_TIME_STEP:
        raise ValueError(
            f"Time step must be between "
            f"{MIN_TIME_STEP} and {MAX_TIME_STEP} seconds."
        )

    if landing_time < 0:
        raise ValueError("Landing time cannot be negative.")

    if landing_time == 0:
        return [{
            "time": 0.0,
            "height": 0.0,
            "velocity": v0,
            "acceleration": -gravity,
        }]

    data = [{
        "time": 0.0,
        "height": y0,
        "velocity": v0,
        "acceleration": -gravity,
    }]

    for index in range(1, MAX_DATA_POINTS):
        time = index * dt

        if time >= landing_time:
            break

        height = calculate_height(y0, v0, gravity, time)
        velocity = calculate_velocity(v0, gravity, time)

        if not math.isfinite(height) or not math.isfinite(velocity):
            raise ValueError("Simulation produced a non-finite value.")

        if height < 0:
            raise ValueError("Calculated height fell below ground.")

        data.append({
            "time": time,
            "height": height,
            "velocity": velocity,
            "acceleration": -gravity,
        })

    final_velocity = calculate_velocity(v0, gravity, landing_time)

    if not math.isfinite(final_velocity):
        raise ValueError("Final velocity is not finite.")

    data.append({
        "time": landing_time,
        "height": 0.0,
        "velocity": final_velocity,
        "acceleration": -gravity,
    })

    return data
