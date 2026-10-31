"""ORYN/Dune Weaver theta-rho transform contract (pure math; no hardware I/O).

Mechanical sign and motor ratios come from the original Dune Weaver design.
Calibrated controller travel scales are supported without changing the coupling
relationship. A numerical parity test is NOT a substitute for verifying the
actual machine's axis wiring, gear ratio and physical calibration.
"""
from math import pi, isfinite
from dataclasses import dataclass


@dataclass(frozen=True)
class MotorDelta:
    x: float
    y: float
    radial: float
    coupling: float


def dune_coupled_delta(delta_theta: float, delta_rho: float, *,
                       x_steps: float, y_steps: float, gear_ratio: float,
                       table_type: str = 'kinetiq_motion',
                       theta_revolution_units: float | None = None,
                       rho_travel_units: float | None = None,
                       rho_direction: float = 1.0,
                       coupling_enabled: bool = True) -> MotorDelta:
    """Return controller-axis increments in the current machine frame.

    The uncalibrated branch reproduces the original Dune Weaver transform:
        dX = dTheta * 100/(2*pi*2)
        dY = dRho * 100/(3.7 for Mini else 5) +/- dX*Xsteps/(gear*Ysteps)
    Saved full-circle/perimeter calibration replaces only the geometry scales.
    """
    quantities = [delta_theta, delta_rho, x_steps, y_steps, gear_ratio, rho_direction]
    if theta_revolution_units is not None: quantities.append(theta_revolution_units)
    if rho_travel_units is not None: quantities.append(rho_travel_units)
    if not all(isfinite(float(v)) for v in quantities):
        raise ValueError('Non-finite motor calibration/coordinate')
    if x_steps <= 0 or y_steps <= 0 or gear_ratio <= 0:
        raise ValueError('Motion requires positive X/Y steps and gear ratio')
    if theta_revolution_units is not None and theta_revolution_units == 0:
        raise ValueError('Full-circle calibration cannot be zero')
    if rho_travel_units is not None and rho_travel_units <= 0:
        raise ValueError('Perimeter calibration must be positive')
    if rho_direction == 0:
        raise ValueError('Perimeter direction cannot be zero')
    mini = table_type == 'kinetiq_motion_mini'
    dx = (delta_theta / (2*pi) * theta_revolution_units) if theta_revolution_units is not None else delta_theta * 100/(2*pi*2)
    dr = delta_rho * (rho_travel_units * rho_direction if rho_travel_units is not None else 100/(3.7 if mini else 5))
    # Legacy Dune Weaver's special winding also applies to Y=546 steps/mm.
    winding = -1.0 if mini or abs(y_steps-546) <= 5 else 1.0
    coupling = dx * (x_steps / (gear_ratio * y_steps)) * winding * (rho_direction if rho_travel_units is not None else 1.0) if coupling_enabled else 0.0
    return MotorDelta(x=dx, y=dr+coupling, radial=dr, coupling=coupling)


def validate_thr_coordinates(coordinates):
    """Stop invalid THR coordinates before they reach the controller.

    Never silently clamp a design or move beyond the nominal 0..1 radius.
    The original THR file remains unchanged on disk.
    """
    for index, (theta, rho) in enumerate(coordinates):
        if not (isfinite(float(theta)) and isfinite(float(rho))):
            raise ValueError(f'THR point {index}: non-finite theta/rho')
        if float(rho) < 0.0 or float(rho) > 1.0:
            raise ValueError(f'THR point {index}: rho {rho} outside 0..1')
    return True
