import streamlit as st
# from scipy.spatial import cKDTree
# from sklearn.preprocessing import StandardScaler
# from sklearn.cluster import KMeans
import requests
import json
from PIL import Image as PILImage
from libs import *
from dict import *
import pdf
from role import USERS


if "lang" not in st.session_state:
    st.session_state.lang = "EN"  # За замовчуванням англійська
lang_choice = st.sidebar.selectbox("🌐 Language / Мова", ["EN", "UA"])
st.session_state.lang = lang_choice
# для зручності перемикання на українську
LANG_UA_UA = {key: key for key in LANG_UA.keys()}
# англійська → англійська
LANG_EN = {key: LANG_UA[key] for key in LANG_UA.keys()}
# --- 3. Вибір активного словника ---
LANG = LANG_EN if st.session_state.lang == "EN" else LANG_UA_UA

FORMSPREE_URL = "https://formspree.io/f/xbdqkbol"
# 🔥 INIT STATE
if "clear_form" not in st.session_state:
    st.session_state.clear_form = False
if "show_toast" not in st.session_state:
    st.session_state.show_toast = False
if "message" not in st.session_state:
    st.session_state.message = ""
if "email" not in st.session_state:
    st.session_state.email = ""

def logout():
    role = st.session_state.get("role", "viewer")
    if st.button(LANG["🚪 Вийти"],
                 disabled=(role == "viewer"),
                 use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = "demo"
        st.session_state.role = "viewer"
        full_reset()
        st.rerun()


def login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(f"## 🔐 {LANG['Вхід до системи']}")
            username = st.text_input(LANG["Логін"])
            password = st.text_input(LANG["Пароль"], type="password")
            if st.button(f"🔑 {LANG['Увійти']}", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.session_state.role = USERS[username]["role"]
                    full_reset()
                    st.rerun()
                    st.stop()
                else:
                    st.error(LANG["Невірний логін або пароль"])


DEFAULT_STATE = {
    "original_image": None,
    "filtered_image": None,
    "filtered_image_png":None,
    "cropped_image": None,
    "crop_percent": None,
    "original_image_file_name": None,
    "image": None,
    "analysis": None,
    "zip_buffer": None,
    "res_sens": None,
    "display_h0": None,
    "data_frame": None,
    "labels": None,
    "distances": None,
    "centroids": None,
    "centroids_stat": None,
    "roughness": None,
    "table_roughness": None,
    "table_statistics": None,
    "distribution_size": None,
    "distribution_geometry": None,
    "distribution_distance": None,
    "clustering": None,
    "pairplot": None,
    "dict_calculated_distributions": None,
    "dict_calculated_datasets": None,
    "table_caption_EN": None,
    "table_caption_UA": None,
    "n_bins": None,
    "conditions1": None,
    "conditions2": None,
    "table_statistics_ui": None,
    "mean_values": None,
    "zip_height_ready": None,
    "zip_height": None,
    "zip_num_size_height_ready": None,
    "zip_num_size_height": None,
    "zip_area_ready": None,
    "zip_area": None,
    "zip_diameter_ready": None,
    "zip_diameter": None,
    "zip_perimeter_ready": None,
    "zip_perimeter": None,
    "zip_circularity_ready": None,
    "zip_circularity": None,
    "zip_majoraxis_ready": None,
    "zip_majoraxis": None,
    "zip_minoraxis_ready": None,
    "zip_minoraxis": None,
    "zip_aspect_ready": None,
    "zip_aspect": None,
    "zip_angle_ready": None,
    "zip_angle": None,
    "zip_istances_centers_ready": None,
    "zip_istances_centers": None,
    "zip_distances_edge2edge_ready": None,
    "zip_distances_edge2edge": None
}

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "prev_file_name" not in st.session_state:
    st.session_state.prev_file_name = None

if "prev_file_signature" not in st.session_state:
    st.session_state.prev_file_signature = None

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

def reset_analysis_state():
    for key in DEFAULT_STATE:
        st.session_state[key] = None

def reset_crop():
    for side in ['top','bottom','left','right']:
        st.session_state[side] = 0

# def reset_image():
#     st.session_state.original_image = None
#     st.session_state.original_image_file_name = None
#     st.session_state.uploader_key += 1

def reset_image_state():
    st.session_state.original_image = None
    st.session_state.original_image_file_name = None

def reset_uploader():
    st.session_state.uploader_key += 1
    st.session_state.prev_file_name = None


def full_reset():
    reset_analysis_state()
    reset_crop()
    reset_image_state()
    reset_uploader()

# --- Налаштування сторінки ---
# st.set_page_config(page_title="AFM Ultimate Analytics", layout="wide", initial_sidebar_state="expanded")
st.set_page_config(
    page_title="AFM Ultimate Analytics",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = "demo"
    st.session_state.role = "viewer"


# uploaded_file_name = None
run_button_analyze = None
run_sens = None
start_analyze = None

with st.sidebar:
    st.divider()
    c1sb, c2sb = st.columns(2)
    with c1sb:
        st.write(f"👤 {st.session_state.role}")
    with c2sb:
        logout()
    st.divider()
    uploaded_file = st.file_uploader(
        f"📂 {LANG['Завантажте файл']}",
        type=["jpg", "png", "tif", "bmp"],
        key=f"uploaded_file_{st.session_state.uploader_key}"
    )

    prev_name = st.session_state.prev_file_name
    prev_sig = st.session_state.prev_file_signature

    if prev_sig is not None and uploaded_file is None:
        st.session_state.prev_file_signature = None
        reset_analysis_state()
        reset_crop()
        reset_image_state()
        # st.toast(LANG["Файл видалено"], icon="🗑️")

    elif uploaded_file is not None:
        current_sig = (uploaded_file.name, uploaded_file.size)

        if prev_sig != current_sig:
            st.session_state.prev_file_signature = current_sig

            file_bytes = np.frombuffer(uploaded_file.getvalue(), np.uint8)
            img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            img_orig = cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)

            st.session_state.original_image = img_orig
            st.session_state.original_image_file_name = uploaded_file.name

    st.divider()


    # with st.expander(f"📏 {LANG['Калібрування']}", expanded=True):
    #     real_width_nm = st.number_input(LANG["Реальна ширина зображення (нм)"], value=600.0, min_value=1.0, step=100.0)
    #     real_height_nm = st.number_input(LANG["Реальна висота структур (нм)"], value=20.0, min_value=1.0, step=1.0)


########################################################################################################

tabs_labels = [f"🔬 {LANG['Застосунок']}"]
if not st.session_state.authenticated:
    tabs_labels.append(f"🔐 {LANG['Вхід до системи']}")
tabs_labels.append(f"📩 {LANG['Зворотний зв\'язок']}")
toptabs = st.tabs(tabs_labels)
tab_idx = 0

with toptabs[tab_idx]:
    if st.session_state.original_image is None:
        st.image("img1.png", use_container_width=True)
    else:
        st.title("🔬 AFM Ultimate Analytics")
        st.header(LANG["Статистичний аналіз, Фізика поверхні, Data Science"])
tab_idx += 1
if not st.session_state.authenticated:
    with toptabs[tab_idx]:
        st.title("🔬 AFM Ultimate Analytics")
        st.header(LANG["Статистичний аналіз, Фізика поверхні, Data Science"])
        login()
    tab_idx += 1
with toptabs[tab_idx]:
    st.title("🔬 AFM Ultimate Analytics")
    st.header(LANG["Статистичний аналіз, Фізика поверхні, Data Science"])
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(f"📩 {LANG['Зворотний зв\'язок']}")
        # 🔥 RESET FORM (перед рендером полів)
        if st.session_state.clear_form:
            st.session_state.message = ""
            st.session_state.email = ""
            st.session_state.clear_form = False
        # 🔥 TOAST (показується після rerun)
        if st.session_state.show_toast:
            st.toast(f"{LANG['Повідомлення надіслано']} 👍", icon="✅")
            st.session_state.show_toast = False
        # 📩 FORM
        message = st.text_area(f"{LANG['Повідомлення']} *", key="message")
        email = st.text_input(f"Email ({LANG['за бажанням']})", key="email")
        send_btn = st.button(f"📤 {LANG['Надіслати']}", use_container_width=True)
        if send_btn:
            if not message.strip():
                st.warning(f"{LANG['Повідомлення не може бути пустим']}")
                # st.stop()
            else:
                data = {
                    "message": message,
                    "email": email,
                    "role": st.session_state.get("role", "unknown"),
                    "app_state": json.dumps(dict(st.session_state), default=str)[:3000]
                }
            try:
                response = requests.post(FORMSPREE_URL, data=data)
                if response.status_code in [200, 201]:
                    # 🔥 тригери стану
                    st.session_state.clear_form = True
                    st.session_state.show_toast = True
                    # 🔄 rerun
                    st.rerun()
                # else:
                    # st.error("Failed to send feedback")
            except Exception as e:
            #     st.error(f"Error: {e}")
                st.error(f"{LANG['Помилка надсилання']}")

role = st.session_state.get("role", "viewer")
# text_in_fig = LANG['Рисунок захищено'] if role == "viewer" else ""
text_in_fig = "Figure is protected" if role == "viewer" else ""

#######################################################################################################

@st.cache_data(show_spinner=False)
def build_overlay_fig(img_orig, top, bottom, left, right):
    height, width, _ = img_orig.shape

    top_line = int(top / 100 * height)
    bottom_line = int(height - bottom / 100 * height)
    left_line = int(left / 100 * width)
    right_line = int(width - right / 100 * width)

    overlay = img_orig.copy().astype(np.float32)

    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:top_line, :] = 1
    mask[bottom_line:, :] = 1
    mask[:, :left_line] = 1
    mask[:, right_line:] = 1

    alpha = 0.5
    color_overlay = np.array([0, 0, 100], dtype=np.float32)

    overlay[mask == 1] = overlay[mask == 1] * (1 - alpha) + color_overlay * alpha
    overlay = overlay.astype(np.uint8)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(overlay)
    ax.axis('off')

    ax.hlines([top_line, bottom_line],
              xmin=-0.05 * width, xmax=1.05 * width,
              colors='red', linewidth=1, linestyles='dashed', alpha=0.5)

    ax.vlines([left_line, right_line],
              ymin=-0.05 * height, ymax=1.05 * height,
              colors='red', linewidth=1, linestyles='dashed', alpha=0.5)

    return fig, (top_line, bottom_line, left_line, right_line)


@st.fragment
def crop_fragment():
    if st.session_state.original_image is None:
        return None, None, None

    img_orig = st.session_state.original_image
    height, width, _ = img_orig.shape

    for side in ['top','bottom','left','right']:
        if side not in st.session_state:
            st.session_state[side] = 0

    st.divider()
    st.subheader(f"✂️ {LANG['Кадрування зображення']}")

    col1, col2 = st.columns([2, 1])

    with col2:
        st.markdown(f"⚙️ **{LANG['Параметри']}**")
        st.divider()

        col21, col22 = st.columns(2)
        with col21:
            top = st.number_input(LANG['Зверху (%)'], 0, 50, key="top")
            bottom = st.number_input(LANG['Знизу (%)'], 0, 50, key="bottom")
        with col22:
            left = st.number_input(LANG['Зліва (%)'], 0, 50, key="left")
            right = st.number_input(LANG['Справа (%)'], 0, 50, key="right")

        st.divider()

        col23, col24 = st.columns(2)
        with col23:
            make_invert_image = st.checkbox(LANG["Інвертувати зображення"], value=False)

        with col24:
            mode_dots_holes = st.radio(LANG["Тип структур"], [LANG["острівці"], LANG["отвори"]])

            if mode_dots_holes == LANG["острівці"]:
                st.session_state.thresh_type = cv2.THRESH_BINARY
                st.session_state.type_of_structures = "(nano-dots)"
            else:
                st.session_state.thresh_type = cv2.THRESH_BINARY_INV
                st.session_state.type_of_structures = "(nano-holes)"

        st.divider()

        st.markdown(f"📏 {LANG['Калібрування']}")
        real_width_nm = st.number_input(LANG["Реальна ширина зображення (нм)"], value=600.0, min_value=1.0,
                                                step=100.0)
        real_height_nm = st.number_input(LANG["Реальна висота структур (нм)"], value=20.0, min_value=1.0,
                                                 step=1.0)

        # st.divider()

        fig, (top_line, bottom_line, left_line, right_line) = build_overlay_fig(
            img_orig, top, bottom, left, right
        )
        cropped = img_orig[top_line:bottom_line, left_line:right_line, :]
        st.session_state.cropped_image = cropped
        # run_button = st.button(f"🔍 {LANG['Аналізувати']}")
    with col1:
        st.markdown(f"🖼️ **{LANG['Оригінальне зображення']}**")
        st.pyplot(fig, use_container_width=True)

    return make_invert_image, real_width_nm, real_height_nm


@st.cache_data(show_spinner=False)
def table_statistics_surface(df, lang):
    df = (df.rename(columns={"Param": LANG["Параметр"], "Value": LANG["Значення"]}))
    if lang == "EN":
        cols_names = roughness_en
    else:
        cols_names = roughness_ua
    df[LANG["Параметр"]] = df[LANG["Параметр"]].map(cols_names)
    # df = df.style.format({LANG["Значення"]: "{:.2f}"})

    return df

# @st.cache_data(show_spinner=False)
# def make_figure_numsize_png(h0, Count, Mean_diameter, mode_numbers, area_nm2, use_log_area, disp_h0, y1label, y2label, xlabel):
# # def make_figure_numsize_png(h0, Count, Mean_diameter, mode_numbers, area_nm2, use_log_area, disp_h0, lang):
#     fig_num_size, ax1 = plt.subplots(figsize=(10, 5))
#     if mode_numbers == "numbers":
#         ax1.plot(h0, Count, 'r-o')
#         # ax1.set_ylabel(f"{LANG['Кількість структур']} {LANG['(шт)']}", color='r')
#     if mode_numbers == "numdens":
#         full_area_cm2 = area_nm2 * 1E-14
#         ax1.plot(h0, Count / full_area_cm2, 'r-o')
#         # ax1.set_ylabel(f"{LANG['Густина структур']} {LANG['(см⁻²)']}", color='r')
#     ax1.tick_params(axis='y', labelcolor='r')
#     ax1.set_xlabel(xlabel)
#     ax1.set_ylabel(y1label, color='r')
#     # ax1.set_xlabel(LANG['Висота поверхні (нм)'])
#     ax1.set_ylim(bottom=0)
#
#     ax2 = ax1.twinx()
#     ax2.plot(h0, Mean_diameter, 'b--s')
#     ax2.set_ylabel(y2label, color='b')
#     # ax2.set_ylabel(LANG['Середній розмір структур (нм)'], color='b')
#     ax2.tick_params(axis='y', labelcolor='b')
#     ax2.set_ylim(bottom=0.0)
#
#     if use_log_area:
#         ax2.set_yscale('log')
#         # ax2.set_ylabel(f"{LANG['Середній розмір структур (нм)']} [Log Scale]", color='b')
#         ax2.set_ylim(bottom=1.0)
#
#     ax1.axvline(disp_h0, color='black', linestyle='--', linewidth=2)
#     ax1.grid(True, color='gray', linestyle='--', linewidth=0.5)
#     fig_num_size.text(s=text_in_fig, **watermark_style)
#     fig_num_size.tight_layout()
#     buf = io.BytesIO()
#     fig_num_size.savefig(buf, format="png")
#     plt.close(fig_num_size)
#
#     return buf.getvalue()

@st.cache_data(show_spinner=False)
def show_filtered_image(labels):
    max_label = labels.max() + 1
    colors = np.random.randint(0, 255, size=(max_label, 3), dtype=np.uint8)
    colors[0] = [255, 255, 255]
    viz = colors[labels]
    thickness = 2  # замість 4
    viz = cv2.copyMakeBorder(
        viz,
        thickness, thickness, thickness, thickness,
        borderType=cv2.BORDER_CONSTANT,
        value=[255, 255, 255]
    )

    h, w = viz.shape[:2]
    cv2.rectangle(
        viz,
        (0, 0),
        (w - 1, h - 1),
        (0, 0, 0),
        thickness=thickness,
        lineType=cv2.LINE_8
    )
    return viz

@st.cache_data(show_spinner=False)
def table_statistics(stats_df_ui, lang):
    if lang == "EN":
        cols_names = cols_en
    else:
        cols_names = cols_ua

    stats_df_ui.rename(index=cols_names, inplace=True)
    stats_df_ui.rename(columns={
        "min": LANG["Мінімальне"],
        "max": LANG["Максимальне"],
        "mean": LANG["Середнє"],
        "median": LANG["Медіана"],
        "std": LANG["Дисперсія"],
        "CV (%)": LANG["Коеф. варіації (%)"]
    }, inplace=True)

    return stats_df_ui


@st.cache_data(show_spinner=False)
def make_pairplot(plot_data, lang):
    fig_pairplot = sns.pairplot(
        plot_data["df"],
        vars=plot_data["vars"],
        hue='Label',
        height=2,
        aspect=1.5,
        hue_order=plot_data["order"]
    )
    fig_pairplot._legend.set_title("")

    for text in fig_pairplot._legend.get_texts():
        text.set_fontsize(12)

    if lang != "EN":
        for ax in fig_pairplot.axes.flatten():
            if ax is not None:
                xlabel = ax.get_xlabel()
                ylabel = ax.get_ylabel()
                if xlabel in labels_ua:
                    ax.set_xlabel(labels_ua[xlabel])
                if ylabel in labels_ua:
                    ax.set_ylabel(labels_ua[ylabel])

        new_labels = []
        for lbl in fig_pairplot._legend.texts:
            short = lbl.get_text()
            lbl.set_text(size_ua.get(short, short))

    fig_pairplot.fig.text(s=text_in_fig, **watermark_style)
    buf_p = io.BytesIO()
    fig_pairplot.savefig(buf_p, format="png", dpi=300, bbox_inches='tight')
    plt.close(fig_pairplot.fig)
    return buf_p.getvalue()

@st.cache_data(show_spinner=False)
def make_violinplot(plot_data, lang, param):
    fig_violinplot, ax_v = plt.subplots(figsize=(10, 5))
    sns.violinplot(
        data=plot_data["df"],
        x='Label',
        y=param,
        ax=ax_v,
        palette='Set2',
        order=plot_data["order"]
    )

    if lang != "EN":
        ax_v.set_ylabel(labels_ua[param])
    else:
        ax_v.set_ylabel(labels_en[param])
    if lang != "EN":
        ax_v.set_xticklabels([size_ua[k] for k in plot_data["order"]])

    ax_v.set_xlabel(LANG["Кластери структур за розмірами"])
    fig_violinplot.text(s=text_in_fig, **watermark_style)
    buf_v = io.BytesIO()
    fig_violinplot.savefig(buf_v, format="png", dpi=300, bbox_inches='tight')
    plt.close(fig_violinplot)
    return buf_v.getvalue()

@st.fragment
def show_statistics_surface():
    if st.session_state.analysis is None:
        return None

    st.divider()
    st.subheader(f"🔢 {LANG['Структура даних']}")

    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.image is not None:
            st.markdown(f"✂️ **{LANG['Обрізане зображення']}**")
            st.image(st.session_state.image, use_container_width=True)

    with c2:
        if st.session_state.roughness is not None:
            st.markdown(f"🗻 **{LANG['Параметри шорсткості поверхні (ISO Roughness)']}**")
            df, data2save = st.session_state.roughness
            df_show = table_statistics_surface(df, st.session_state.lang)
            st.dataframe(df_show.style.format({LANG["Значення"]: "{:.2f}"}), hide_index=True)
            data2save = df_show.to_csv(sep="\t", index=False, float_format="%.2f")
            # data2save = df.to_csv(sep="\t", index=False, float_format="%.2f")

            st.download_button(
                label=f"💾 {LANG['Завантажити дані у текстовий файл']}",
                data=data2save,
                file_name="roughness_data.txt",
                mime="text/plain",
                disabled=(role == "viewer")
            )

    dict_with_data = st.session_state.analysis["dict"]
    tab1h, tab2h, tab3h, tab4h = st.columns(4)
    with tab1h:
        st.markdown(f"📊 **{LANG['Розподіл висот']}**")
    with tab2h:
        show_height = st.checkbox(
            LANG["Показати середню висоту"],
            key="show_h"
        )
    with tab3h:
        show_gaus = st.checkbox(
            LANG["Показати Gaussian fit"],
            key="show_gaus_h",
            disabled=(not dict_with_data["gauss_fit_ok"])
        )
    with tab4h:
        show_logn = st.checkbox(
            LANG["Показати Log-Normal fit"],
            key="show_logn_h",
            disabled=(not dict_with_data["ln_fit_ok"])
        )
    st.session_state.dict_for_distrib_heights = None
    dict_for_distrib_heights = {}
    dict_for_distrib_heights["show_gaus"] = show_gaus
    dict_for_distrib_heights["show_logn"] = show_logn
    dict_for_distrib_heights["show_height"] = show_height
    dict_for_distrib_heights["mean_height"] = dict_with_data["mean"]
    st.session_state.dict_for_distrib_heights = dict_for_distrib_heights

    fig_heights = make_figure_distribution_png(dict_with_data,
                                                  'gray', LANG['Діапазон висот (нм)'],
                                                  LANG['Частота зустрічання'], LANG['Дані'],
                                                  show_gaus, show_logn, show_height, dict_with_data["mean"],
                                                  text_in_fig, cache_buster=time.time())

    st.image(fig_heights, use_container_width=True)

    if not dict_with_data["gauss_fit_ok"]:
        st.warning(LANG["Gaussian fit не зійшовся"])
    if not dict_with_data["ln_fit_ok"]:
        st.warning(LANG["Log-Normal fit не зійшовся"])

    st.session_state["zip_height_ready"] = False
    col1, col2 = st.columns(2)
    with col1:
        mk_zip_height = st.button(
            f"📦 {LANG['Зробити ZIP архів з даними']}",
            key="mk_zip_height",
            disabled=(role == "viewer")
        )
    zip_data_height = None
    if mk_zip_height:
        datasets = st.session_state.analysis["datasets"]
        zip_fname = st.session_state.analysis["fname"]
        zip_data_height = make_zip_from_dict(datasets, fig_heights, "fig_heights.png")
        st.session_state["zip_height"] = zip_data_height
        st.session_state["zip_height_ready"] = True
    with col2:
        if st.session_state.get("zip_height_ready", False):
            st.download_button(
                label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                data=zip_data_height,
                file_name=zip_fname,
                mime="application/zip",
                disabled=(role == "viewer")
            )

    return fig_heights


@st.fragment
def height_dependent_analysis():
    if st.session_state.analysis is None:
        return None

    st.divider()
    st.subheader(f"🔢 {LANG['Аналіз кількості/розмірів структур на різних висотах']}")
    res = st.session_state.analysis
    c_set1, c_set2 = st.columns(2)
    image_gray = res["image"]
    z_scale = res["z_scale"]
    width = res["width"]
    height = res["height"]
    scale_nm_px = res["scale_nm_px"]
    full_image_area_nm2 = res["full_image_area_nm2"]
    min_h_nm = int(image_gray.min() * z_scale)
    max_h_nm = int(image_gray.max() * z_scale)
    min_step = 1
    max_step = max(1, int((max_h_nm - min_h_nm) / 2))
    cur_step = max(1, int((max_h_nm - min_h_nm) / 10))

    with c_set1:
        h_min_nm = st.number_input(LANG["Мінімальна висота (нм)"], min_h_nm, max_h_nm, min_h_nm, step=1)
        h_max_nm = st.number_input(LANG["Максимальна висота (нм)"], min_h_nm, max_h_nm, max_h_nm, step=1)
        step_h_nm = st.number_input(LANG["Крок (нм)"], min_step, max_step, cur_step, step=1)
        h_min = int(h_min_nm / z_scale) + 1
        h_max = int(h_max_nm / z_scale) + 1
        step_h = int(step_h_nm / z_scale) + 1

    with c_set2:
        exclude_min_area_1 = st.checkbox(f"{LANG['Ігнорувати малі структури']}", value=False, key="checkbox11")
        if exclude_min_area_1:
            max_value_nm = int(min(width, height) * scale_nm_px)
            curr_value_nm = max(1, int(scale_nm_px))
            min_diameter = st.number_input(f"{LANG['Мінімальний діаметр (нм)']}", 0, max_value_nm, curr_value_nm,
                                           key="diameter11")
            min_area = int(np.pi * (min_diameter / scale_nm_px) ** 2 / 4)
        else:
            min_area = 0
            min_diameter = 0
        exclude_max_area_1 = st.checkbox(f"{LANG['Ігнорувати великі структури']}", value=False, key="checkbox12")
        if exclude_max_area_1:
            min_value_nm = max(1, int(scale_nm_px))
            max_value_nm = int(min(width, height) * scale_nm_px)
            curr_value_nm = int(max_value_nm / 2)
            max_diameter = st.number_input(f"{LANG['Максимальний діаметр (нм)']}", min_value_nm, max_value_nm,
                                           curr_value_nm, key="diameter12")
            max_area = int(np.pi * (max_diameter / scale_nm_px) ** 2 / 4)
        else:
            max_area = width * height
            max_diameter = int(min(width, height) * scale_nm_px)

        options = {
            "none": f"{LANG['Без обробки']}",
            "exclude_border": f"{LANG['Ігнорувати структури на границях']}",
            "periodic_conditions": f"{LANG['Застосувати періодичні граничні умови']}"
        }

        mode1 = st.radio(
            f"{LANG['Обробка меж: ']}",
            list(options.keys()),
            format_func=lambda x: options[x],
            key="radio1"
        )

        run_sens = st.button(f"▶️ {LANG['Запустити тест']}")

    if run_sens:
        # with toptabs[0]:
            if h_min >= h_max:
                st.error("Мінімальна висота має бути меншою за максимальну")
            else:
                h_range = range(h_min, h_max + step_h, step_h)
                res_sens = []
                prog = st.progress(0)
                for i, h_val in enumerate(h_range):
                    d_tmp = analyze_batch(image_gray, h_val, min_area, max_area, scale_nm_px, z_scale, mode1,
                                          st.session_state.thresh_type)
                    if not d_tmp.empty:
                        mean_d = np.sqrt(4 * d_tmp['Area (nm^2)'].mean() / np.pi)
                        res_sens.append({'h0': int(h_val * z_scale), 'Count': len(d_tmp), 'Mean_diameter': mean_d})
                    else:
                        res_sens.append({'h0': int(h_val * z_scale), 'Count': 0.0, 'Mean_diameter': 0.0})
                    prog.progress(int((i + 1) / len(h_range) * 100))

                df_sens = pd.DataFrame(res_sens)
                st.session_state.res_sens = df_sens
                st.session_state.conditions1 = [exclude_min_area_1, min_diameter, exclude_max_area_1, max_diameter, mode1]
                # st.success(f"✅ {LANG['Розрахунок завершено']}")
                prog.empty()
                st.toast(f"{LANG['Розрахунок завершено']} 👍", icon="✅")
                st.session_state.display_h0 = st.session_state.analysis["opt_h"]

    fig_num_size = None
    zip_data_num_size_height = None
    if st.session_state.res_sens is not None:
        col1sn, col2sn = st.columns(2)
        with col1sn:
            use_log_area = st.checkbox(LANG["Логарифмічна шкала розмірів"], value=False)
        present_numbers = {
            "numbers": f"{LANG['Кількість структур']} {LANG['(шт)']}",
            "numdens": f"{LANG['Густина структур']} {LANG['(см⁻²)']}"
        }
        with col2sn:
            mode_numbers = st.radio(
                f"{LANG['Кількість структур']} {LANG['(шт)']} / {LANG['Густина структур']} {LANG['(см⁻²)']}",
                list(present_numbers.keys()),
                format_func=lambda x: present_numbers[x],
                key="radio01"
            )
        df_sens = st.session_state.res_sens
        st.markdown(f"📈 **{LANG['Залежність кількості структур та середнього розміру від порогу висоти поверхні']}**")
        dict_for_fig_numsize = {}
        st.session_state.dict_for_fig_numsize = None
        dict_for_fig_numsize["mode_numbers"] = mode_numbers
        dict_for_fig_numsize["full_image_area_nm2"] = full_image_area_nm2
        dict_for_fig_numsize["use_log_area"] = use_log_area
        st.session_state.dict_for_fig_numsize = dict_for_fig_numsize

        # y1label = None
        # y2label = None
        if mode_numbers == "numbers":
            y1label = f"{LANG['Кількість структур']} {LANG['(шт)']}"
        elif mode_numbers == "numdens":
            y1label = f"{LANG['Густина структур']} {LANG['(см⁻²)']}"
        else:
            y1label = None
        xlabel = LANG['Висота поверхні (нм)']
        if use_log_area:
            y2label = f"{LANG['Середній розмір структур (нм)']} [Log Scale]"
        else:
            y2label = LANG['Середній розмір структур (нм)']

        fig_num_size = make_figure_numsize_png(df_sens['h0'], df_sens['Count'], df_sens['Mean_diameter'],
                                               mode_numbers, full_image_area_nm2, use_log_area,
                                               st.session_state.display_h0, y1label, y2label, xlabel, text_in_fig)

        st.image(fig_num_size, use_container_width=True)

        st.session_state["zip_num_size_height_ready"] = False
        col1, col2 = st.columns(2)
        with col1:
            mk_zip_num_size_height = st.button(
                f"📦 {LANG['Зробити ZIP архів з даними']}",
                key="mk_zip_num_size_height",
                disabled=(role == "viewer")
            )
        if mk_zip_num_size_height:
            datasets_num_size_height = {
                "number(height).txt": list(zip(df_sens['h0'], df_sens['Count'])),
                "diameter(height).txt": list(zip(df_sens['h0'], df_sens['Mean_diameter']))
            }
            zip_data_num_size_height = make_zip_from_dict(datasets_num_size_height, fig_num_size,
                                                          "fig_num_size(height).png")
            st.session_state["zip_num_size_height"] = zip_data_num_size_height
            st.session_state["zip_num_size_height_ready"] = True
        with col2:
            if st.session_state.get("zip_num_size_height_ready", False):
                st.download_button(
                    label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                    data=zip_data_num_size_height,
                    file_name="statistics_on_height.zip",
                    mime="application/zip",
                    disabled=(role == "viewer")
                )

        st.success(f"{LANG['Оптимальне значення висоти h₀']} = {round(st.session_state.display_h0)}  {LANG['(нм)']}")

    return fig_num_size


@st.fragment
def segmentation_and_filtration():
    if st.session_state.analysis is None:
        return None, None, None, None

    st.divider()
    st.subheader(f"🔢 {LANG['Сегментація та фільтрація']}")
    res = st.session_state.analysis
    image_gray = res["image"]
    blur = cv2.GaussianBlur(image_gray, (3, 3), 0)
    # topo_map = res["topo_map"]
    z_scale = res["z_scale"]
    width = res["width"]
    height = res["height"]
    scale_nm_px = res["scale_nm_px"]
    # full_image_area_nm2 = res["full_image_area_nm2"]
    full_area_cm2 = res["full_image_area_nm2"] * 1E-14

    # min_area = 0
    # min_diameter = 0
    # max_diameter = min(height, width) * scale_nm_px
    # max_area = height * width
    c_set1, c_set2 = st.columns(2)
    with (c_set1):
        h0_nm = st.slider(LANG["Встановити поріг висоти h₀"], 0, int(255 * z_scale), round(st.session_state.display_h0))
        # display_h0 = h0_nm
        h0 = int(h0_nm / z_scale)
        exclude_min_area = st.checkbox(f"{LANG['Ігнорувати малі структури']}", value=True, key="checkbox21")
        if exclude_min_area:
            max_value_nm = int(min(width, height) * scale_nm_px)
            curr_value_nm = max(1, int(scale_nm_px))
            min_diameter = st.number_input(f"{LANG['Мінімальний діаметр (нм)']}", 0, max_value_nm, curr_value_nm,
                                           key="diameter21")
            min_area = round(np.pi * (min_diameter / scale_nm_px) ** 2 / 4)
        else:
            min_area = 0
            min_diameter = 0
        exclude_max_area = st.checkbox(f"{LANG['Ігнорувати великі структури']}", value=False, key="checkbox22")
        if exclude_max_area:
            min_value_nm = max(1, int(scale_nm_px))
            max_value_nm = int(min(width, height) * scale_nm_px)
            curr_value_nm = int(max_value_nm / 2)
            max_diameter = st.number_input(f"{LANG['Максимальний діаметр (нм)']}", min_value_nm, max_value_nm,
                                           curr_value_nm, key="diameter22")
            max_area = round(np.pi * (max_diameter / scale_nm_px) ** 2 / 4)
        else:
            max_area = width * height
            max_diameter = int(min(width, height) * scale_nm_px)

        options = {
            "none": f"{LANG['Без обробки']}",
            "exclude_border": f"{LANG['Ігнорувати структури на границях']}",
            "periodic_conditions": f"{LANG['Застосувати періодичні граничні умови']}"
        }
        mode = st.radio(
            f"{LANG['Обробка меж:']}",
            list(options.keys()),
            format_func=lambda x: options[x],
            key="radio2"
        )

        _, mask = cv2.threshold(blur, h0, 255, st.session_state.thresh_type)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        num_labels, labels = cv2.connectedComponents(mask)
        num_labels, labels = remove_minmax_area(num_labels, labels, min_area, max_area)
        # mask = np.array(mask, dtype=np.uint8)
        if mode == "periodic_conditions":
            num_labels, labels = merge_periodic_labels(labels)

        elif mode == "exclude_border":
            labels = remove_border_labels(labels)
            labels = np.array(labels, dtype=np.uint8)
            num_labels, labels = cv2.connectedComponents((labels > 0).astype(np.uint8))

        else:
            labels = np.array(labels, dtype=np.uint8)
            num_labels, labels = cv2.connectedComponents((labels > 0).astype(np.uint8))

        st.session_state.labels = labels
        st.session_state.conditions2 = [exclude_min_area, min_diameter, exclude_max_area, max_diameter, mode, h0_nm]
        num_of_structures = num_labels - 1

        if num_of_structures > 0:
            st.success(
                f"{num_of_structures} {LANG['структур ідентифіковано']}  \n {LANG['Густина структур']} = {num_of_structures / full_area_cm2 / 1E10:.2f} x 10¹⁰ {LANG['(см⁻²)']}")
            st.session_state.n_bins = st.slider(LANG["Кількість бінів для розподілів"], 0, min(20, num_of_structures),
                                                min(15, num_of_structures // 2))
        else:
            st.warning(LANG["Структури не знайдені"])

        # start_analyze = st.button(f"▶️ {LANG['Почати аналіз']}")

    with c_set2:
        st.markdown(f"🖼️ **{LANG['Відфільтроване зображення']}**")
        filtered_image = show_filtered_image(labels)
        c_set2.image(filtered_image, use_container_width=True)
        st.session_state.filtered_image = filtered_image
        img_pil = PILImage.fromarray(filtered_image)
        img_bytes = io.BytesIO()
        img_pil.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        st.session_state.filtered_image_png = img_bytes
        st.download_button(
            label=f"💾 {LANG['Завантажити зображення']}",
            data=img_bytes,
            file_name=f"segmented_structures_h{int(h0_nm)}_min{int(min_diameter)}_max{int(max_diameter)}.png",
            mime="image/png",
            disabled=(role == "viewer")
        )

    return filtered_image, h0_nm, min_diameter, max_diameter


@st.fragment
def show_table_with_statistics():
    if st.session_state.data_frame is None:
        return None

    if st.session_state.lang != "EN":
        table_caption = st.session_state.table_caption_UA
    else:
        table_caption = st.session_state.table_caption_EN
    st.markdown(f"🔢 **{table_caption}**")

    stats_df_ui = table_statistics(st.session_state.table_statistics.copy(), st.session_state.lang)
    st.session_state.table_statistics_ui = stats_df_ui

    st.dataframe(
        stats_df_ui.style.format("{:.2f}"),
        use_container_width=True
    )
    st.session_state["zip_table_statistics_ready"] = False
    zip_data_table_statistics = None
    col1, col2 = st.columns(2)
    with col1:
        mk_zip_table_statistics = st.button(
            f"📦 {LANG['Зробити ZIP архів з даними']}",
            key="mk_zip_table_statistics",
            disabled=(role == "viewer")
        )
    if mk_zip_table_statistics:
        # df_statistics = st.session_state.table_statistics.copy()
        df_statistics = st.session_state.table_statistics_ui.copy()
        # df_statistics.rename(index=cols_en, inplace=True)
        # df_statistics.rename(columns={
        #     "min": "Minimum",
        #     "max": "Maximum",
        #     "mean": "Mean",
        #     "median": "Median",
        #     "std": "Std. Dev.",
        #     "CV (%)": "CV (%)"
        # }, inplace=True)
        csv_bytes = df_statistics.to_csv(index=True, float_format="%.2f").encode("utf-8-sig")
        txt_data = df_statistics.to_csv(sep="\t", index=True, float_format="%.2f")
        zip_data_table_statistics = build_statistics_zip(csv_bytes, txt_data,
                                                         st.session_state.filtered_image_png.getvalue(),
                                                         "filtered_image.png")
        st.session_state["zip_table_statistics"] = zip_data_table_statistics
        st.session_state["zip_table_statistics_ready"] = True
    with col2:
        if st.session_state.get("zip_table_statistics_ready", False):
            st.download_button(
                label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                data=zip_data_table_statistics,
                file_name="geometric_statistics.zip",
                mime="application/zip",
                disabled=(role == "viewer")
            )


@st.fragment
def show_distribution(
    name_prefix,          # "area", "diameter", ...
    option_for_xaxis,
    option_for_yaxis,
    color,
    data_label
):
    if st.session_state.data_frame is None:
        return None, None

    col_xaxis, col_yaxis, col_approx = st.columns(3)

    with col_xaxis:
        is_disabled_x = name_prefix in ["aspect", "circularity"]
        mode_x = st.radio(
            LANG['Формат розмірів'],
            list(option_for_xaxis.keys()),
            format_func=lambda x: option_for_xaxis[x],
            key=f"{name_prefix}_x",
            index=0,
            disabled=is_disabled_x
        )

    with col_yaxis:
        is_disabled_y = name_prefix in ["distances_centers", "distances_edge2edge"]
        mode_y = st.radio(
            LANG['Тип гістограми'],
            list(option_for_yaxis.keys()),
            format_func=lambda x: option_for_yaxis[x],
            key=f"{name_prefix}_y",
            index=0,
            disabled=is_disabled_y
        )

    prefix = f"log({name_prefix})" if mode_x == "log" else name_prefix
    key = f"{prefix}_{mode_y}"

    distribs = st.session_state.dict_calculated_distributions.get(key)
    datasets = st.session_state.dict_calculated_datasets.get(key)
    value_dist, value_dens, value_xlable = make_dicts_for_figures()

    titles_dict = {
        "dist": (
            LANG[f"{value_dist[name_prefix]}"],
            LANG_EN[f"{value_dist[name_prefix]}"],
            LANG['Частота зустрічання'],
            LANG_EN['Частота зустрічання']
        ),
        "dens": (
            LANG[f"{value_dens[name_prefix]}"],
            LANG_EN[f"{value_dens[name_prefix]}"],
            LANG['Густина структур (см⁻²)'],
            LANG_EN['Густина структур (см⁻²)']
        )
    }

    title, caption, ylabel, ylabel_EN = titles_dict[mode_y]
    st.markdown(f"**{title}**")
    label = LANG[value_xlable[name_prefix]]
    xlabel = f"log₁₀({label})" if mode_x == "log" else label

    label_EN = LANG_EN[value_xlable[name_prefix]]
    xlabel_EN = f"log₁₀({label_EN})" if mode_x == "log" else label_EN

    gaus_ok = distribs["gauss_fit_ok"]
    logn_ok = distribs["ln_fit_ok"]
    mean_val = distribs["mean"]

    if not gaus_ok:
        st.session_state[f"show_gaus_{name_prefix}"] = False
    if not logn_ok:
        st.session_state[f"show_logn_{name_prefix}"] = False

    with col_approx:
        show_mean = st.checkbox(
            LANG["Показати середнє значення"],
            key=f"show_mean_{name_prefix}"
        )
        show_gaus = st.checkbox(
            LANG["Показати Gaussian fit"],
            key=f"show_gaus_{name_prefix}",
            disabled=(not gaus_ok)
        )
        show_logn = st.checkbox(
            LANG["Показати Log-Normal fit"],
            key=f"show_logn_{name_prefix}",
            disabled=(not logn_ok)
        )

    fig = make_figure_distribution_png(
        distribs, color, xlabel, ylabel, data_label,
        show_gaus, show_logn, show_mean, mean_val,
        text_in_fig
    )
    st.image(fig, use_container_width=True)
    st.session_state[f"plot_for_report_{name_prefix}"] = {
        "distribs": distribs,
        "color": color,
        "xlabel": xlabel_EN,
        "ylabel": ylabel_EN,
        # "data_label": data_label,
        "show_gaus": show_gaus,
        "show_logn": show_logn,
        "show_mean": show_mean,
        "mean_val": mean_val
    }

    if not gaus_ok:
        st.warning(LANG["Gaussian fit не зійшовся"])
    if not logn_ok:
        st.warning(LANG["Log-Normal fit не зійшовся"])

    fig_fname = f"fig_{key}.png"
    zip_fname = f"{key}_analysis.zip"
    st.session_state[f"zip_{name_prefix}_ready"] = False
    zip_data = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            f"📦 {LANG['Зробити ZIP архів з даними']}",
            key=f"mk_zip_{name_prefix}",
            disabled=(role == "viewer")
        ):
            zip_data = make_zip_from_dict(datasets, fig, fig_fname)
            st.session_state[f"zip_{name_prefix}"] = zip_data
            st.session_state[f"zip_{name_prefix}_ready"] = True

    with col2:
        if st.session_state.get(f"zip_{name_prefix}_ready", False):
            st.download_button(
                label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                data=st.session_state[f"zip_{name_prefix}"],
                file_name=zip_fname,
                mime="application/zip"
            )

    return fig, caption


@st.fragment
def show_pairplot():
    if st.session_state.clustering is None:
        return None

    plot_data = st.session_state.clustering
    lang = st.session_state.lang
    fig_pairplot = make_pairplot(plot_data, lang)
    st.markdown(f"**{LANG['Зв’язки між розміром структур, коефіцієнтом округлості та кутом нахилу еліпса']}**")
    st.image(fig_pairplot, use_container_width=True)
    st.download_button(
        label=f"💾 {LANG['Завантажити Pairplot']}",
        data=fig_pairplot,
        file_name="fig_pairplot.png",
        mime="image/png",
        disabled=(role == "viewer")
    )
    return fig_pairplot

@st.fragment
def show_violinplot():
    if st.session_state.clustering is None:
        return None

    plot_data = st.session_state.clustering
    lang = st.session_state.lang
    st.markdown(f"**{LANG['Розподіл даних у різних групах']}**")

    if st.session_state.lang != "EN":
        ua_to_key = {v: k for k, v in labels_ua.items() if k in plot_data["vars"]}
        selected_ua = st.selectbox(LANG["Параметр"], list(ua_to_key.keys()))
        param = ua_to_key[selected_ua]

    else:
        en_to_key = {v: k for k, v in labels_en.items() if k in plot_data["vars"]}
        selected_en = st.selectbox(LANG["Параметр"], list(en_to_key.keys()))
        param = en_to_key[selected_en]

    fig_violinplot = make_violinplot(plot_data, lang, param)

    file_name_v = f"fig_violinplot_{param}.png"
    st.image(fig_violinplot, use_container_width=True)
    st.download_button(
        label=f"💾 {LANG['Завантажити Violinplot']}",
        data=fig_violinplot,
        file_name=file_name_v,
        mime="image/png",
        disabled=(role == "viewer")
    )

    return fig_violinplot


###########################################################################################################

with toptabs[0]:
    make_invert_image, real_width_nm, real_height_nm = crop_fragment()
    if st.session_state.original_image is not None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            run_button_analyze = st.button(f"🔍 {LANG['Аналізувати']}", use_container_width=True)


if run_button_analyze:
    cropped_img = st.session_state.cropped_image
    if make_invert_image:
        hsv = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = 255 - hsv[:, :, 2]
        cropped_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    dict_analysis, data_roughness = run_button_analysis(
        cropped_img,
        real_width_nm,
        real_height_nm,
        st.session_state.thresh_type
    )

    st.session_state.image = cropped_img
    st.session_state.analysis = dict_analysis
    st.session_state.roughness = data_roughness
    st.session_state.table_roughness, _ = st.session_state.roughness
    st.session_state.display_h0 = dict_analysis["mean_h"]
    st.session_state.data_frame = None
    st.session_state.res_sens = None
    st.session_state.clustering = None

with toptabs[0]:
    fig_heights = show_statistics_surface()
    fig_num_size = height_dependent_analysis()
    filtered_image, h0_nm, min_diameter, max_diameter = segmentation_and_filtration()
    if st.session_state.filtered_image is not None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            start_analyze = st.button(f"▶️ {LANG['Почати аналіз']}", use_container_width=True)

if start_analyze:
    st.session_state.clustering = None
    res = st.session_state.analysis
    topo_map = res["topo_map"]
    scale_nm_px = res["scale_nm_px"]
    full_image_area_nm2 = res["full_image_area_nm2"]
    full_area_cm2 = res["full_image_area_nm2"] * 1E-14
    nbins = st.session_state.n_bins  # 15
    labels = st.session_state.labels
    num_grains, centroids_stat, df_dist, df, stats_df = run_button_calculations(labels,
                                                                                scale_nm_px,
                                                                                full_image_area_nm2,
                                                                                topo_map)
    st.session_state.centroids_stat = centroids_stat
    st.session_state.distances = df_dist
    st.session_state.data_frame = df
    st.session_state.table_statistics = stats_df
    # print(st.session_state.table_statistics)
    with toptabs[0]:
        if num_grains > 1:
            # show_table_with_statistics()
            dict_distribs, dict_datasets = calc_all_distributions(df, nbins, full_area_cm2)
            st.session_state.dict_calculated_distributions = dict_distribs
            st.session_state.dict_calculated_datasets = dict_datasets
            st.session_state.table_caption_UA = f"Статистичні характеристики структур з розмірами від {int(min_diameter)} (нм) до {int(max_diameter)} (нм) на висоті h₀ = {int(h0_nm)} (нм)"
            st.session_state.table_caption_EN = f"Statistical properties of structures with sizes from {int(min_diameter)} (nm) to {int(max_diameter)} (nm) on a height h₀ = {int(h0_nm)} (nm)"
        else:
            st.warning(LANG["Зерна не знайдені"])

with toptabs[0]:
    if st.session_state.data_frame is not None:

        show_table_with_statistics()
        st.divider()
        st.subheader(f"📊 {LANG['Графічний Аналіз']}")
        tabs = st.tabs([
            f"📊 **{LANG['Розподіли розмірів']}**",
            f"📈 **{LANG['Геометрія структур']}**",
            f"📊 **{LANG['Розподіл відстаней']}**",
            f"🤖 **{LANG['Кластеризація']}**",
            f"📝 **{LANG['Сформувати звіт']}**"
        ])

        option_for_xaxis = {
            "none": f"{LANG['Без перетворень']}",
            "log": f"{LANG['Логарифмічне перетворення']}"
        }
        option_for_yaxis = {
            "dist": f"{LANG['Нормований розподіл']}",
            "dens": f"{LANG['Густина структур']}"
        }
        with tabs[0]:
            fig_area, caption_area = show_distribution("area", option_for_xaxis, option_for_yaxis, 'orange', LANG['Дані'])
            st.divider()
            fig_diameter, caption_diameter = show_distribution("diameter", option_for_xaxis, option_for_yaxis, 'orange', LANG['Дані'])
            st.divider()
            fig_perimeter, caption_perimeter = show_distribution("perimeter", option_for_xaxis, option_for_yaxis, 'orange', LANG['Дані'])

        with tabs[1]:
            fig_circularity, caption_circularity = show_distribution("circularity", option_for_xaxis, option_for_yaxis, 'green', LANG['Дані'])
            st.divider()
            fig_aspect, caption_aspect = show_distribution("aspect", option_for_xaxis, option_for_yaxis, 'green', LANG['Дані'])
            st.divider()
            fig_majoraxis, caption_majoraxis = show_distribution("majoraxis", option_for_xaxis, option_for_yaxis, 'green', LANG['Дані'])
            st.divider()
            fig_minoraxis, caption_minoraxis = show_distribution("minoraxis", option_for_xaxis, option_for_yaxis, 'green', LANG['Дані'])
            st.divider()
            fig_angle, caption_angle = show_distribution("angle", option_for_xaxis, option_for_yaxis, 'green', LANG['Дані'])

        with tabs[2]:
            R_value = st.session_state.centroids_stat.loc[
                st.session_state.centroids_stat["Param"] == "R-Index center", "Value"].values[0]
            fig_label = f"{LANG['Дані: Індекс Кларка-Еванса']} (R={R_value:.2f})"
            fig_distances_centers, caption_distances_centers = show_distribution("distances_centers", option_for_xaxis, option_for_yaxis, 'teal', fig_label)
            st.divider()
            R_value = st.session_state.centroids_stat.loc[
                st.session_state.centroids_stat["Param"] == "R-Index grains", "Value"].values[0]
            fig_label = f"{LANG['Дані: Індекс Кларка-Еванса']} (R={R_value:.2f})"
            fig_distances_edge2edge, caption_distances_edge2edge = show_distribution("distances_edge2edge", option_for_xaxis, option_for_yaxis, 'teal', fig_label)

        with tabs[3]:
            st.markdown(f"**{LANG['Кластеризація']}**")
            col_in, col_out = st.columns(2)
            with col_in:
                n_cl = st.slider(LANG["Кількість кластерів"], 2, 5, 3)
            with col_out:
                input_ncl = st.button(f"▶️ {LANG['Провести кластеризацію']}")

            if input_ncl:
                df = st.session_state.data_frame
                df_plot = df[['Diameter (nm)', 'Circularity', 'Angle of elips']].copy()
                plot_data = make_clusterization(df_plot, n_cl)
                st.session_state.clustering = plot_data

            fig_pairplot = show_pairplot()
            st.divider()
            fig_violinplot = show_violinplot()

        # REPORT
        with tabs[4]:
            image_name = st.session_state.original_image_file_name
            # plot_data = st.session_state.clustering
            st.markdown(f"**{LANG['Формування звіту за результатами аналізу зображення']} ({image_name})**")
            col1d, col2d = st.columns(2)
            with col1d:
                gen_rep = st.button(
                    f"▶️ {LANG['Згенерувати PDF звіту']}",
                    #disabled=(role == "viewer")
                )
            if gen_rep:
                if st.session_state.lang != "EN":
                    dic = st.session_state[f"plot_for_report_area"]
                    fig_area = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    dic = st.session_state[f"plot_for_report_diameter"]
                    fig_diameter = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    dic = st.session_state[f"plot_for_report_perimeter"]
                    fig_perimeter = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)

                    dic = st.session_state[f"plot_for_report_circularity"]
                    fig_circularity = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    dic = st.session_state[f"plot_for_report_majoraxis"]
                    fig_majoraxis = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    dic = st.session_state[f"plot_for_report_minoraxis"]
                    fig_minoraxis = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    dic = st.session_state[f"plot_for_report_aspect"]
                    fig_aspect = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    dic = st.session_state[f"plot_for_report_angle"]
                    fig_angle = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], LANG_EN["Дані"],
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)

                    R_value = st.session_state.centroids_stat.loc[
                        st.session_state.centroids_stat["Param"] == "R-Index center", "Value"].values[0]
                    fig_label = f"{LANG_EN['Дані: Індекс Кларка-Еванса']} (R={R_value:.2f})"
                    dic = st.session_state[f"plot_for_report_distances_centers"]
                    fig_distances_centers = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], fig_label,
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)
                    R_value = st.session_state.centroids_stat.loc[
                        st.session_state.centroids_stat["Param"] == "R-Index grains", "Value"].values[0]
                    fig_label = f"{LANG_EN['Дані: Індекс Кларка-Еванса']} (R={R_value:.2f})"
                    dic = st.session_state[f"plot_for_report_distances_edge2edge"]
                    fig_distances_edge2edge = make_figure_distribution_png(
                        dic["distribs"], dic["color"], dic["xlabel"], dic["ylabel"], fig_label,
                        dic["show_gaus"], dic["show_logn"], dic["show_mean"], dic["mean_val"], text_in_fig)

                if st.session_state.roughness is not None:
                    df_roughness = st.session_state.table_roughness
                    df_roughness = (df_roughness.rename(columns={"Param": LANG_EN["Параметр"], "Value": LANG_EN["Значення"]}))
                    cols_names = roughness_en
                    df_roughness[LANG_EN["Параметр"]] = df_roughness[LANG_EN["Параметр"]].map(cols_names)
                    tables_dict_without_index = {
                        "Surface roughness parameters": df_roughness
                    }

                if st.session_state.data_frame is not None:
                    df_statistics = st.session_state.table_statistics.copy()
                    df_statistics.rename(index=cols_en, inplace=True)
                    df_statistics.rename(columns={
                        "min": "Minimum",
                        "max": "Maximum",
                        "mean": "Mean",
                        "median": "Median",
                        "std": "Std. Dev.",
                        "CV (%)": "CV (%)"
                    }, inplace=True)
                    tables_dict_with_index = {
                        st.session_state.table_caption_EN: df_statistics
                    }

                # tables_dict_without_index = {
                #     "Surface roughness parameters": df_roughness
                # }
                # tables_dict_with_index = {
                #     st.session_state.table_caption_EN: df_statistics
                # }

                figs_dict_size = {
                    name: fig for name, fig in {
                        caption_area: fig_area,
                        caption_diameter: fig_diameter,
                        caption_perimeter: fig_perimeter
                    }.items() if fig is not None
                }

                figs_dict_geometry = {
                    name: fig for name, fig in {
                        caption_circularity: fig_circularity,
                        caption_aspect: fig_aspect,
                        caption_majoraxis: fig_majoraxis,
                        caption_minoraxis: fig_minoraxis,
                        caption_angle: fig_angle
                    }.items() if fig is not None
                }

                figs_dict_distances = {
                    name: fig for name, fig in {
                        caption_distances_centers: fig_distances_centers,
                        caption_distances_edge2edge: fig_distances_edge2edge
                    }.items() if fig is not None
                }
                if st.session_state.lang != "EN":
                    fig_heights = make_figure_distribution_png(st.session_state.analysis["dict"],
                                                           'gray', LANG_EN['Діапазон висот (нм)'],
                                                           LANG_EN['Частота зустрічання'], LANG_EN['Дані'],
                                                           st.session_state.dict_for_distrib_heights["show_gaus"],
                                                           st.session_state.dict_for_distrib_heights["show_logn"],
                                                           st.session_state.dict_for_distrib_heights["show_height"],
                                                           st.session_state.dict_for_distrib_heights["mean_height"],
                                                           text_in_fig, cache_buster=time.time())

                figs_dict_heights = {LANG_EN['Розподіл висот']: fig_heights}

                if st.session_state.res_sens is not None:
                    if st.session_state.lang != "EN":

                        if st.session_state.dict_for_fig_numsize["mode_numbers"] == "numbers":
                            y1label = f"{LANG_EN['Кількість структур']} {LANG_EN['(шт)']}"
                        elif st.session_state.dict_for_fig_numsize["mode_numbers"] == "numdens":
                            y1label = f"{LANG_EN['Густина структур']} {LANG_EN['(см⁻²)']}"
                        else:
                            y1label = None
                        xlabel = LANG_EN['Висота поверхні (нм)']
                        if st.session_state.dict_for_fig_numsize["use_log_area"]:
                            y2label = f"{LANG_EN['Середній розмір структур (нм)']} [Log Scale]"
                        else:
                            y2label = LANG_EN['Середній розмір структур (нм)']

                        fig_num_size = make_figure_numsize_png(st.session_state.res_sens['h0'],
                                                               st.session_state.res_sens['Count'],
                                                               st.session_state.res_sens['Mean_diameter'],
                                                               st.session_state.dict_for_fig_numsize["mode_numbers"],
                                                               st.session_state.dict_for_fig_numsize["full_image_area_nm2"],
                                                               st.session_state.dict_for_fig_numsize["use_log_area"],
                                                               st.session_state.display_h0,
                                                               y1label, y2label, xlabel, text_in_fig)

                    figs_dict_num_size = {LANG_EN['Залежність кількості структур та середнього розміру від порогу висоти поверхні']: fig_num_size}
                else:
                    figs_dict_num_size = None

                if st.session_state.clustering is not None:
                    plot_data = st.session_state.clustering
                    fig_pairplot = sns.pairplot(
                        plot_data["df"],
                        vars=plot_data["vars"],
                        hue='Label',
                        height=2,
                        aspect=1.5,
                        hue_order=plot_data["order"]
                    )
                    fig_pairplot._legend.set_title("")
                    for text in fig_pairplot._legend.get_texts():
                        text.set_fontsize(12)
                    fig_pairplot.fig.text(s=text_in_fig, **watermark_style)
                    figs_dict_clustering_pairplot = {LANG_EN['Зв’язки між розміром структур, коефіцієнтом округлості та кутом нахилу еліпса']: fig_pairplot.fig}
                    plt.close(fig_pairplot.fig)

                    figs_dict_clustering_violinplot = {}
                    for param in plot_data["vars"]:
                        fig_v, ax_v = plt.subplots(figsize=(10, 5))
                        sns.violinplot(
                            data=plot_data["df"],
                            x='Label',
                            y=param,
                            ax=ax_v,
                            palette='Set2',
                            order=plot_data["order"]
                        )
                        ax_v.set_ylabel(labels_en[param])
                        caption = labels_en[param]
                        ax_v.set_xlabel(LANG_EN["Кластери структур за розмірами"])
                        fig_v.text(s=text_in_fig, **watermark_style)
                        figs_dict_clustering_violinplot[
                            f"{LANG_EN['Кластери структур за розмірами']}: {caption}"
                        ] = fig_v
                        plt.close(fig_v)
                else:
                    figs_dict_clustering_pairplot = None
                    figs_dict_clustering_violinplot = None

                if st.session_state.original_image is not None:
                    img = st.session_state.original_image
                    uploaded_file_name = st.session_state.original_image_file_name
                    figs_dict_original_image = {f"{LANG_EN['Оригінальне зображення']}": pdf.image_to_figure(img, "", watermark_style_picture)}
                else:
                    figs_dict_original_image = None
                if st.session_state.filtered_image is not None:
                    img = st.session_state.filtered_image
                    figs_dict_filtered_image = {f"{LANG_EN['Відфільтроване зображення']}: {len(st.session_state.data_frame)} {LANG_EN['структур ідентифіковано']}": pdf.image_to_figure(img, text_in_fig, watermark_style_picture)}
                else:
                    figs_dict_filtered_image = None

                pdf_bytes = pdf.generate_pdf_report(
                    uploaded_file_name,real_width_nm,real_height_nm,
                    st.session_state.conditions1,st.session_state.conditions2,st.session_state.type_of_structures,
                    figs_dict_original_image,
                    tables_dict_without_index,
                    figs_dict_heights,
                    figs_dict_num_size,
                    figs_dict_filtered_image,
                    tables_dict_with_index,
                    figs_dict_size,
                    figs_dict_geometry,
                    figs_dict_distances,
                    figs_dict_clustering_pairplot,
                    figs_dict_clustering_violinplot
                )

                with col2d:
                    st.download_button(
                        label=f"💾 {LANG['Завантажити звіт у форматі PDF']}",
                        data=pdf_bytes,
                        file_name=f"report_{uploaded_file_name}.pdf",
                        mime="application/pdf",
                        #disabled=(role == "viewer")
                    )

st.divider()

# st.markdown(f"{LANG['[Сумський державний університет](https://sumdu.edu.ua)']}")
# "| 🏛️ [Applied Mathematics & Complex Systems Modeling](https://pom.sumdu.edu.ua/en/) "
st.markdown(f"🔬 AFM Ultimate Analytics | 🏫 {LANG['[Сумський державний університет](https://sumdu.edu.ua)']} "
            f"| 👤 {LANG['[Контакт](https://pom.sumdu.edu.ua/uk/kafedra/personalni-storinki/162-dvornichenko-a-v)']} "
            f"| © 2026 |")
st.divider()