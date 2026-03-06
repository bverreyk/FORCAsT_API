class InitialConditions:
    def __init__(self, grndT0=288.69, towT0=290.35, lapse=0.0098, zs=[-0.05,  -0.18,  -0.42,  -0.76,  -1.10], eta=[0.097,  0.095,  0.104,  0.174,  0.232], temps=[287.0,  286.3,  285.7,  285.0,  284.5], bd=1.14, sandfc=0.32, siltfc=0.35, clayfc=0.33):
        self.grndT0 = grndT0
        self.towT0 = towT0
        self.lapse = lapse
        self.zs    = zs
        self.eta   = eta
        self.temps = temps
        self.bd = bd
        self.sandfc = sandfc
        self.siltfc = siltfc
        self.clayfc = clayfc
