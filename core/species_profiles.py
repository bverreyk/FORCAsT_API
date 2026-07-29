from dataclasses import dataclass
from pathlib import Path
from typing import List
import numpy as np

VALID_PROFILES = ('CONST', 'EXP', 'LINEAR', 'RH')

_PARAMS_MIN = {'CONST': 1, 'EXP': 2, 'LINEAR': 2, 'RH': 1}
_PARAMS_MAX = {'CONST': 1, 'EXP': 2, 'LINEAR': 3, 'RH': 1}


@dataclass
class ProfileEntry:
    """
    One row in init_profiles.dat.

    species : int   -- species index (from module_parameters_ddw.f90)
    profile : str   -- 'CONST' | 'EXP' | 'LINEAR' | 'RH'
    params  : list  -- CONST: [c0]
                       EXP:   [c0, scale]          c0*exp(-z*scale)
                       LINEAR:[c0, c1]             c0+c1*z  (no cap)
                               [c0, c1, cmax]      capped at cmax if cmax>0
                       RH:    [frac]               frac*esat(T)/p
    zmin    : float -- lower height bound [m], inclusive
    zmax    : float -- upper height bound [m], exclusive
    comment : str   -- written as inline comment
    """
    species: int
    profile: str
    params:  List[float]
    zmin:    float = 0.0
    zmax:    float = 9999.0
    comment: str   = ""

    def __post_init__(self):
        self.profile = self.profile.upper()
        if self.profile not in VALID_PROFILES:
            raise ValueError(
                f"Unknown profile type '{self.profile}'. "
                f"Must be one of {VALID_PROFILES}."
            )
        n_min = _PARAMS_MIN[self.profile]
        n_max = _PARAMS_MAX[self.profile]
        if not (n_min <= len(self.params) <= n_max):
            raise ValueError(
                f"Profile '{self.profile}' requires {n_min}–{n_max} parameter(s), "
                f"got {len(self.params)}: {self.params}"
            )
        if self.zmin >= self.zmax:
            raise ValueError(
                f"zmin ({self.zmin}) must be less than zmax ({self.zmax})."
            )

    def to_line(self, data_width: int = 72) -> str:
        params_str = "  ".join(f"{p:.6g}" for p in self.params)
        data = (
            f"{self.species:4d}  "
            f"{self.zmin:8.1f}  "
            f"{self.zmax:8.1f}  "
            f"{self.profile:<8s}  "
            f"{params_str}"
        )
        comment = f"# {self.comment}" if self.comment else ""
        return f"{data:<{data_width}}{comment}"


class SpeciesProfiles:
    """
    Container for FORCAsT initial species concentration profiles.

    Manages the list of ProfileEntry objects that are written to
    data/init_profiles.dat and read by the Fortran init block in main.f.

    Typical usage
    -------------
    # Start from the default UMBS/CABINEX configuration and tweak one species:
    sp = SpeciesProfiles.default()
    sp.set(410, 'RH', [1.0], comment='H2O: 100% RH')
    model.species_profiles = sp

    # Build from scratch:
    sp = SpeciesProfiles()
    sp.add(401, 'LINEAR', [42e-9, 0.10e-9, 60e-9])
    sp.add(397, 'EXP',    [8.34e-10, 0.001], zmin=0,  zmax=20)
    sp.add(397, 'EXP',    [1.048e-9, 0.001], zmin=20, zmax=34)

    # Load from existing file:
    sp = SpeciesProfiles.from_file('data/init_profiles.dat')
    """

    def __init__(self, entries: List[ProfileEntry] = None):
        self.entries = list(entries) if entries else []

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add(
        self,
        species: int,
        profile: str,
        params:  List[float],
        zmin:    float = 0.,
        zmax:    float = 9999.,
        comment: str   = "",
    ) -> "SpeciesProfiles":
        """Append a profile entry. Returns self for chaining."""
        self.entries.append(ProfileEntry(
            species=species,
            profile=profile,
            params=list(params),
            zmin=zmin,
            zmax=zmax,
            comment=comment,
        ))
        return self

    def remove(
        self,
        species: int,
        zmin: float = None,
        zmax: float = None,
    ) -> "SpeciesProfiles":
        """
        Remove entries for a given species.
        If zmin/zmax are given, only entries whose bounds match exactly are removed.
        Returns self for chaining.
        """
        def _keep(e: ProfileEntry) -> bool:
            if e.species != species:
                return True
            if zmin is not None and e.zmin != zmin:
                return True
            if zmax is not None and e.zmax != zmax:
                return True
            return False

        self.entries = [e for e in self.entries if _keep(e)]
        return self

    def set(
        self,
        species: int,
        profile: str,
        params:  List[float],
        zmin:    float = 0.,
        zmax:    float = 9999.,
        comment: str   = "",
    ) -> "SpeciesProfiles":
        """
        Replace ALL existing entries for a species with a single new one.
        For piecewise profiles, call remove() followed by multiple add() calls.
        Returns self for chaining.
        """
        self.remove(species)
        self.add(species, profile, params, zmin, zmax, comment)
        return self

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def write(self, filepath) -> Path:
        """Write init_profiles.dat to filepath."""
        filepath = Path(filepath)
        header = [
            "# init_profiles.dat -- generated by FORCAsT_API SpeciesProfiles",
            "# Format: SPECIES_INDEX  ZMIN  ZMAX  TYPE  PARAMS",
            "#",
            "# Types:",
            "#   CONST   c0                  uniform value [mol/mol]",
            "#   EXP     c0  scale           c0 * exp(-z * scale)",
            "#   LINEAR  c0  c1  [cmax]      c0 + c1*z,  capped at cmax if cmax > 0",
            "#   RH      frac                frac * esat(T(z)) / p(z)  [H2O only]",
            "#",
            "# Species indices: module_parameters_ddw.f90",
            "# ZMIN <= z < ZMAX  [m a.g.l.]  --  use 0. and 9999. for all levels",
            "#",
        ]
        lines = header + [e.to_line() for e in self.entries]
        filepath.write_text("\n".join(lines) + "\n")
        return filepath

    def add_from_observations(
        self,
        species: int,
        heights,
        values,
        profile_type: str = 'EXP',
        piecewise: bool = False,
        zmin: float = 0.,
        zmax: float = 9999.,
        default_above: float = None,
        comment: str = '',
    ) -> "SpeciesProfiles":
        """
        Add profile entries derived from observed (heights, values) data.

        Non-piecewise: fits a single analytical function to all observations.
        Piecewise: creates one entry per observation interval. Only CONST and
        LINEAR are supported in piecewise mode.

        In piecewise CONST mode each interval [heights[i], heights[i+1]) takes
        the value values[i]. The final entry runs from heights[-1] to zmax using
        default_above (if given) or values[-1] (if not).

        In piecewise LINEAR mode each interval is an exact linear segment through
        the two bounding observations. If default_above is given, a CONST entry
        is appended above heights[-1].
    
        Parameters
        ----------
        species : int
            Species index from module_parameters_ddw.f90.
        heights : array-like
            Measurement heights [m a.g.l.].
        values : array-like
            Measured concentrations [mol/mol] at each height.
        profile_type : str
            'CONST', 'LINEAR', or 'EXP'. Piecewise mode only accepts 'CONST'
            and 'LINEAR'.
        piecewise : bool
            If True, produce one entry per observation interval.
        zmin : float
            Lower bound for the single fitted entry (non-piecewise only).
        zmax : float
            Upper ceiling of the last entry or default_above entry.
        default_above : float or None
            If given, append a CONST entry covering [max(heights), zmax) with
            this value. Applies to piecewise mode only; ignored otherwise.
        comment : str
            Inline comment written to the file.
        """
        heights = np.asarray(heights, dtype=float)
        values  = np.asarray(values,  dtype=float)
    
        order   = np.argsort(heights)
        heights = heights[order]
        values  = values[order]
    
        if piecewise:
            if profile_type not in ('CONST', 'LINEAR'):
                raise ValueError(
                    f"piecewise mode only supports 'CONST' and 'LINEAR', "
                    f"got '{profile_type}'."
                )
            if len(heights) < 2:
                raise ValueError(
                    "piecewise mode requires at least 2 observations."
                )
    
            if profile_type == 'CONST':
                for i in range(len(heights) - 1):
                    self.add(
                        species=species,
                        profile='CONST',
                        params=[float(values[i])],
                        zmin=float(heights[i]),
                        zmax=float(heights[i + 1]),
                        comment=comment,
                    )
                top_value = float(default_above) if default_above is not None else float(values[-1])
                self.add(
                    species=species,
                    profile='CONST',
                    params=[top_value],
                    zmin=float(heights[-1]),
                    zmax=zmax,
                    comment=comment,
                )
    
            else:  # LINEAR
                for i in range(len(heights) - 1):
                    dz = float(heights[i + 1] - heights[i])
                    c1 = float(values[i + 1] - values[i]) / dz
                    c0 = float(values[i]) - c1 * float(heights[i])
                    self.add(
                        species=species,
                        profile='LINEAR',
                        params=[c0, c1],
                        zmin=float(heights[i]),
                        zmax=float(heights[i + 1]),
                        comment=comment,
                    )
                if default_above is not None:
                    self.add(
                        species=species,
                        profile='CONST',
                        params=[float(default_above)],
                        zmin=float(heights[-1]),
                        zmax=zmax,
                        comment=comment,
                    )
    
        else:
            if profile_type == 'CONST':
                params = [float(np.mean(values))]
    
            elif profile_type == 'LINEAR':
                c1, c0 = np.polyfit(heights, values, 1)
                params = [float(c0), float(c1)]
    
            elif profile_type == 'EXP':
                if np.any(values <= 0):
                    raise ValueError(
                        "EXP fit requires all values to be positive."
                    )
                slope, intercept = np.polyfit(heights, np.log(values), 1)
                params = [float(np.exp(intercept)), float(-slope)]
    
            else:
                raise ValueError(
                    f"Unsupported profile_type '{profile_type}'. "
                    f"Must be one of 'CONST', 'LINEAR', 'EXP'."
                )
    
            self.add(
                species=species,
                profile=profile_type,
                params=params,
                zmin=zmin,
                zmax=zmax,
                comment=comment,
            )
    
        return self

    def set_rh_profile(
        self,
        species: int,
        heights,
        values,
        default_above: float = None,
        zmax: float = 9999.,
        comment: str = '',
    ) -> "SpeciesProfiles":
        """
        Replace all existing entries for a species with piecewise RH entries
        derived directly from an observed relative humidity profile.
    
        Each interval [heights[i], heights[i+1]) receives an RH entry whose
        frac equals values[i]. The final entry runs from heights[-1] to zmax
        using default_above (if given) or values[-1] (if not).
    
        Parameters
        ----------
        species : int
            Species index from module_parameters_ddw.f90.
        heights : array-like
            Measurement heights [m a.g.l.], at least 2 values.
        values : array-like
            Relative humidity fractions [0-1] at each height.
        default_above : float or None
            frac to use above heights[-1]. If None, values[-1] is used.
        zmax : float
            Upper ceiling of the last entry.
        comment : str
            Inline comment written to every entry.
        """
        heights = np.asarray(heights, dtype=float)
        values  = np.asarray(values,  dtype=float)
    
        if len(heights) != len(values):
            raise ValueError("heights and values must have the same length.")
    
        if len(heights) < 2:
            raise ValueError("At least 2 height/value pairs are required.")
    
        order   = np.argsort(heights)
        heights = heights[order]
        values  = values[order]
    
        self.remove(species)
    
        for i in range(len(heights) - 1):
            self.add(
                species=species,
                profile='RH',
                params=[float(values[i])],
                zmin=float(heights[i]),
                zmax=float(heights[i + 1]),
                comment=comment,
            )
    
        top_frac = float(default_above) if default_above is not None else float(values[-1])
        self.add(
            species=species,
            profile='RH',
            params=[top_frac],
            zmin=float(heights[-1]),
            zmax=zmax,
            comment=comment,
        )
    
        return self

    @classmethod
    def from_file(cls, filepath) -> "SpeciesProfiles":
        """Parse an existing init_profiles.dat and return a SpeciesProfiles instance."""
        filepath = Path(filepath)
        entries = []

        with open(filepath) as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue

                comment = ""
                if "#" in line:
                    idx = line.index("#")
                    comment = line[idx + 1:].strip()
                    line = line[:idx].strip()

                parts = line.split()
                if len(parts) < 5:
                    continue

                entries.append(ProfileEntry(
                    species=int(parts[0]),
                    zmin=float(parts[1]),
                    zmax=float(parts[2]),
                    profile=parts[3],
                    params=[float(p) for p in parts[4:]],
                    comment=comment,
                ))

        return cls(entries)

    # ------------------------------------------------------------------
    # Default configuration
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> "SpeciesProfiles":
        """
        Return profiles matching the hardcoded init block in main.f
        (UMBS CABINEX site, xx=0.01).

        Species indices from module_parameters_ddw.f90.
        """
        sp = cls()

        # --- Long-lived background gases ---
        sp.add(  1, 'CONST',  [3.95e-4],                    comment="LCO2=1: 395 ppmv")
        sp.add(135, 'CONST',  [1.76e-6],                    comment="LCH4=135: 1.76 ppmv")
        sp.add(373, 'CONST',  [1.0e-7],                     comment="LCO=373: 100 ppbv")

        # --- Inorganic oxidants ---
        sp.add(401, 'LINEAR', [42.0e-9, 0.10e-9, 60.0e-9],  comment="LO3=401: 42 ppbv + 0.1 ppbv/m, cap 60 ppbv")
        sp.add(397, 'EXP',    [8.34e-10, 0.001],  zmin=0.,    zmax=20.,    comment="LNO2=397: 0-20 m")
        sp.add(397, 'EXP',    [1.048e-9, 0.001],  zmin=20.,   zmax=34.,    comment="LNO2=397: 20-34 m")
        sp.add(397, 'EXP',    [1.253e-9, 0.001],  zmin=34.,   zmax=300.,   comment="LNO2=397: 34-300 m")
        sp.add(397, 'CONST',  [2.0e-10],           zmin=300.,  zmax=600.,   comment="LNO2=397: 300-600 m")
        sp.add(397, 'CONST',  [1.0e-10],           zmin=600.,  zmax=1500.,  comment="LNO2=397: 600-1500 m")
        sp.add(397, 'CONST',  [5.0e-11],           zmin=1500., zmax=9999.,  comment="LNO2=397: >1500 m")
        sp.add(402, 'EXP',    [3.0e-12, 0.001],               comment="LNO=402: slow decay")
        sp.add(400, 'EXP',    [2.1e-12, 0.01],                comment="LNO3=400")
        sp.add(191, 'EXP',    [1.542e-10, 0.01],              comment="LHONO=191")
        sp.add(270, 'EXP',    [1.0e-10, 0.01],                comment="LHNO3=270")
        sp.add(243, 'EXP',    [5.0e-10, 0.0001],              comment="LH2O2=243: xx*xx scale")
        sp.add(133, 'EXP',    [1.0e-10, 0.01],                comment="LSO2=133")

        # --- Isoprene oxidation products ---
        sp.add(364, 'EXP',    [2.0e-10, 0.01],               comment="LMACR=364: MCR+MVK")
        sp.add(275, 'EXP',    [5.0e-10, 0.01],               comment="LMVK=275")
        sp.add(383, 'EXP',    [5.0e-9,  0.01],               comment="LHCHO=383: 5 ppbv surface")
        sp.add(384, 'EXP',    [3.9e-10, 0.01],               comment="LALD1=384: acetaldehyde")
        sp.add(396, 'EXP',    [2.0e-11, 0.01],               comment="LMGLY=396: methylglyoxal")
        sp.add(363, 'EXP',    [2.5e-9,  0.0001],             comment="LKETL=363: acetone, xx*xx scale")

        # --- Biogenic VOCs ---
        sp.add(356, 'EXP',    [2.0e-10, 0.01],               comment="LISOP=356: isoprene")
        sp.add(372, 'EXP',    [4.0e-11, 0.01],               comment="LAPIN=372: alpha-pinene")
        sp.add(359, 'CONST',  [0.0],                         comment="LBPIN=359: zero since apr 2015")
        sp.add(368, 'EXP',    [4.0e-11, 0.01],               comment="LDLMN=368: d-limonene")
        sp.add(345, 'EXP',    [2.0e-12, 0.01],               comment="LETHE=345: ethylene")

        # --- Anthropogenic VOCs ---
        sp.add(148, 'EXP',    [6.0e-11, 0.01],               comment="LAROH=148: toluene/xylene")
        sp.add(156, 'EXP',    [2.0e-11, 0.01],               comment="LAROL=156: toluene/xylene")
        sp.add(149, 'EXP',    [1.5e-10, 0.01],               comment="LETOH=149: ethanol")
        sp.add(203, 'EXP',    [3.0e-10, 0.01],               comment="LALKM=203: alkanes ~C8")
        sp.add(144, 'EXP',    [1.0e-9,  0.01],               comment="LPAN2301=144: PAN")

        # --- Water vapor ---
        # Replace with ('RH', [1.0]) for 100% RH tied to the temperature profile.
        sp.add(410, 'EXP',    [0.0198, 0.01],                comment="LH2O=410: hardcoded profile")

        return sp
