import numpy as np

class VerticalGrid:
    def __init__(self,nlev=40,htr=10,levhtr=8,hcpy=35,levcpy=18,delta=0.277):
        """
        Parameters
        ----------
        nlev : int
            Number of levels
        htr : float
            Height trunk space [m a.g.l.]
        levhtr : int
            Number of vertical layers in the trunk space
        hcpy : float
            Height of the canopy [m a.g.l.]
        levcpy : int
            Number of vertical layers in the forest canopy space (trunk+crown space)
        delta : float
            Spacing parameter
        """
        self.nlev = nlev
        self.htr = htr
        self.levhtr = levhtr
        self.hcpy = hcpy
        self.levcpy = levcpy
        self.delta = delta

    def get_z_mid(self):
        """
        Returns
        -------
        z_mid : array
            Middle points of the FORCAsT vertical grid [m a.g.l.]
        """
        tt = np.exp((self.levhtr - 1) * self.delta)
        hh = np.exp((self.levcpy - 1) * self.delta)
        xx = ((self.levcpy - 1) * self.delta) / ((self.levhtr - 1) * self.delta)
        zmin1 = (self.hcpy - self.htr * xx) / (hh + xx - tt * xx - 1)
        zmin2 = (zmin1 + self.htr - zmin1 * tt) / ((self.levhtr - 1) * self.delta)

        z_mid = np.zeros(self.nlev)
        for k in range(self.nlev):
            z_mid[k] = zmin1 * np.exp(k * self.delta) + zmin2 * k * self.delta - zmin1

        return z_mid

    def get_z_faces(self):
        """
        Returns
        -------
        z_faces : array
            Faces of the FORCAsT vertical grid [m a.g.l.]
        """
        z_mid = self.get_z_mid()
        z_faces = [0]
        for i in range(len(z_mid) - 1):
            z_faces.append(0.5 * (z_mid[i] + z_mid[i + 1]))
        z_faces.append(z_mid[-1] + 0.5 * (z_mid[-1] - z_mid[-2]))

        return np.array(z_faces)
