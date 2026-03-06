import numpy as np
import matplotlib.pyplot as plt

def plot_canopy_distribution(grid,canopy):
    z_faces = grid.get_z_faces()
    z_mid = grid.get_z_mid()
    dz = np.diff(z_faces)

    # -------------------------------------------------
    # Continuous PDF (normalized)
    # -------------------------------------------------
    z_plot = np.linspace(0, canopy.height, 1000)
    x_plot = z_plot / canopy.height

    if canopy.distribution == "normal":
        mu, sigma, _ = canopy.params
        pdf_plot = canopy._normal_pdf(x_plot, mu, sigma)

    elif canopy.distribution == "weibull":
        k, lam, _ = canopy.params
        pdf_plot = canopy._weibull_pdf(x_plot, k, scale=lam)

    elif canopy.distribution == "beta":
        a, b, _ = canopy.params
        pdf_plot = canopy._beta_pdf(x_plot, a, b)

    else:
        raise ValueError("Unknown distribution")

    # Normalize PDF over physical height
    pdf_plot /= np.trapz(pdf_plot, z_plot)

    # Scale to total LAI
    pdf_plot *= canopy.LAI

    layer_LAI, LAD_layer = canopy.get_full_profiles_LAI_LAD(grid)

    canopy_bottom = grid.htr*0.9
    canopy_top = canopy.height*1.1
    if canopy.height != grid.hcpy:
        print(f"Warning: Canopy height inconsistent between vertical_grid ({grid.hcpy} m) and canopy ({canopy.height} m) objects")

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

    return None
