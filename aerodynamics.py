
"""Vertical motion with quadratic air resistance.

Coordinate convention:
- Positive height and velocity point upward.
- Gravity always acts downward.
- Drag opposes the direction of motion.
"""

import math


AIR_DENSITY = 1.225  # kg/m³, approximately sea-level air


def calculate_acceleration(
    velocity,
    gravity,
    mass,
    drag_coefficient,
    area,
    air_density=AIR_DENSITY,
):
    """Calculate vertical acceleration including quadratic drag."""
    values = (
        velocity,
        gravity,
        mass,
        drag_coefficient,
        area,
        air_density,
    )

    if not all(math.isfinite(value) for value in values):
        raise ValueError("All parameters must be finite.")

    if gravity <= 0:
        raise ValueError("Gravity must be greater than zero.")
    if mass <= 0:
        raise ValueError("Mass must be greater than zero.")
    if drag_coefficient < 0:
        raise ValueError("Drag coefficient cannot be negative.")
    if area < 0:
        raise ValueError("Reference area cannot be negative.")
    if air_density < 0:
        raise ValueError("Air density cannot be negative.")

    drag_acceleration = (
        air_density
        * drag_coefficient
        * area
        * velocity
        * abs(velocity)
        / (2.0 * mass)
    )

    acceleration = -gravity - drag_acceleration

    if not math.isfinite(acceleration):
        raise ValueError("Calculated acceleration is not finite.")

    return acceleration


def simulate_with_air_resistance(
    initial_height,
    initial_velocity,
    gravity,
    mass,
    drag_coefficient,
    area,
    dt,
    air_density=AIR_DENSITY,
    max_steps=1_000_000,
):
    """Simulate vertical motion using fourth-order Runge-Kutta (RK4).

    Returns a list of dictionaries containing time, height, velocity,
    and acceleration. The final sample is placed at ground level.
    """
    parameters = (
        initial_height,
        initial_velocity,
        gravity,
        mass,
        drag_coefficient,
        area,
        dt,
        air_density,
    )

    if not all(math.isfinite(value) for value in parameters):
        raise ValueError("All simulation parameters must be finite.")

    if initial_height < 0:
        raise ValueError("Initial height cannot be negative.")
    if gravity <= 0:
        raise ValueError("Gravity must be greater than zero.")
    if mass <= 0:
        raise ValueError("Mass must be greater than zero.")
    if drag_coefficient < 0 or area < 0 or air_density < 0:
        raise ValueError("Aerodynamic parameters cannot be negative.")
    if dt <= 0:
        raise ValueError("Time step must be greater than zero.")
    if not isinstance(max_steps, int) or isinstance(max_steps, bool):
        raise ValueError("max_steps must be an integer.")
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1.")

    def acceleration(velocity):
        return calculate_acceleration(
            velocity,
            gravity,
            mass,
            drag_coefficient,
            area,
            air_density,
        )

    def derivatives(height, velocity):
        return velocity, acceleration(velocity)

    def rk4_step(height, velocity, step):
        k1_y, k1_v = derivatives(height, velocity)

        k2_y, k2_v = derivatives(
            height + 0.5 * step * k1_y,
            velocity + 0.5 * step * k1_v,
        )

        k3_y, k3_v = derivatives(
            height + 0.5 * step * k2_y,
            velocity + 0.5 * step * k2_v,
        )

        k4_y, k4_v = derivatives(
            height + step * k3_y,
            velocity + step * k3_v,
        )

        next_height = height + (
            step / 6.0
        ) * (k1_y + 2 * k2_y + 2 * k3_y + k4_y)

        next_velocity = velocity + (
            step / 6.0
        ) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)

        if not math.isfinite(next_height) or not math.isfinite(next_velocity):
            raise ValueError(
                "Simulation became numerically unstable. "
                "Try a smaller time step."
            )

        return next_height, next_velocity

    data = [{
        "time": 0.0,
        "height": initial_height,
        "velocity": initial_velocity,
        "acceleration": acceleration(initial_velocity),
    }]

    if initial_height == 0 and initial_velocity <= 0:
        return data

    time = 0.0
    height = initial_height
    velocity = initial_velocity

    for _ in range(max_steps):
        next_height, next_velocity = rk4_step(height, velocity, dt)
        next_time = time + dt


        if next_height <= 0:
            # Locate ground impact by repeatedly refining the
            # fractional RK4 step that brackets the event.
            low = 0.0
            high = 1.0

            for _ in range(50):
                fraction = 0.5 * (low + high)
                trial_height, _ = rk4_step(
                    height,
                    velocity,
                    dt * fraction,
                )

                if trial_height > 0:
                    low = fraction
                else:
                    high = fraction

            fraction = 0.5 * (low + high)

            landing_height, landing_velocity = rk4_step(
                height,
                velocity,
                dt * fraction,
            )

            landing_time = time + dt * fraction

            if not all(math.isfinite(value) for value in (
                landing_height,
                landing_velocity,
                landing_time,
            )):
                raise ValueError(
                    "Impact calculation produced a non-finite value."
                )

            data.append({
                "time": landing_time,
                "height": 0.0,
                "velocity": landing_velocity,
                "acceleration": acceleration(landing_velocity),
            })
            return data


        time = next_time
        height = next_height
        velocity = next_velocity

        data.append({
            "time": time,
            "height": height,
            "velocity": velocity,
            "acceleration": acceleration(velocity),
        })

    raise RuntimeError(
        "Maximum simulation steps reached before landing. "
        "Increase max_steps or check the simulation parameters."
    )
