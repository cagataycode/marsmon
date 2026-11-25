"""Mars seasons: solar longitude (Ls) and Mars Year (MY) from a UTC time.

Ls uses the Allison & McEwen (2000) algorithm, as in NASA GISS Mars24.
Mars Years follow the Clancy et al. (2000) convention: MY1 began on 11 Apr 1955.
Ls 0 is northern spring equinox, 90 northern summer solstice, 180 autumn, 270 winter.
"""
import datetime as dt
import math

TT_MINUS_UTC_S = 69.184  # 37 leap seconds + 32.184 s; constant since 2017
MY1_START = dt.datetime(1955, 4, 11, tzinfo=dt.timezone.utc)
MARS_YEAR_DAYS = 686.9726
SOL_S = 88775.244  # mean solar day on Mars, in seconds

# Start of sol 0 (local midnight) for each rover, in UTC.
# Landing UTC minus the local mean solar time at landing, converted to Earth seconds.
SOL0 = {
    # Perseverance landed 2021-02-18 20:55 UTC at about 15:53 LMST.
    "m20": dt.datetime(2021, 2, 18, 20, 55, tzinfo=dt.timezone.utc) - dt.timedelta(seconds=(15 * 3600 + 53 * 60) * SOL_S / 86400),
    # Curiosity landed 2012-08-06 05:17:57 UTC at about 15:00 LMST.
    "msl": dt.datetime(2012, 8, 6, 5, 17, 57, tzinfo=dt.timezone.utc) - dt.timedelta(seconds=15 * 3600 * SOL_S / 86400),
}

_PERTURBATIONS = [
    (0.0071, 2.2353, 49.409), (0.0057, 2.7543, 168.173), (0.0039, 1.1177, 191.837),
    (0.0037, 15.7866, 21.736), (0.0021, 2.1354, 15.704), (0.0020, 2.4694, 95.528),
    (0.0018, 32.8493, 49.095),
]


def _days_since_j2000_tt(t: dt.datetime) -> float:
    jd_utc = t.timestamp() / 86400 + 2440587.5
    return jd_utc + TT_MINUS_UTC_S / 86400 - 2451545.0


def ls(t: dt.datetime) -> float:
    """Solar longitude in degrees [0, 360) for an aware UTC datetime."""
    d = _days_since_j2000_tt(t)
    m = math.radians(19.3871 + 0.52402073 * d)
    alpha_fms = 270.3871 + 0.524038496 * d
    pbs = sum(a * math.cos(math.radians(0.985626 * d / tau + phi)) for a, tau, phi in _PERTURBATIONS)
    eoc = ((10.691 + 3.0e-7 * d) * math.sin(m) + 0.623 * math.sin(2 * m) + 0.050 * math.sin(3 * m)
           + 0.005 * math.sin(4 * m) + 0.0005 * math.sin(5 * m) + pbs)
    return (alpha_fms + eoc) % 360


def mars_year(t: dt.datetime) -> int:
    """Mars Year number. Uses Ls to settle times near the year boundary."""
    years = (t - MY1_START).total_seconds() / 86400 / MARS_YEAR_DAYS
    my = 1 + int(years // 1)
    frac = years % 1
    lon = ls(t)
    if frac > 0.9 and lon < 30:
        my += 1
    elif frac < 0.1 and lon > 330:
        my -= 1
    return my


def sol_to_utc(rover: str, sol: float) -> dt.datetime:
    """UTC time at a (fractional) sol; sol 12.5 is local noon of sol 12. Accurate to minutes."""
    return SOL0[rover] + dt.timedelta(seconds=SOL_S * sol)


def parse_utc(s: str) -> dt.datetime:
    """Parse the API's UTC strings ('2026-11-07T11:12:25.917', with or without 'Z')."""
    s = s.rstrip("Z")[:19]
    return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)


def season_name(lon: float) -> str:
    """Northern-hemisphere season name for an Ls (both rovers are near the equator)."""
    return ["northern spring", "northern summer", "northern autumn", "northern winter"][int(lon // 90) % 4]
