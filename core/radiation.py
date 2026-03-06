class Radiation:
    def __init__(self, itot=9, jmax=16, jmin=2, dfmin=0.2, clump=1.0, kmax=3, inrad=1, iwpm2=0, ratiod=0.55, ration=0.55, emis=0.95, emisol=0.93, rsoil=[0.15, 0.20, 0.10], rleaf=[0.20, 0.45, 0.10], tleaf=[0.10, 0.30, 0.10]):
        self.itot = itot
        self.jmax = jmax
        self.jmin = jmin
        self.dfmin = dfmin
        self.clump = clump
        self.kmax = kmax

        self.inrad = inrad
        self.iwpm2 = iwpm2
        self.ratiod = ratiod
        self.ration = ration

        self.emis = emis
        self.emisol = emisol

        self.rsoil = rsoil
        self.rleaf = rleaf
        self.tleaf = tleaf

        self._validate()

    def _validate(self):
        if not isinstance(self.rsoil, (list, tuple)):
            raise TypeError("rsoil must be a list or tuple.")

        if len(self.rsoil) != self.kmax:
            raise ValueError(
                f"Length of rsoil ({len(self.rsoil)}) must equal nalpha ({self.kmax})."
            )

        if not isinstance(self.rleaf, (list, tuple)):
            raise TypeError("rleaf must be a list or tuple.")

        if len(self.rleaf) != self.kmax:
            raise ValueError(
                f"Length of rleaf ({len(self.rleaf)}) must equal nalpha ({self.kmax})."
            )
        if not isinstance(self.tleaf, (list, tuple)):
            raise TypeError("tleaf must be a list or tuple.")

        if len(self.rsoil) != self.kmax:
            raise ValueError(
                f"Length of tleaf ({len(self.tleaf)}) must equal nalpha ({self.kmax})."
            )

