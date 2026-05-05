import io
import cv2
import zipfile
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from scipy.optimize import curve_fit
from scipy import stats, ndimage
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import time


plt.rcParams.update({
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'axes.titlesize': 16,
    'legend.fontsize': 12
})


watermark_style = dict(
    x=0.5,
    y=0.5,
    fontsize=50,
    color="gray",
    alpha=0.3,
    ha="center",
    va="center",
    rotation=30
)

watermark_style_picture = dict(
    x=0.5,
    y=0.5,
    fontsize=25,
    color="gray",
    alpha=0.7,
    ha="center",
    va="center",
    rotation=45
)

# Функція для збереження фігури
def save_figure(fig, filename):
    # створюємо папку для збереження, якщо не існує
    os.makedirs("saved_figures", exist_ok=True)
    path = os.path.join("saved_figures", filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')


def calc_distribution_from_data(data, fname, nbins, type, area_cm2):
    if type == "dist":
        counts, bin_edges = np.histogram(data, bins=nbins, density=True)
        y = counts
    else:
        counts, bin_edges = np.histogram(data, bins=nbins, density=False)
        y = counts / area_cm2
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_width = bin_edges[1] - bin_edges[0]
    x = bin_centers
    # y = counts
    x_ax = np.linspace(data.min(), data.max(), 200)

    if nbins > 2:
        try:
            p0 = [max(y), np.mean(x), np.std(x)]
            params_gauss, _ = curve_fit(gaussian, x, y, p0=p0)
            A_gauss, mu_gauss, sigma_gauss = params_gauss
            y_gauss_fit = gaussian(x, A_gauss, mu_gauss, sigma_gauss)
            # --- R^2 для Gaussian ---
            ss_res_gauss = np.sum((y - y_gauss_fit) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2_gauss = 1 - ss_res_gauss / ss_tot
            y_gauss_fit = gaussian(x_ax, A_gauss, mu_gauss, sigma_gauss)
            # ax_h.plot(x_ax, y_gauss_fit, 'r-', lw=2, label=f'Gaussian fit, R²={r2_gauss:.4f}')
            gauss_fit_ok = True
        except RuntimeError:
            # st.warning("Gaussian fit не зійшовся.")
            gauss_fit_ok = False
            y_gauss_fit = np.zeros_like(x_ax)
            r2_gauss = 0

        try:
            p0_ln = [max(y), 0.5, np.mean(x)]
            params_ln, _ = curve_fit(lognormal, x, y, p0=p0_ln)
            A_ln, shape_ln, scale_ln = params_ln
            y_ln_fit = lognormal(x, A_ln, shape_ln, scale_ln)
            # --- R^2 для Log-normal ---
            ss_res_ln = np.sum((y - y_ln_fit) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2_ln = 1 - ss_res_ln / ss_tot
            y_ln_fit = lognormal(x_ax, A_ln, shape_ln, scale_ln)
            # ax_h.plot(x_ax, y_ln_fit, 'b-', lw=2, label=f'Log-normal fit, R²={r2_ln:.4f}')
            ln_fit_ok = True
        except RuntimeError:
            # st.warning("Log-Normal fit не зійшовся.")
            ln_fit_ok = False
            y_ln_fit = np.zeros_like(x_ax)
            r2_ln = 0
    else:
        gauss_fit_ok = False
        y_gauss_fit = np.zeros_like(x_ax)
        r2_gauss = 0
        ln_fit_ok = False
        y_ln_fit = np.zeros_like(x_ax)
        r2_ln = 0

    datasets = {
        f"data_{fname}.txt": [(i, val) for i, val in enumerate(data)],
        f"histogram_{fname}.txt": list(zip(x, y)),
        f"gaussian_fit_{fname}.txt": list(zip(x_ax, y_gauss_fit)),
        f"lognormal_fit_{fname}.txt": list(zip(x_ax, y_ln_fit))
    }

    dict4return = {
        "x": x,
        "y": y,
        "x_ax": x_ax,
        "gauss_fit_ok": gauss_fit_ok,
        "y_gauss_fit": y_gauss_fit,
        "r2_gauss": r2_gauss,
        "ln_fit_ok": ln_fit_ok,
        "y_ln_fit": y_ln_fit,
        "r2_ln": r2_ln,
        "bin_width": bin_width,
        # "datasets": datasets,
        "mean": data.mean()
                   }
    return dict4return, datasets


def make_distribution_figs_and_data(dict_with_data,
                                    nbins, colorbins, xlabel, ylabel, data_label,
                                    show_gaus, show_logn, show_mean, mean, show_text):
    x = dict_with_data["x"]
    y = dict_with_data["y"]
    x_ax = dict_with_data["x_ax"]
    gauss_fit_ok = dict_with_data["gauss_fit_ok"]
    y_gs = dict_with_data["y_gauss_fit"]
    r2gs = dict_with_data["r2_gauss"]
    ln_fit_ok = dict_with_data["ln_fit_ok"]
    y_ln = dict_with_data["y_ln_fit"]
    r2ln = dict_with_data["r2_ln"]
    bin_width = dict_with_data["bin_width"]

    fig_fit, ax_fit = plt.subplots(figsize=(10, 5))
    ax_fit.bar(x, y, width=bin_width * 0.8, color=colorbins, edgecolor='black', alpha=0.5, label=data_label)
    if gauss_fit_ok and show_gaus:
        ax_fit.plot(x_ax, y_gs, 'r-', lw=2, label=f'Gaussian fit, R²={r2gs:.4f}')
    if ln_fit_ok and show_logn:
        ax_fit.plot(x_ax, y_ln, 'b-', lw=2, label=f'Log-normal fit, R²={r2ln:.4f}')
    if show_mean:
        ax_fit.axvline(mean, color='black', linestyle='--', linewidth=2)
    ax_fit.set_xlabel(xlabel)
    ax_fit.set_ylabel(ylabel)
    lines, labels = ax_fit.get_legend_handles_labels()
    ax_fit.legend(lines[::-1], labels[::-1])
    fig_fit.text(s=show_text, **watermark_style)

    return fig_fit


@st.cache_data(show_spinner=False)
def make_figure_numsize_png(h0, Count, Mean_diameter, mode_numbers, area_nm2, use_log_area, disp_h0,
                            y1label, y2label, xlabel, show_text):
# def make_figure_numsize_png(h0, Count, Mean_diameter, mode_numbers, area_nm2, use_log_area, disp_h0, lang):
    fig_num_size, ax1 = plt.subplots(figsize=(10, 5))
    if mode_numbers == "numbers":
        ax1.plot(h0, Count, 'r-o')
        # ax1.set_ylabel(f"{LANG['Кількість структур']} {LANG['(шт)']}", color='r')
    if mode_numbers == "numdens":
        full_area_cm2 = area_nm2 * 1E-14
        ax1.plot(h0, Count / full_area_cm2, 'r-o')
        # ax1.set_ylabel(f"{LANG['Густина структур']} {LANG['(см⁻²)']}", color='r')
    ax1.tick_params(axis='y', labelcolor='r')
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1label, color='r')
    # ax1.set_xlabel(LANG['Висота поверхні (нм)'])
    ax1.set_ylim(bottom=0)

    ax2 = ax1.twinx()
    ax2.plot(h0, Mean_diameter, 'b--s')
    ax2.set_ylabel(y2label, color='b')
    # ax2.set_ylabel(LANG['Середній розмір структур (нм)'], color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.set_ylim(bottom=0.0)

    if use_log_area:
        ax2.set_yscale('log')
        # ax2.set_ylabel(f"{LANG['Середній розмір структур (нм)']} [Log Scale]", color='b')
        ax2.set_ylim(bottom=1.0)

    ax1.axvline(disp_h0, color='black', linestyle='--', linewidth=2)
    ax1.grid(True, color='gray', linestyle='--', linewidth=0.5)
    fig_num_size.text(s=show_text, **watermark_style)
    fig_num_size.tight_layout()
    buf = io.BytesIO()
    fig_num_size.savefig(buf, format="png")
    plt.close(fig_num_size)

    return buf.getvalue()

# @st.cache_data(show_spinner=False)
@st.cache_data(
    show_spinner=False,
    hash_funcs={np.ndarray: lambda x: x.tobytes()}
)
def make_figure_distribution_png(dict_with_data, colorbins, xlabel, ylabel, data_label,
                                    show_gaus, show_logn, show_mean, mean, show_text, cache_buster=None):
    x = dict_with_data["x"]
    y = dict_with_data["y"]
    x_ax = dict_with_data["x_ax"]
    gauss_fit_ok = dict_with_data["gauss_fit_ok"]
    y_gs = dict_with_data["y_gauss_fit"]
    r2gs = dict_with_data["r2_gauss"]
    ln_fit_ok = dict_with_data["ln_fit_ok"]
    y_ln = dict_with_data["y_ln_fit"]
    r2ln = dict_with_data["r2_ln"]
    bin_width = dict_with_data["bin_width"]

    fig_fit, ax_fit = plt.subplots(figsize=(10, 5))
    ax_fit.bar(x, y, width=bin_width * 0.8, color=colorbins, edgecolor='black', alpha=0.5, label=data_label)
    if gauss_fit_ok and show_gaus:
        ax_fit.plot(x_ax, y_gs, 'r-', lw=2, label=f'Gaussian fit, R²={r2gs:.4f}')
    if ln_fit_ok and show_logn:
        ax_fit.plot(x_ax, y_ln, 'b-', lw=2, label=f'Log-normal fit, R²={r2ln:.4f}')
    if show_mean:
        ax_fit.axvline(mean, color='black', linestyle='--', linewidth=2)
    ax_fit.set_xlabel(xlabel)
    ax_fit.set_ylabel(ylabel)
    lines, labels = ax_fit.get_legend_handles_labels()
    ax_fit.legend(lines[::-1], labels[::-1])
    fig_fit.text(s=show_text, **watermark_style)
    fig_fit.tight_layout()
    buf = io.BytesIO()
    fig_fit.savefig(buf, format="png")
    plt.close(fig_fit)
    return buf.getvalue()


def make_zip_from_dict(data_dict, fig=None, fig_name="figure.png"):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Додаємо текстові файли
        for file_name, data_list in data_dict.items():
            txt_io = io.StringIO()
            for row in data_list:
                txt_io.write("\t".join(f"{val:.6f}" for val in row) + "\n")
            txt_io.seek(0)
            zf.writestr(file_name, txt_io.getvalue())

        # Додаємо фігуру, якщо вона є
        if fig is not None:
            zf.writestr(fig_name, fig)
            # img_io = io.BytesIO()
            # fig.savefig(img_io, format="png", dpi=300, bbox_inches="tight", pad_inches=0)
            # img_io.seek(0)
            # zf.writestr(fig_name, img_io.getvalue())

    zip_buffer.seek(0)
    return zip_buffer


def gaussian(x, A, mu, sigma):
    return A * np.exp(-(x - mu) ** 2 / (2 * sigma ** 2))


def lognormal(x, A, shape, scale):
    return A * stats.lognorm.pdf(x, shape, scale=scale)


def remove_minmax_area(num_labels, labels, min_area, max_area):
    areas = np.bincount(labels.ravel())
    # створюємо маску "дозволених" міток
    valid = np.where((areas >= min_area) & (areas <= max_area))[0]
    # прибираємо фон
    valid = valid[valid != 0]
    # створюємо нову маску
    mask = np.isin(labels, valid)
    # бінаризуємо
    cleaned = mask.astype(np.uint8)
    # перевизначаємо компоненти
    num_labels, labels = cv2.connectedComponents(cleaned)
    return num_labels, labels


def remove_border_labels(labels):
    h, w = labels.shape
    # мітки на межах
    border_labels = np.unique(np.concatenate([
        labels[0, :],        # верх
        labels[-1, :],       # низ
        labels[:, 0],        # ліво
        labels[:, -1]        # право
    ]))
    # прибираємо фон
    border_labels = border_labels[border_labels != 0]
    # занулюємо їх
    mask = np.isin(labels, border_labels)
    labels[mask] = 0
    return labels



class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def merge_periodic_labels(labels):
    h, w = labels.shape
    max_label = labels.max()

    uf = UnionFind(max_label + 1)

    # --- збираємо координати ---
    coords = {}
    for label in range(1, max_label + 1):
        ys, xs = np.where(labels == label)
        if len(ys) == 0:
            continue
        coords[label] = {
            "ymin": ys.min(),
            "ymax": ys.max(),
            "xmin": xs.min(),
            "xmax": xs.max()
        }

    # --- ліво-право ---
    left_labels = np.unique(labels[:, 0])
    right_labels = np.unique(labels[:, -1])

    for l in left_labels:
        if l == 0 or l not in coords:
            continue
        for r in right_labels:
            if r == 0 or r not in coords:
                continue

            # перевірка overlap по Y
            if not (coords[l]["ymax"] < coords[r]["ymin"] or
                    coords[r]["ymax"] < coords[l]["ymin"]):
                uf.union(l, r)

    # --- верх-низ ---
    top_labels = np.unique(labels[0, :])
    bottom_labels = np.unique(labels[-1, :])

    for t in top_labels:
        if t == 0 or t not in coords:
            continue
        for b in bottom_labels:
            if b == 0 or b not in coords:
                continue

            # overlap по X
            if not (coords[t]["xmax"] < coords[b]["xmin"] or
                    coords[b]["xmax"] < coords[t]["xmin"]):
                uf.union(t, b)

    # --- ремапінг ---
    new_labels = np.zeros_like(labels)
    label_map = {}
    new_id = 1

    for i in range(1, max_label + 1):
        root = uf.find(i)
        if root not in label_map:
            label_map[root] = new_id
            new_id += 1
        new_labels[labels == i] = label_map[root]

    # return new_labels, new_id - 1
    return new_id, new_labels


# --- ДОПОМІЖНА ФУНКЦІЯ (для чутливості) ---
# analyze_batch(image_gray, h_val, seg_method, min_area, max_area, scale_nm_px, z_scale)
# def analyze_batch(img, h_val, min_a, max_a, s_xy, s_z, dist=10):
def analyze_batch(img, h_val, min_a, max_a, s_xy, s_z, mode, tresh_type):

    blur = cv2.GaussianBlur(img, (3, 3), 0)
    topo = img.astype(float) * s_z
    _, mask = cv2.threshold(blur, h_val, 255, tresh_type)
    # _, mask = cv2.threshold(blur, h_val, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    num, labels = cv2.connectedComponents(mask)
    num, labels = remove_minmax_area(num, labels, min_a, max_a)

    mask = np.array(mask, dtype=np.uint8)
    if mode == "periodic_conditions":
        # num, labels = cv2.connectedComponents(mask)
        num, labels = merge_periodic_labels(labels)

    elif mode == "exclude_border":
        # num, labels = cv2.connectedComponents(mask)
        labels = remove_border_labels(labels)
        labels = np.array(labels, dtype=np.uint8)
        num, labels = cv2.connectedComponents((labels > 0).astype(np.uint8))

    else:
        # num, labels = cv2.connectedComponents(mask)
        labels = np.array(labels, dtype=np.uint8)
        num, labels = cv2.connectedComponents((labels > 0).astype(np.uint8))

    res = []
    unq = np.unique(labels)
    for l in unq:
        if l == 0: continue
        msk_g = (labels == l).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(msk_g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts: continue
        area = cv2.contourArea(cnts[0])
        # if area < min_a: continue
        # if area > max_a: continue

        area_nm = area * (s_xy ** 2)
        z_v = topo[labels == l]
        mean_h = np.mean(z_v) if len(z_v) > 0 else 0
        res.append({'Area (nm^2)': area_nm, 'Mean Height (nm)': mean_h})
    return pd.DataFrame(res)


def plane_correction(z):
    h, w = z.shape
    y, x = np.mgrid[:h, :w]
    X = np.column_stack((x.ravel(), y.ravel(), np.ones(h*w)))
    Z = z.ravel()
    coeffs, _, _, _ = np.linalg.lstsq(X, Z, rcond=None)
    plane = coeffs[0]*x + coeffs[1]*y + coeffs[2]
    return z - plane


# def calc_roughness(image_gray, z_scale):
#     topo_nm = image_gray.astype(float) * z_scale
#     topo_nm = plane_correction(topo_nm)
#     z = topo_nm - np.mean(topo_nm)
#
#     Sa = np.mean(np.abs(z))
#     Sq = np.sqrt(np.mean(z ** 2))
#     Sz = np.ptp(topo_nm)
#
#     Sm = np.mean(image_gray.astype(float) * z_scale)
#     Sp = np.max(z)
#     Sv = np.min(z)
#
#     Ssk = np.mean(z ** 3) / (Sq ** 3)
#     Sku = np.mean(z ** 4) / (Sq ** 4)
#
#     df = pd.DataFrame({
#         "Param": ["Heights_difference",
#                   "Mean_height",
#                   "Max_height",
#                   "Min_height",
#                   "Mean_roughness",
#                   "RMS-roughness",
#                   "Skewness",
#                   "Kurtosis"],
#         "Value": [Sz, Sm, Sp, Sv, Sa, Sq, Ssk, Sku]
#     })
#
#     txt_io = io.StringIO()
#     for _, row in df.iterrows():
#         # Пишемо параметр та значення, відокремлюємо табуляцією
#         txt_io.write(f"{row['Param']}\t{row['Value']:.6f}\n")
#     txt_io.seek(0)
#     return df, txt_io.getvalue()


def add_stats_row(stats_df, data, row_name):
    s = pd.Series(data).describe()

    stats_df.loc[row_name] = [
        s["min"],
        s["max"],
        s["mean"],
        s["50%"],
        s["std"],
        (s["std"] / s["mean"]) * 100 if s["mean"] != 0 else np.nan
    ]

    return stats_df


def run_button_analysis(cropped_img, real_width_nm, real_height_nm, thresh_type):
    image_gray = cv2.cvtColor(cropped_img, cv2.COLOR_RGB2GRAY)
    height, width = image_gray.shape
    scale_nm_px = real_width_nm / width
    z_scale = real_height_nm / 255
    full_image_area_nm2 = height * width * (scale_nm_px ** 2)
    # mean_h = np.mean(image_gray.astype(float))
    ticks = np.linspace(image_gray.min(), image_gray.max(), 8)
    topo_map = image_gray.astype(float) * z_scale

    blur = cv2.GaussianBlur(image_gray, (3, 3), 0)
    thresh_val, mask = cv2.threshold(blur, 0, 255, thresh_type + cv2.THRESH_OTSU)
    h0 = int(thresh_val)
    opt_h = h0 * z_scale
    # st.session_state.display_h0 = display_h0

    topo_nm = topo_map.copy()
    topo_nm = plane_correction(topo_nm)
    z = topo_nm - np.mean(topo_nm)
    Sa = np.mean(np.abs(z))
    Sq = np.sqrt(np.mean(z ** 2))
    Sz = np.ptp(topo_nm)
    Sm = np.mean(image_gray.astype(float) * z_scale)
    Sp = np.max(z)
    Sv = np.min(z)
    Ssk = np.mean(z ** 3) / (Sq ** 3)
    Sku = np.mean(z ** 4) / (Sq ** 4)

    df = pd.DataFrame({
        "Param": ["Heights_difference",
                  "Mean_height",
                  "Max_height",
                  "Min_height",
                  "Mean_roughness",
                  "RMS-roughness",
                  "Skewness",
                  "Kurtosis"],
        "Value": [Sz, Sm, Sp, Sv, Sa, Sq, Ssk, Sku]
    })

    txt_io = io.StringIO()
    for _, row in df.iterrows():
        # Пишемо параметр та значення, відокремлюємо табуляцією
        txt_io.write(f"{row['Param']}\t{row['Value']:.6f}\n")
    txt_io.seek(0)

    data = image_gray.ravel()*z_scale
    nbins = 15
    fname = "heights"
    dict_with_data, datasets = calc_distribution_from_data(data, fname, nbins, "dist", full_image_area_nm2)
    dict_to_return = {
                "z_scale": z_scale,
                "scale_nm_px": scale_nm_px,
                "full_image_area_nm2": full_image_area_nm2,
                "image": image_gray,
                "topo_map": topo_map,
                "height": height,
                "width": width,
                "mean_h_px": Sm / z_scale,
                "mean_h": Sm,
                "opt_h": opt_h,
                "dict": dict_with_data,
                "datasets": datasets,
                "fname": "heights_analysis.zip",
                "ticks": ticks
            }
    data_roughness = df, txt_io.getvalue()
    return dict_to_return, data_roughness


def run_button_calculations(labels, scale_nm_px, full_image_area_nm2, topo_map):
    data_list = []
    centroids = []
    radii = []
    unique_labels = np.unique(labels)

    for lbl in unique_labels:
        if lbl == 0: continue
        grain_mask = (labels == lbl).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(grain_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts: continue
        cnt = cnts[0]
        area_px = cv2.contourArea(cnt)
        area_nm2 = area_px * (scale_nm_px ** 2)
        perimeter_nm = cv2.arcLength(cnt, True) * scale_nm_px
        equiv_d = np.sqrt(4 * area_nm2 / np.pi)
        radius = equiv_d / 2
        radii.append(radius)
        circularity = (4 * np.pi * area_nm2) / (perimeter_nm ** 2) if perimeter_nm > 0 else 0

        if len(cnt) >= 5:
            (cx, cy), (MA, ma), angle = cv2.fitEllipse(cnt)
            major = max(MA, ma) * scale_nm_px
            minor = min(MA, ma) * scale_nm_px
            aspect = major / minor if minor > 0 else 0
        else:
            major = 0
            minor = 0
            angle = 0
            aspect = 1.0

        grain_pixels = (labels == lbl)
        z_vals = topo_map[grain_pixels]

        max_h = np.max(z_vals) if len(z_vals) > 0 else 0
        mean_h = np.mean(z_vals) if len(z_vals) > 0 else 0

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            centroids.append([(M["m10"] / M["m00"]) * scale_nm_px, (M["m01"] / M["m00"]) * scale_nm_px])

        data_list.append({
            "Area (nm^2)": area_nm2,
            "Diameter (nm)": equiv_d,
            "Perimeter (nm)": perimeter_nm,
            "Circularity": circularity,
            "Major axis of elips (nm)": major,
            "Minor axis of elips (nm)": minor,
            "Aspect Ratio": aspect,
            "Angle of elips": angle,
            "Height from h₀ (nm)": max_h,
            "Mean Height (nm)": mean_h,
            "Log_Area": np.log10(area_nm2) if area_nm2 > 0 else 0,
            "Log_Diameter": np.log10(equiv_d) if equiv_d > 0 else 0,
            "Log_Perimeter": np.log10(perimeter_nm) if perimeter_nm > 0 else 0,
            "Log_Circularity": np.log10(circularity) if circularity > 0 else 0,
            "Log_Majoraxis": np.log10(major) if major > 0 else 0,
            "Log_Minoraxis": np.log10(minor) if minor > 0 else 0,
            "Log_Aspectratio": np.log10(aspect) if aspect > 0 else 0,
            "Log_Angle": np.log10(angle) if angle > 0 else 0
        })

    if len(centroids) > 1:
        num_grains = len(centroids)
        # full_image_area_nm2 = st.session_state.analysis["full_image_area_nm2"]
        # area_cm2 = full_image_area_nm2 * 1e-14  # nm² → см²
        tree = cKDTree(centroids)
        dd, idx = tree.query(centroids, k=2)
        mean_nn = np.mean(dd[:, 1])

        edge_distances = []
        for i in range(len(centroids)):
            j = idx[i, 1]
            center_dist = dd[i, 1]
            edge_dist = max(0, center_dist - (radii[i] + radii[j]))
            edge_distances.append(edge_dist)

        mean_nn_grains = np.mean(edge_distances)

        rho = num_grains / full_image_area_nm2
        R_centroids = mean_nn / (0.5 / np.sqrt(rho))
        R_grains = mean_nn_grains / (0.5 / np.sqrt(rho))

        centroids_stat = pd.DataFrame({
            "Param": ["Mean NN center (nm)", "R-Index center", "Mean NN grains (nm)", "R-Index grains"],
            "Value": [mean_nn, R_centroids, mean_nn_grains, R_grains]})

        df_dist = pd.DataFrame({
            "Nearest Neighbor (nm)": dd[:, 1],
            "Edge Distance (nm)": edge_distances
        })

        df = pd.DataFrame(data_list)

        df["Nearest Neighbor (nm)"] = dd[:, 1]
        df["Edge Distance (nm)"] = edge_distances

        df["Log Nearest Neighbor (nm)"] = np.where(dd[:, 1] > 0, np.log10(dd[:, 1]), 0)
        df["Log Edge Distance (nm)"] = np.where(np.array(edge_distances) > 0,
                                                np.log10(edge_distances), 0)

        # st.session_state.data_frame = df

        cols_geom = ["Area (nm^2)",
                     "Diameter (nm)",
                     "Perimeter (nm)",
                     "Circularity",
                     "Major axis of elips (nm)",
                     "Minor axis of elips (nm)",
                     "Aspect Ratio",
                     "Angle of elips",
                     "Height from h₀ (nm)",
                     "Nearest Neighbor (nm)",
                     "Edge Distance (nm)"
                     ]

        stats_df = df[cols_geom].describe().T
        stats_df = stats_df.drop(columns=['count', '25%', '75%'])
        stats_df.rename(columns={'50%': 'median'}, inplace=True)
        stats_df['CV (%)'] = np.where(
            stats_df['mean'] != 0,
            (stats_df['std'] / stats_df['mean']) * 100,
            np.nan
        )
        # st.session_state.table_statistics = stats_df

    return num_grains, centroids_stat, df_dist, df, stats_df


def calc_all_distributions(df, nbins, area_cm2):
    dict_calculated_distributions = {}
    dict_datasets = {}

    #############################   DIAMETER   ###########################################################

    name = "diameter_dist"
    distr, data = calc_distribution_from_data(df['Diameter (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(diameter)_dist"
    distr, data = calc_distribution_from_data(df['Log_Diameter'], name, nbins,"dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "diameter_dens"
    distr, data = calc_distribution_from_data(df['Diameter (nm)'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(diameter)_dens"
    distr, data = calc_distribution_from_data(df['Log_Diameter'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   AREA   ###########################################################

    name = "area_dist"
    distr, data = calc_distribution_from_data(df['Area (nm^2)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(area)_dist"
    distr, data = calc_distribution_from_data(df['Log_Area'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "area_dens"
    distr, data = calc_distribution_from_data(df['Area (nm^2)'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(area)_dens"
    distr, data = calc_distribution_from_data(df['Log_Area'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   PERIMETER   ###########################################################

    name = "perimeter_dist"
    distr, data = calc_distribution_from_data(df['Perimeter (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(perimeter)_dist"
    distr, data = calc_distribution_from_data(df['Log_Perimeter'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "perimeter_dens"
    distr, data = calc_distribution_from_data(df['Perimeter (nm)'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(perimeter)_dens"
    distr, data = calc_distribution_from_data(df['Log_Perimeter'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   CIRCULARITY   ###########################################################

    name = "circularity_dist"
    distr, data = calc_distribution_from_data(df['Circularity'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "circularity_dens"
    distr, data = calc_distribution_from_data(df['Circularity'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   MAJOR AXIS  ###########################################################

    name = "majoraxis_dist"
    distr, data = calc_distribution_from_data(df['Major axis of elips (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(majoraxis)_dist"
    distr, data = calc_distribution_from_data(df['Log_Majoraxis'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "majoraxis_dens"
    distr, data = calc_distribution_from_data(df['Major axis of elips (nm)'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(majoraxis)_dens"
    distr, data = calc_distribution_from_data(df['Log_Majoraxis'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   MINOR AXIS   ###########################################################

    name = "minoraxis_dist"
    distr, data = calc_distribution_from_data(df['Minor axis of elips (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(minoraxis)_dist"
    distr, data = calc_distribution_from_data(df['Log_Minoraxis'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "minoraxis_dens"
    distr, data = calc_distribution_from_data(df['Minor axis of elips (nm)'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(minoraxis)_dens"
    distr, data = calc_distribution_from_data(df['Log_Minoraxis'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   ASPECT RATIO   ###########################################################

    name = "aspect_dist"
    distr, data = calc_distribution_from_data(df['Aspect Ratio'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(aspect)_dist"
    distr, data = calc_distribution_from_data(df['Log_Aspectratio'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "aspect_dens"
    distr, data = calc_distribution_from_data(df['Aspect Ratio'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(aspect)_dens"
    distr, data = calc_distribution_from_data(df['Log_Aspectratio'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   ANGLE   ###########################################################

    name = "angle_dist"
    distr, data = calc_distribution_from_data(df['Angle of elips'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(angle)_dist"
    distr, data = calc_distribution_from_data(df['Log_Angle'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "angle_dens"
    distr, data = calc_distribution_from_data(df['Angle of elips'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(angle)_dens"
    distr, data = calc_distribution_from_data(df['Log_Angle'], name, nbins, "dens", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    #############################   DISTANCES   ###########################################################

    name = "distances_centers_dist"
    distr, data = calc_distribution_from_data(df['Nearest Neighbor (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(distances_centers)_dist"
    distr, data = calc_distribution_from_data(df['Log Nearest Neighbor (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "distances_edge2edge_dist"
    distr, data = calc_distribution_from_data(df['Edge Distance (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    name = "log(distances_edge2edge)_dist"
    distr, data = calc_distribution_from_data(df['Log Edge Distance (nm)'], name, nbins, "dist", area_cm2)
    dict_calculated_distributions[name] = distr
    dict_datasets[name] = data

    return dict_calculated_distributions, dict_datasets

def make_dicts_for_figures():
    value_dist = {}
    value_dist["area"] = "Розподіл структур за площею"
    value_dist["diameter"] = "Розподіл структур за діаметром"
    value_dist["perimeter"] = "Розподіл структур за периметром"
    value_dist["circularity"] = "Розподіл структур за коефіцієнтом округлості"
    value_dist["majoraxis"] = "Розподіл структур за довжиною великої вісі еліпса"
    value_dist["minoraxis"] = "Розподіл структур за довжиною малої вісі еліпса"
    value_dist["aspect"] = "Розподіл структур за коефіцієнтом витягнутості"
    value_dist["angle"] = "Розподіл структур за кутом повороту еліпса"
    value_dist["distances_centers"] = "Розподіл найближчих міжцентрових відстаней між структурами"
    value_dist["distances_edge2edge"] = "Розподіл відстаней між межами структур"

    value_dens = {}
    value_dens["area"] = "Залежність густини структур від площі"
    value_dens["diameter"] = "Залежність густини структур від діаметра"
    value_dens["perimeter"] = "Залежність густини структур від периметра"
    value_dens["circularity"] = "Залежність густини структур від коефіцієнта округлості"
    value_dens["majoraxis"] = "Залежність густини структур від довжини великої вісі еліпса"
    value_dens["minoraxis"] = "Залежність густини структур від довжини малої вісі еліпса"
    value_dens["aspect"] = "Залежність густини структур від коефіцієнта витягнутості"
    value_dens["angle"] = "Залежність густини структур від кута повороту еліпса"
    value_dens["distances_centers"] = ""
    value_dens["distances_edge2edge"] = ""

    value_xlable = {}
    value_xlable["area"] = "Площа (нм²)"
    value_xlable["diameter"] = "Діаметр (нм)"
    value_xlable["perimeter"] = "Периметр (нм)"
    value_xlable["circularity"] = "Коефіцієнт округлості"
    value_xlable["majoraxis"] = "Довжина великої вісі еліпса (нм)"
    value_xlable["minoraxis"] = "Довжина малої вісі еліпса (нм)"
    value_xlable["aspect"] = "Коефіцієнт витягнутості"
    value_xlable["angle"] = "Кут повороту еліпса (°)"
    value_xlable["distances_centers"] = "Найближча міжцентрова відстань (нм)"
    value_xlable["distances_edge2edge"] = "Відстань між межами структур (нм)"
    return value_dist, value_dens, value_xlable


def build_statistics_zip(csv_bytes, txt_data, image_bytes, image_name="filtered_image.png"):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("geometric_statistics.csv", csv_bytes)
        zf.writestr("geometric_statistics.txt", txt_data.encode("utf-8"))
        zf.writestr(image_name, image_bytes)
    zip_buffer.seek(0)
    return zip_buffer


def make_clusterization(df_plot, n_cl):
    X = StandardScaler().fit_transform(df_plot)
    kmeans = KMeans(n_clusters=n_cl, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    df_plot['Cluster_Temp'] = cluster_labels

    cluster_means = df_plot.groupby('Cluster_Temp')['Diameter (nm)'].mean().sort_values()
    size_names = ["Small", "Medium", "Large", "X-Large", "XX-Large"]
    cluster_map = {}

    for new_id, (old_id, val) in enumerate(cluster_means.items()):
        name = size_names[new_id] if new_id < len(size_names) else f"Type {new_id + 1}"
        cluster_map[old_id] = name

    df_plot['Label'] = df_plot['Cluster_Temp'].map(cluster_map)
    df_plot.drop(columns=['Cluster_Temp'], inplace=True)

    order = [cluster_map[i] for i in cluster_means.index]
    plot_data = {
        "df": df_plot,
        "order": order,
        "vars": ['Diameter (nm)', 'Circularity', 'Angle of elips'],
    }

    return plot_data