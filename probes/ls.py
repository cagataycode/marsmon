"""Mars solar longitude (Ls) and Mars Year from UTC, Allison & McEwen (2000) / Mars24 algorithm."""
import math, datetime as dt
def jd_tt(t):
    jd_ut = t.timestamp()/86400 + 2440587.5
    return jd_ut + 69.184/86400  # TT-UTC (37 leap s + 32.184)
def ls(t):
    d = jd_tt(t) - 2451545.0
    M = math.radians(19.3871 + 0.52402073*d)
    a_fms = 270.3871 + 0.524038496*d
    pbs = 0.0
    for A,tau,phi in [(0.0071,2.2353,49.409),(0.0057,2.7543,168.173),(0.0039,1.1177,191.837),(0.0037,15.7866,21.736),(0.0021,2.1354,15.704),(0.0020,2.4694,95.528),(0.0018,32.8493,49.095)]:
        pbs += A*math.cos(math.radians(0.985626*d/tau + phi))
    nu_m = (10.691+3.0e-7*d)*math.sin(M) + 0.623*math.sin(2*M) + 0.050*math.sin(3*M) + 0.005*math.sin(4*M) + 0.0005*math.sin(5*M) + pbs
    return (a_fms + nu_m) % 360
MY1_START = dt.datetime(1955,4,11,tzinfo=dt.timezone.utc)   # Clancy et al. convention
MY_LEN = 686.9726
def mars_year(t):
    # approximate then fix using Ls near the year boundary
    my = 1 + int((t - MY1_START).total_seconds()/86400 // MY_LEN)
    L = ls(t)
    frac = ((t - MY1_START).total_seconds()/86400 / MY_LEN) % 1
    if frac > 0.9 and L < 30: my += 1
    if frac < 0.1 and L > 330: my -= 1
    return my
