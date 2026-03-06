# ==========================================================
# PLANT PARAMETERS
# ==========================================================

class PlantParameters:
    """
    Parameters read by plant.f in FORCAsT (CUPID module).
    """

    def __init__(self,
                 avisr=0.0,
                 bvisr=0.0,
                 cvisr=8.16,
                 anirr=0.0,
                 bnirr=0.0,
                 cnirr=41.18,
                 avist=0.0,
                 bvist=0.0,
                 cvist=3.22,
                 anirt=0.0,
                 bnirt=0.0,
                 cnirt=57.23,
                 ispher=0,
                 nalpha=9,
                 gr=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.8],
                 imunu=1,
                 xmeu=1.101,
                 xneu=1.930,
                 imunua=0,
                 xmeuaz=180.0,
                 xneuaz=15.0,
                 beta0=37.62,
                 nbeta=50):

        if gr is None:
            gr = [0.0] * nalpha

        self.avisr = avisr
        self.bvisr = bvisr
        self.cvisr = cvisr
        self.anirr = anirr
        self.bnirr = bnirr
        self.cnirr = cnirr
        self.avist = avist
        self.bvist = bvist
        self.cvist = cvist
        self.anirt = anirt
        self.bnirt = bnirt
        self.cnirt = cnirt
        self.ispher = ispher
        self.nalpha = nalpha
        self.gr = gr
        self.imunu = imunu
        self.xmeu = xmeu
        self.xneu = xneu
        self.imunua = imunua
        self.xmeuaz = xmeuaz
        self.xneuaz = xneuaz
        self.beta0 = beta0
        self.nbeta = nbeta

        self._validate()

    def _validate(self):
        if not isinstance(self.gr, (list, tuple)):
            raise TypeError("gr must be a list or tuple.")

        if len(self.gr) != self.nalpha:
            raise ValueError(
                f"Length of gr ({len(self.gr)}) must equal nalpha ({self.nalpha})."
            )

    def to_dict(self):
        return self.__dict__.copy()


# ==========================================================
# RESISTANCE PARAMETERS
# ==========================================================

class ResistanceParameters:
    """
    Stomatal, cuticular, and soil resistance parameters
    used by CUPID inside FORCAsT.
    """

    def __init__(self,
                 rcut20=3000.0,
                 rsmin=90.0,
                 anstom=3.0,
                 radn=100.0,
                 trsopt=30.0,
                 trsmax=45.0,
                 trsmin=-2.0,
                 rsexp=6.0,
                 rsm=5.0,
                 psi1=-10.0,
                 psi2=-25.0,
                 rastom=1.0,
                 d1=0.0,
                 bkv=0.5,
                 rroot=3.0e6,
                 aroot=2.4):

        self.rcut20 = rcut20
        self.rsmin = rsmin
        self.anstom = anstom
        self.radn = radn
        self.trsopt = trsopt
        self.trsmax = trsmax
        self.trsmin = trsmin
        self.rsexp = rsexp
        self.rsm = rsm
        self.psi1 = psi1
        self.psi2 = psi2
        self.rastom = rastom
        self.d1 = d1
        self.bkv = bkv
        self.rroot = rroot
        self.aroot = aroot

    def to_dict(self):
        return self.__dict__.copy()
