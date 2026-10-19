# Motion Simulator

A Python-based physics simulation project for modeling vertical motion with and without quadratic air resistance. The project combines analytical equations, numerical integration, automated tests, and numerical convergence analysis.

## Features

- Ideal vertical motion under constant gravitational acceleration
- Vertical motion with quadratic aerodynamic drag
- Fourth-order Runge–Kutta (RK4) numerical integration
- Ground-impact event localization using bisection
- Simulation data generation for height, velocity, and acceleration
- Automated unit tests for physics and numerical behavior
- Time-step convergence study for aerodynamic simulations

## Physical Models

### 1. Motion without air resistance

The ideal model assumes constant gravitational acceleration and no aerodynamic forces.

Height:

\[
y(t)=y_0+v_0t-\frac{1}{2}gt^2
\]

Vertical velocity:

\[
v(t)=v_0-gt
\]

where:

- \(y_0\) is the initial height
- \(v_0\) is the initial vertical velocity
- \(g\) is gravitational acceleration
- \(t\) is elapsed time

The positive vertical direction is upward.

### 2. Motion with quadratic air resistance

The aerodynamic model assumes still air, constant air density, and a constant drag coefficient and reference area.

The drag force is modeled as:

\[
F_d=-\frac{1}{2}\rho C_d A v|v|
\]

The equation of motion is:

\[
\frac{dv}{dt}=-g-\frac{\rho C_d A}{2m}v|v|
\]

where:

- \(\rho\) is air density
- \(C_d\) is the drag coefficient
- \(A\) is the reference area
- \(m\) is object mass
- \(v\) is vertical velocity

The differential equations are integrated using the fourth-order Runge–Kutta method (RK4). Ground impact is located by refining the final integration step with bisection.

## Validation

The project includes automated tests covering:

- Analytical height and velocity equations
- Initial and boundary conditions
- Upward and downward launches
- Aerodynamic drag direction
- Zero-drag behavior
- Ground-impact handling
- Finite simulation values
- Time-step sensitivity

The current test suite contains **28 tests**.

A convergence study compares simulations with time steps of 0.20, 0.10, 0.05, and 0.01 seconds.

| Time step (s) | Maximum height (m) | Flight time (s) | Impact speed (m/s) |
|---:|---:|---:|---:|
| 0.20 | 113.486062 | 9.004573 | 18.446616 |
| 0.10 | 113.486345 | 9.004565 | 18.446617 |
| 0.05 | 113.486371 | 9.004564 | 18.446617 |
| 0.01 | 113.486371 | 9.004564 | 18.446617 |

These values are from the current validation scenario. The finest time step is used as a numerical reference, not as an exact solution.

## Requirements

- Python 3
- No third-party packages are required for the core physics tests, assuming the project remains compatible with the Python standard library.

## Run the Simulator

From the project directory:

```powershell
py main.py
```

## Run Automated Tests

```powershell
py -m unittest -v
```

## Run the Aerodynamic Convergence Study

```powershell
py validate_aerodynamics.py
```

## Project Structure

```text
motion-simulator/
├── aerodynamics.py
├── main.py
├── physics.py
├── test_aerodynamics.py
├── test_physics.py
├── test_simulation_data.py
├── validate_aerodynamics.py
├── .gitignore
└── README.md
```

## Assumptions and Limitations

- Motion is restricted to one vertical dimension.
- Gravitational acceleration is constant.
- Air density is constant.
- The drag coefficient and reference area do not vary with velocity or orientation.
- Wind, lift, buoyancy, and changes in atmospheric conditions are not modeled.
- Numerical convergence supports the consistency of the computation but does not independently establish experimental accuracy.

## Future Improvements

- Add plots comparing ideal and aerodynamic trajectories.
- Add configurable simulation scenarios and parameter sweeps.
- Export simulation results to CSV.
- Expand numerical validation with independent reference solutions.
- Add continuous integration for automated testing.

## License

No license has been specified yet. A license should be selected before the project is redistributed or reused by others.
