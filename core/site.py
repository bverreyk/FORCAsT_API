class Site:
    def __init__(self,name='BE-Vie',lat=50.305,lon=5.998,stdlng=15,isonics=2,zobstow=51,zobstcpy=24,zmxd=200.):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.stdlng = stdlng

        # SONIC setup
        self.isonics = isonics
        self.zobstow = zobstow
        self.zobstcpy = zobstcpy
        self.zmxd = zmxd
