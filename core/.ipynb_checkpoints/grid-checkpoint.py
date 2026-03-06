import numpy as np

class VerticalGrid:
    def __init__(self, nlev, htr, levhtr, hcpy, levcpy, delta):
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
        tt = np.exp((levhtr - 1) * delta)
        hh = np.exp((levcpy - 1) * delta)
        xx = ((levcpy - 1) * delta) / ((levhtr - 1) * delta)
        zmin1 = (hcpy - htr * xx) / (hh + xx - tt * xx - 1)
        zmin2 = (zmin1 + htr - zmin1 * tt) / ((levhtr - 1) * delta)

        z_mid = np.zeros(nlev)
        for k in range(nlev):
            z_mid[k] = zmin1 * np.exp(k * delta) + zmin2 * k * delta - zmin1

        return z_mid

    def get_z_faces(self):
        """
        Returns
        -------
        z_faces : array
            Faces of the FORCAsT vertical grid [m a.g.l.]
        """
        z_faces = [0]
        for i in range(len(z_mid) - 1):
            z_faces.append(0.5 * (z_mid[i] + z_mid[i + 1]))
        z_faces.append(z_mid[-1] + 0.5 * (z_mid[-1] - z_mid[-2]))

        return np.array(z_faces)
