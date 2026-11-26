"""Read-only theoretical monoisotopic electrospray ions for verified products.

Calculated from exact neutral mass of a sanitized molecular graph, NOT from
average mass or an observed LC-MS spectrum. No isotope patterns or salt mixtures
are inferred; charge states and sodium/potassium species are candidates only.
"""
from __future__ import annotations
import math

PROTON = 1.007276466621
SODIUM_CATION = 22.989220702
POTASSIUM_CATION = 38.963157907


def theoretical_ms_ions(exact_neutral_mass: float, *, max_charge: int = 3) -> dict:
    """Return candidate m/z for common ESI charge/adduct states (no prediction)."""
    if isinstance(exact_neutral_mass,bool):
        raise ValueError('Neutral monoisotopic mass must be a positive finite number.')
    try:
        mass=float(exact_neutral_mass)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Neutral monoisotopic mass must be a positive finite number.') from exc
    if not math.isfinite(mass) or mass<=0:
        raise ValueError('Neutral monoisotopic mass must be a positive finite number.')
    if type(max_charge) is not int or not 1<=max_charge<=5:
        raise ValueError('Requested charge range must be an integer from 1 to 5.')
    positive=[{'label':f'[M+{z}H]{z}+' if z>1 else '[M+H]+',
               'charge':z,'mz':round((mass+z*PROTON)/z,5)} for z in range(1,max_charge+1)]
    positive.extend(({'label':'[M+Na]+','charge':1,'mz':round(mass+SODIUM_CATION,5)},
                     {'label':'[M+K]+','charge':1,'mz':round(mass+POTASSIUM_CATION,5)}))
    negative=[{'label':'[M-H]-','charge':-1,'mz':round(mass-PROTON,5)}]
    return {'neutral_monoisotopic_mass':round(mass,5),
            'positive_ion_candidates':positive,'negative_ion_candidates':negative,
            'status':'THEORETICAL_ONLY_NOT_OBSERVED',
            'notes':'No isotope pattern, adduct abundance, ionization efficiency, instrument error, or measured mass is inferred.'}
