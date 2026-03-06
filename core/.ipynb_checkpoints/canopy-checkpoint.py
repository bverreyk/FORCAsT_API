import numpy as np
from scipy.stats import norm, beta, weibull_min

class canopy:
    def __init__(self, LAI, height, sizelf = 0.08, distribution="beta"):
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
        """
        self.LAI = LAI
        self.height = height
        self.sizelf = sizelf
        self.distribution = distribution
        self.params = None

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
    # Fit distribution parameters using curve_fit
    # ------------------------------------------------------------------
    def fit(self, z_mid, y_obs, height=None, plot=False):
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
        plot : bool
            If True, plot observed data and fitted distribution
        """

        if height is None:
            height = self.height

        # Normalize height
        x = z_mid / height

        if self.distribution == "normal":
            popt, _ = curve_fit(
                self._normal_pdf,
                x,
                y_obs,
                p0=[0.5, 0.2, np.sum(y_obs)],
                bounds=([0.0, 1e-3, 0.], [1.0, 1.0, np.inf])
            )
            pdf_func = self._normal_pdf

        elif self.distribution == "weibull":
            popt, _ = curve_fit(
                self._weibull_pdf,
                x,
                y_obs,
                p0=[2.0, 0.5, np.sum(y_obs)],
                bounds=([0.5, 0.05, 0.], [10.0, 2.0, np.inf])
            )
            pdf_func = self._weibull_pdf

        elif self.distribution == "beta":
            popt, _ = curve_fit(
                self._beta_pdf,
                x,
                y_obs,
                p0=[2.0, 2.0, np.sum(y_obs)],
                bounds=([0.5, 0.5, 0.], [10.0, 10.0, np.inf])
            )
            pdf_func = self._beta_pdf

        else:
            raise ValueError("Unknown distribution type")

        self.params = popt

        # ------------------------------------------------------------------
        # Optional plotting
        # ------------------------------------------------------------------
        if plot:
            x_plot = np.linspace(0, 1, 500)
            p_fit = pdf_func(x_plot, *popt)
            
            # Predicted at midpoints
            y_pred = pdf_func(x, *popt)

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
    def lad_profile(self, grid, plot=False):
        """
        Compute LAD per FORCAs finite-volume grid and optionally plot.

        Parameters
        ----------
        grid : array
            VerticalGrid object
        plot : bool
            If True, show visualization

        Returns
        -------
        layer_LAI_canopy : array
            Leaf area index per crown layer [m2 m-2]
            (as required for FORCAST input)
        """
        z_faces = grid.get_z_faces()
        z_mid = grid.get_z_mid()
        dz = np.diff(z_faces)

        # -------------------------------------------------
        # Continuous PDF (normalized)
        # -------------------------------------------------
        z_plot = np.linspace(0, self.height, 1000)
        x_plot = z_plot / self.height

        if self.distribution == "normal":
            mu, sigma, _ = self.params
            pdf_plot = norm.pdf(x_plot, mu, sigma)
            cdf_faces = norm.cdf(z_faces / self.height, mu, sigma)

        elif self.distribution == "weibull":
            k, lam, _ = self.params
            pdf_plot = weibull_min.pdf(x_plot, k, scale=lam)
            cdf_faces = weibull_min.cdf(z_faces / self.height, k, scale=lam)

        elif self.distribution == "beta":
            a, b, _ = self.params
            pdf_plot = beta.pdf(x_plot, a, b)
            cdf_faces = beta.cdf(z_faces / self.height, a, b)

        else:
            raise ValueError("Unknown distribution")
        
        # Normalize PDF over physical height
        pdf_plot /= np.trapz(pdf_plot, z_plot)

        # Scale to total LAI
        pdf_plot *= self.LAI

        # -------------------------------------------------
        # Finite-volume LAI per layer
        # -------------------------------------------------
        layer_LAI = self.LAI * np.diff(cdf_faces)

        # Convert to LAD (volume density)
        LAD_layer = layer_LAI / dz

        # -------------------------------------------------
        # Optional plotting
        # -------------------------------------------------
        if plot:
            canopy_bottom = grid.htr*0.9
            canopy_top = self.height*1.1
            if self.height != grid.hcpy:
                print(f"Warning: Canopy height inconsistent between vertical_grid ({grid.hcpy} m) and canopy ({self.height} m) objects")

            plt.figure(figsize=(8, 5))

            # Shade the canopy space
            plt.axvspan(grid.get_z_faces()[grid.levhtr],grid.get_z_faces()[grid.levcpy],alpha=0.1,color='C2',zorder=-2)

            # Continuous LAD
            plt.plot(z_plot, pdf_plot, label="Continuous LAD", linewidth=2)

            # Stepwise LAD
            for i in range(len(LAD_layer)):
                plt.hlines(
                    LAD_layer[i],
                    z_faces[i],
                    z_faces[i + 1],
                    linewidth=3
                )
            
            # Grid faces (light vertical lines)
            for zf in z_faces:
                if canopy_bottom <= zf <= canopy_top:
                    plt.axvline(zf, color="gray", alpha=0.2)

            # Midpoints (light markers)
            canopy_mask = (z_mid >= canopy_bottom) & (z_mid <= canopy_top)
            plt.scatter(
                z_mid[canopy_mask],
                LAD_layer[canopy_mask],
                color="gray",
                alpha=0.5,
                zorder=3
            )

            # ---- Focus x-axis on canopy region ----
            plt.xlim(canopy_bottom, canopy_top)

            # Optional: tighten LAD range automatically
            plt.ylim(0, max(pdf_plot) * 1.1)

            plt.xlabel("Height [m]")
            plt.ylabel("Leaf Area Density [m2 m-3]")
            plt.title("LAD Profile (Canopy Space)")
            plt.legend()
            plt.tight_layout()
            plt.show()

        return layer_LAI[grid.levhtr:grid.levcpy]/np.sum(layer_LAI[grid.levhtr:grid.levcpy])
