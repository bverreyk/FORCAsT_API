import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import norm, beta, weibull_min
from scipy.optimize import curve_fit

class Canopy:
    def __init__(
            self, 
            LAI: float, 
            height: float, 
            sizelf: float = 0.08, 
            distribution: str = None,
            df : list = None
    ):
        """
        Parameters
        ----------
        LAI : float
            Total leaf area index
        height : float
            Canopy height [m]
        sizelf : float
            Mean size of a leaf [m2]
        distribution : str
            'normal', 'weibull', or 'beta'
        df : list
            Optional, contains the output of get_crownspace_profile_LAI
        """
        self.LAI = LAI
        self.height = height
        self.sizelf = sizelf
        self.distribution = distribution
        self.params = None
        self.df = df

    # ------------------------------------------------------------------
    # PDFs defined on normalized height x in [0, 1]
    # ------------------------------------------------------------------
    @staticmethod
    def _normal_pdf(x, mu, sigma, normalisation=1):
        return normalisation*norm.pdf(x, mu, sigma)
    
    @staticmethod
    def _normal_cdf(x, mu, sigma):
        return norm.cdf(x, mu, sigma)

    @staticmethod
    def _weibull_pdf(x, k, lam, normalisation=1):
        return normalisation*weibull_min.pdf(x, k, scale=lam)

    @staticmethod
    def _weibull_cdf(x, k, lam):
        return weibull_min.cdf(x, k, scale=lam)

    @staticmethod
    def _beta_pdf(x, a, b, normalisation=1):
        return normalisation*beta.pdf(x, a, b)

    @staticmethod
    def _beta_cdf(x, a, b):
        return beta.cdf(x, a, b)

    # ------------------------------------------------------------------
    # Plot fitted parameters with dry leaf mass observations
    # ------------------------------------------------------------------
    def plot_fit(self, z_mid, y_obs, height = None):
        """
        Plot distribution parameters together with binned dry mass data

        Parameters
        ----------
        z_mid : array
            Midpoint height of bins [m]
        y_obs : array
            Dry leaf mass per bin
        height : float
            Heigt of the canopy at time of measurement [m a.g.l.]
        """

        if height is None:
            height = self.height

        # Normalize height
        x = z_mid / height

        if self.distribution is None:
            raise ValueError("Cannot plot a distribution when this attribute is None")
        elif self.distribution == "normal":
            pdf_func = self._normal_pdf
        elif self.distribution == "weibull":
            pdf_func = self._weibull_pdf
        elif self.distribution == "beta":
            pdf_func = self._beta_pdf
        else:
            raise ValueError("Unknown distribution type")

        x_plot = np.linspace(0, 1, 500)
        p_fit = pdf_func(x_plot, *self.params)
            
        # Predicted at midpoints
        y_pred = pdf_func(x, *self.params)

        # R² calculation
        ss_res = np.sum((y_obs - y_pred) ** 2)
        ss_tot = np.sum((y_obs - np.mean(y_obs)) ** 2)
        r2 = 1 - ss_res / ss_tot
            
        plt.figure()
        plt.scatter(x, y_obs, label="Observed")
        plt.plot(x_plot, p_fit, label=f"Fitted {self.distribution}")
        plt.xlabel("Normalized height (z / H)")
        plt.ylabel("Leaf mass per bin")
        plt.title(f"Vertical Leaf Area Distribution Fit\nR² = {r2:.4f}")
        plt.legend()
        plt.show()

    # ------------------------------------------------------------------
    # Fit distribution parameters using curve_fit
    # ------------------------------------------------------------------
    def fit(self, z_mid, y_obs, height=None):
        """
        Fit distribution parameters to binned dry mass data

        Parameters
        ----------
        z_mid : array
            Midpoint height of bins [m]
        y_obs : array
            Dry leaf mass per bin
        height : float
            Heigt of the canopy at time of measurement [m a.g.l.]
        """

        if height is None:
            height = self.height

        # Normalize height
        x = z_mid / height

        if self.distribution is None:
            raise ValueError("Cannot fit a distribution when this attribute is None")

        elif self.distribution == "normal":
            popt, _ = curve_fit(
                self._normal_pdf,
                x,
                y_obs,
                p0=[0.5, 0.2, np.sum(y_obs)],
                bounds=([0.0, 1e-3, 0.], [1.0, 1.0, np.inf])
            )

        elif self.distribution == "weibull":
            popt, _ = curve_fit(
                self._weibull_pdf,
                x,
                y_obs,
                p0=[2.0, 0.5, np.sum(y_obs)],
                bounds=([0.5, 0.05, 0.], [10.0, 2.0, np.inf])
            )

        elif self.distribution == "beta":
            popt, _ = curve_fit(
                self._beta_pdf,
                x,
                y_obs,
                p0=[2.0, 2.0, np.sum(y_obs)],
                bounds=([0.5, 0.5, 0.], [10.0, 10.0, np.inf])
            )

        else:
            raise ValueError("Unknown distribution type")

        self.params = popt

        return None
    
    # ------------------------------------------------------------------
    # Set the distribution parameters manually
    # ------------------------------------------------------------------
    def set_distribution_params(self,params):
        self.params = params
        return None

    # ------------------------------------------------------------------
    # Leaf Area Density profile
    # ------------------------------------------------------------------
    def get_full_profiles_LAI_LAD(self, grid):
        """
        Compute LAD per FORCAsT finite-volume grid.

        Parameters
        ----------
        grid : array
            VerticalGrid object

        Returns
        -------
        layer_LAI : array
            Leaf area index per FORCAsT layer [m2 m-2]
        layer_LAD : array
            Leaf area density per FORCAsT layer [m2 m-3]
        """
        z_faces = grid.get_z_faces()
        dz = np.diff(z_faces)

        # -------------------------------------------------
        # Continuous PDF (normalized)
        # -------------------------------------------------
        if self.distribution == "normal":
            mu, sigma, _ = self.params
            cdf_faces = norm.cdf(z_faces / self.height, mu, sigma)

        elif self.distribution == "weibull":
            k, lam, _ = self.params
            cdf_faces = weibull_min.cdf(z_faces / self.height, k, scale=lam)

        elif self.distribution == "beta":
            a, b, _ = self.params
            cdf_faces = beta.cdf(z_faces / self.height, a, b)

        else:
            raise ValueError("Unknown distribution")
        
        # -------------------------------------------------
        # Finite-volume LAI per layer
        # -------------------------------------------------
        layer_LAI = self.LAI * np.diff(cdf_faces)

        # Convert to LAD (volume density)
        layer_LAD = layer_LAI / dz

        return layer_LAI, layer_LAD


    def get_crownspace_profile_LAI(self,grid):
        """
        Compute LAD per FORCAsT finite-volume grid.

        Parameters
        ----------
        grid : array
            VerticalGrid object

        Returns
        -------
        layer_LAI_canopy : array
            Leaf area index per crownspace layer [m2 m-2]
            (as required for FORCAST input)
        """
        if not self.df is None and len(self.df) == (grid.levhtr-grid.levcpy):
            return self.df

        layer_LAI, layer_LAD = self.get_full_profiles_LAI_LAD(grid)
        return layer_LAI[grid.levhtr:grid.levcpy]/np.sum(layer_LAI[grid.levhtr:grid.levcpy])
