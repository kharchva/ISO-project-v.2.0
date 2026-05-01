import streamlit as st
# from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
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


# def full_reset():
#     reset_analysis_state()
#     reset_crop()
#     reset_image()

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


    with st.expander(f"📏 {LANG['Калібрування']}", expanded=True):
        real_width_nm = st.number_input(LANG["Реальна ширина зображення (нм)"], value=600.0, min_value=1.0, step=100.0)
        real_height_nm = st.number_input(LANG["Реальна висота структур (нм)"], value=20.0, min_value=1.0, step=1.0)


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

if st.session_state.original_image is not None:
    with toptabs[0]:
        img_orig = st.session_state.original_image
        height, width, _ = img_orig.shape

        # Дефолтні відсотки обрізки
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
                st.number_input(f"{LANG['Зверху (%)']}", 0, 50, 0, step=1, key="top")
                st.number_input(f"{LANG['Знизу (%)']}", 0, 50, 0, step=1, key="bottom")
            with col22:
                st.number_input(f"{LANG['Зліва (%)']}", 0, 50, 0, step=1, key="left")
                st.number_input(f"{LANG['Справа (%)']}", 0, 50, 0, step=1, key="right")
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

            top_line = int(st.session_state.top / 100 * height)
            bottom_line = int(height - st.session_state.bottom / 100 * height)
            left_line = int(st.session_state.left / 100 * width)
            right_line = int(width - st.session_state.right / 100 * width)
            st.session_state.cropped_image = img_orig[top_line:bottom_line, left_line:right_line, :]
            run_button_analyze = st.button(f"🔍 {LANG['Аналізувати']}")

        with col1:
            st.markdown(f"🖼️ **{LANG['Оригінальне зображення']}**")

            # Розрахунок координат обрізки
            top_line = int(st.session_state.top / 100 * height)
            bottom_line = int(height - st.session_state.bottom / 100 * height)
            left_line = int(st.session_state.left / 100 * width)
            right_line = int(width - st.session_state.right / 100 * width)

            # Створюємо маску для затемнення обрізаної області
            overlay = img_orig.copy().astype(np.float32)
            mask = np.zeros((height, width), dtype=np.uint8)
            mask[:top_line, :] = 1
            mask[bottom_line:, :] = 1
            mask[:, :left_line] = 1
            mask[:, right_line:] = 1

            alpha = 0.5  # прозорість накриття
            color_overlay = np.array([0, 0, 100], dtype=np.float32)  # темно-синя накладка (RGB)
            overlay[mask == 1] = overlay[mask == 1] * (1 - alpha) + color_overlay * alpha

            overlay = overlay.astype(np.uint8)

            # Малюємо межі обрізки
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(overlay)
            ax.axis('off')
            # Горизонтальні лінії
            ax.hlines([top_line, bottom_line], xmin=-0.05 * width, xmax=1.05 * width,
                      colors='red', linewidth=1, linestyles='dashed', alpha=0.5)
            # Вертикальні лінії
            ax.vlines([left_line, right_line], ymin=-0.05 * height, ymax=1.05 * height,
                      colors='red', linewidth=1, linestyles='dashed', alpha=0.5)
            st.pyplot(fig, use_container_width=True)
if run_button_analyze:
    cropped_img = st.session_state.cropped_image
    if make_invert_image:
        hsv = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = 255 - hsv[:, :, 2]
        cropped_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    dict_analysis, data_roughness = run_button_analysis(cropped_img, real_width_nm, real_height_nm, st.session_state.thresh_type)

    st.session_state.image = cropped_img
    st.session_state.analysis = dict_analysis
    st.session_state.roughness = data_roughness
    st.session_state.display_h0 = dict_analysis["mean_h"]
    st.session_state.data_frame = None
    st.session_state.res_sens = None
    st.session_state.clustering = None


if st.session_state.analysis is not None:
    with toptabs[0]:
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

                st.session_state.table_roughness = df

                df = (df.rename(columns={"Param": LANG["Параметр"], "Value": LANG["Значення"]}))
                if st.session_state.lang == "EN":
                    cols_names = roughness_en
                else:
                    cols_names = roughness_ua
                df[LANG["Параметр"]] = df[LANG["Параметр"]].map(cols_names)

                st.dataframe(df.style.format({LANG["Значення"]: "{:.2f}"}), hide_index=True)
                data2save = df.to_csv(sep="\t", index=False, float_format="%.2f")
                # role = st.session_state.get("role", "viewer")
                st.download_button(
                    label=f"💾 {LANG['Завантажити дані у текстовий файл']}",
                    data=data2save,
                    file_name="roughness_data.txt",
                    mime="text/plain",
                    disabled=(role == "viewer")
                )

        dict_with_data = st.session_state.analysis["dict"]
        datasets = dict_with_data["datasets"]
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

        fig_heights = make_distribution_figs_and_data(dict_with_data,
                                                        15, 'gray', LANG['Діапазон висот (нм)'],
                                                      LANG['Частота зустрічання'], LANG['Дані'],
                                                        show_gaus, show_logn,
                                                        show_height, st.session_state.analysis["mean_h"],
                                                        text_in_fig)
        st.pyplot(fig_heights)
        # st.session_state.display_h0 = st.session_state.analysis["mean_h"]


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
        if mk_zip_height:
            zip_data_height = make_zip_from_dict(datasets, fig_heights, "fig_heights.png")
            st.session_state["zip_height"] = zip_data_height
            st.session_state["zip_height_ready"] = True
        with col2:
            if st.session_state.get("zip_height_ready", False):
                st.download_button(
                    label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                    data=zip_data_height,
                    file_name=st.session_state.analysis["fname"],
                    mime="application/zip",
                    disabled=(role == "viewer")
                )

        st.divider()

        st.subheader(f"🔢 {LANG['Аналіз кількості/розмірів структур на різних висотах']}")
        res = st.session_state.analysis
        c_set1, c_set2 = st.columns(2)
        image_gray = res["image"]
        z_scale = res["z_scale"]
        width = res["width"]
        height = res["height"]
        scale_nm_px = res["scale_nm_px"]
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
                min_diameter = st.number_input(f"{LANG['Мінімальний діаметр (нм)']}", 0, max_value_nm, curr_value_nm, key="diameter11")
                min_area = int(np.pi * (min_diameter/scale_nm_px)**2 / 4)
            else:
                min_area = 0
                min_diameter = 0
            exclude_max_area_1 = st.checkbox(f"{LANG['Ігнорувати великі структури']}", value=False, key="checkbox12")
            if exclude_max_area_1:
                min_value_nm = max(1, int(scale_nm_px))
                max_value_nm = int(min(width, height) * scale_nm_px)
                curr_value_nm = int(max_value_nm / 2)
                max_diameter = st.number_input(f"{LANG['Максимальний діаметр (нм)']}", min_value_nm, max_value_nm, curr_value_nm, key="diameter12")
                max_area = int(np.pi * (max_diameter/scale_nm_px)**2 / 4)
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
    with toptabs[0]:
        if h_min >= h_max:
            st.error("Мінімальна висота має бути меншою за максимальну")
        else:
            h_range = range(h_min, h_max + step_h, step_h)
            res_sens = []
            prog = st.progress(0)
            for i, h_val in enumerate(h_range):
                d_tmp = analyze_batch(image_gray, h_val, min_area, max_area, scale_nm_px, z_scale, mode1, st.session_state.thresh_type)
                if not d_tmp.empty:
                    mean_d = np.sqrt(4 * d_tmp['Area (nm^2)'].mean() / np.pi)
                    res_sens.append({'h0': int(h_val * z_scale), 'Count': len(d_tmp), 'Mean_diameter': mean_d})
                else:
                    res_sens.append({'h0': int(h_val * z_scale), 'Count': 0.0, 'Mean_diameter': 0.0})
                prog.progress(int((i + 1) / len(h_range) * 100))

            df_sens = pd.DataFrame(res_sens)
            st.session_state.res_sens = df_sens
            st.session_state.conditions1 = [exclude_min_area_1, min_diameter, exclude_max_area_1, max_diameter, mode1]
            st.success(f"✅ {LANG['Розрахунок завершено']}")
            st.session_state.display_h0 = st.session_state.analysis["opt_h"]


if st.session_state.res_sens is not None:
    with toptabs[0]:
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

        width = st.session_state.analysis["width"]
        height = st.session_state.analysis["height"]
        scale_nm_px = st.session_state.analysis["scale_nm_px"]
        full_image_area_nm2 = st.session_state.analysis["full_image_area_nm2"]
        df_sens = st.session_state.res_sens
        fig_num_size, ax1 = plt.subplots(figsize=(10, 5))
        if mode_numbers == "numbers":
            ax1.plot(df_sens['h0'], df_sens['Count'], 'r-o')
            ax1.set_ylabel(f"{LANG['Кількість структур']} {LANG['(шт)']}", color='r')
        if mode_numbers == "numdens":
            full_area_cm2 = full_image_area_nm2 * 1E-14
            ax1.plot(df_sens['h0'], df_sens['Count'] / full_area_cm2 , 'r-o')
            ax1.set_ylabel(f"{LANG['Густина структур']} {LANG['(см⁻²)']}", color='r')
        ax1.tick_params(axis='y', labelcolor='r')
        ax1.set_xlabel(LANG['Висота поверхні (нм)'])
        ax1.set_ylim(bottom=0)

        ax2 = ax1.twinx()
        ax2.plot(df_sens['h0'], df_sens['Mean_diameter'], 'b--s')
        ax2.set_ylabel(LANG['Середній розмір структур (нм)'], color='b')
        ax2.tick_params(axis='y', labelcolor='b')
        ax2.set_ylim(bottom=0.0)

        if use_log_area:
            ax2.set_yscale('log')
            ax2.set_ylabel(f"{LANG['Середній розмір структур (нм)']} [Log Scale]", color='b')
            ax2.set_ylim(bottom=1.0)

        ax1.axvline(st.session_state.display_h0, color='black', linestyle='--', linewidth=2)

        ax1.grid(
            True,
            color='gray',
            linestyle='--',
            linewidth=0.5
        )

        st.markdown(f"📈 **{LANG['Залежність кількості структур та середнього розміру від порогу висоти поверхні']}**")
        fig_num_size.text(s=text_in_fig, **watermark_style)
        st.pyplot(fig_num_size)

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
            zip_data_num_size_height = make_zip_from_dict(datasets_num_size_height, fig_num_size, "fig_num_size(height).png")
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


if st.session_state.analysis is not None:
    with toptabs[0]:
        st.divider()
        st.subheader(f"🔢 {LANG['Сегментація та фільтрація']}")
        res = st.session_state.analysis
        image_gray = res["image"]
        blur = cv2.GaussianBlur(image_gray, (3, 3), 0)
        topo_map = res["topo_map"]
        z_scale = res["z_scale"]
        width = res["width"]
        height = res["height"]
        scale_nm_px = res["scale_nm_px"]
        full_image_area_nm2 = res["full_image_area_nm2"]
        full_area_cm2 = res["full_image_area_nm2"] * 1E-14

        min_area = 0
        min_diameter = 0
        max_diameter = min(height, width) * scale_nm_px
        max_area = height * width
        c_set1, c_set2 = st.columns(2)
        with (c_set1):
            h0_nm = st.slider(LANG["Встановити поріг висоти h₀"], 0, int(255 * z_scale), round(st.session_state.display_h0))
            display_h0 = h0_nm
            h0 = int(h0_nm / z_scale)
            exclude_min_area = st.checkbox(f"{LANG['Ігнорувати малі структури']}", value=True, key="checkbox21")
            if exclude_min_area:
                max_value_nm = int(min(width, height) * scale_nm_px)
                curr_value_nm = max(1, int(scale_nm_px))
                min_diameter = st.number_input(f"{LANG['Мінімальний діаметр (нм)']}", 0, max_value_nm, curr_value_nm, key="diameter21")
                min_area = round(np.pi * (min_diameter/scale_nm_px)**2 / 4)
            else:
                min_area = 0
                min_diameter = 0
            exclude_max_area = st.checkbox(f"{LANG['Ігнорувати великі структури']}", value=False, key="checkbox22")
            if exclude_max_area:
                min_value_nm = max(1, int(scale_nm_px))
                max_value_nm = int(min(width, height) * scale_nm_px)
                curr_value_nm = int(max_value_nm / 2)
                max_diameter = st.number_input(f"{LANG['Максимальний діаметр (нм)']}", min_value_nm, max_value_nm, curr_value_nm, key="diameter22")
                max_area = round(np.pi * (max_diameter/scale_nm_px)**2 / 4)
            else:
                max_area = width * height
                max_diameter = int(min(width, height) * scale_nm_px)

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
            mask = np.array(mask, dtype=np.uint8)
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
                st.success(f"{num_of_structures} {LANG['структур ідентифіковано']}  \n {LANG['Густина структур']} = {num_of_structures/full_area_cm2/1E10:.2f} x 10¹⁰ {LANG['(см⁻²)']}")
                st.session_state.n_bins = st.slider(LANG["Кількість бінів для розподілів"], 0, min(20, num_of_structures), min(15, num_of_structures // 2))
            else:
                st.warning(LANG["Структури не знайдені"])

            start_analyze = st.button(f"▶️ {LANG['Почати аналіз']}")

        with c_set2:
            st.markdown(f"🖼️ **{LANG['Відфільтроване зображення']}**")
            max_label = labels.max() + 1
            colors = np.random.randint(0, 255, size=(max_label, 3), dtype=np.uint8)
            colors[0] = [255, 255, 255]
            viz = colors[labels]
            h, w = viz.shape[:2]
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

            c_set2.image(viz, use_container_width=True)
            st.session_state.filtered_image = viz;

            img_pil = PILImage.fromarray(viz)
            img_bytes = io.BytesIO()
            img_pil.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            st.download_button(
                label=f"💾 {LANG['Завантажити зображення']}",
                data=img_bytes,
                file_name=f"segmented_structures_h{int(h0_nm)}_min{int(min_diameter)}_max{int(max_diameter)}.png",
                mime="image/png",
                disabled=(role == "viewer")
            )

if start_analyze:
    st.session_state.clustering = None
    labels = st.session_state.labels
    num_grains, centroids_stat, df_dist, df, stats_df = run_button_calculations(labels,
                                                                                scale_nm_px,
                                                                                full_image_area_nm2,
                                                                                topo_map)
    st.session_state.centroids_stat = centroids_stat
    st.session_state.distances = df_dist
    st.session_state.data_frame = df
    st.session_state.table_statistics = stats_df

    if num_grains > 1:
        stats_df_ui = stats_df.copy()

        if st.session_state.lang == "EN":
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

        st.session_state.table_statistics_ui = stats_df_ui
        nbins = st.session_state.n_bins #15
        dict_calculated_distributions = calc_all_distributions(df, nbins, full_area_cm2)
        st.session_state.dict_calculated_distributions = dict_calculated_distributions
        st.session_state.table_caption_UA = f"Статистичні характеристики структур з розмірами від {int(min_diameter)} (нм) до {int(max_diameter)} (нм) на висоті h₀ = {int(h0_nm)} (нм)"
        st.session_state.table_caption_EN = f"Statistical properties of structures with sizes from {int(min_diameter)} (nm) to {int(max_diameter)} (nm) on a height h₀ = {int(h0_nm)} (nm)"
    else:
        st.warning(LANG["Зерна не знайдені"])


if st.session_state.data_frame is not None:
    with (toptabs[0]):
        if st.session_state.lang != "EN":
            table_caption = st.session_state.table_caption_UA
        else:
            table_caption = st.session_state.table_caption_EN
        st.markdown(f"🔢 **{table_caption}**")
        stats_df_ui = st.session_state.table_statistics_ui
        st.dataframe(
            stats_df_ui.style.format("{:.2f}"),
            use_container_width=True
        )
        st.session_state["zip_table_statistics_ready"] = False
        col1, col2 = st.columns(2)
        with col1:
            mk_zip_table_statistics = st.button(
                f"📦 {LANG['Зробити ZIP архів з даними']}",
                key="mk_zip_table_statistics",
                disabled=(role == "viewer")
            )
        if mk_zip_table_statistics:
            stats_df = st.session_state.table_statistics
            csv_bytes = stats_df.to_csv(index=True, float_format="%.2f").encode('utf-8-sig')
            data2save = stats_df.to_csv(sep="\t", index=True, float_format="%.2f")
            datasets_table_statistics = {
                "geometric_statistics.csv": csv_bytes,
                "geometric_statistics.txt": data2save
            }
            zip_data_table_statistics = make_zip_from_dict(datasets_table_statistics,
                                                           st.session_state.filtered_image,
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

        st.divider()

        nbins = st.session_state.n_bins

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

        # 1. Залежність густини структур від площі
        with tabs[0]:
            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_area = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="area1"
                )
            with col_yaxis:
                mode_y_area = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="area2"
                )
            prefix = "log(area)" if mode_x_area == "log" else "area"
            key = f"{prefix}_{mode_y_area}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_area_fname = f"fig_{key}.png"
            zip_area_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за площею'],
                    LANG_EN['Розподіл структур за площею'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від площі'],
                    LANG_EN['Залежність густини структур від площі'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_area, ylable = titles[mode_y_area]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Площа (нм²)']})"
                if mode_x_area == "log"
                else LANG['Площа (нм²)']
            )
            gaus_area = dict_calculated_distributions["gauss_fit_ok"]
            logn_area = dict_calculated_distributions["ln_fit_ok"]
            datasets_area = dict_calculated_distributions["datasets"]
            mean_area = dict_calculated_distributions["mean"]
            if not gaus_area:
                st.session_state["show_gaus_area"] = False
            if not logn_area:
                st.session_state["show_logn_area"] = False
            with col_approx:
                show_mean_area = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_area"
                )
                show_gaus_area = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_area",
                    disabled=(not gaus_area)
                )
                show_logn_area = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_area",
                    disabled=(not logn_area)
                )
            fig_area = make_distribution_figs_and_data(dict_calculated_distributions,
                                                                nbins, 'orange', xlable, ylable, LANG['Дані'],
                                                                show_gaus_area, show_logn_area,
                                                                show_mean_area, mean_area,
                                                                text_in_fig)
            st.pyplot(fig_area)
            if not gaus_area:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_area:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_area_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_area = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_area",
                    disabled=(role == "viewer")
                )
            if mk_zip_area:
                zip_data_area = make_zip_from_dict(datasets_area, fig_area, fig_area_fname)
                st.session_state["zip_area"] = zip_data_area
                st.session_state["zip_area_ready"] = True
            with col2:
                if st.session_state.get("zip_area_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_area,
                        file_name=zip_area_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_diameter = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="diameter1"
                )
            with col_yaxis:
                mode_y_diameter = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="diameter2"
                )
            prefix = "log(diameter)" if mode_x_diameter == "log" else "diameter"
            key = f"{prefix}_{mode_y_diameter}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_diameter_fname = f"fig_{key}.png"
            zip_diameter_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за діаметром'],
                    LANG_EN['Розподіл структур за діаметром'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від діаметра'],
                    LANG_EN['Залежність густини структур від діаметра'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_diameter, ylable = titles[mode_y_diameter]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Діаметр (нм)']})"
                if mode_x_diameter == "log"
                else LANG['Діаметр (нм)']
            )
            gaus_diameter = dict_calculated_distributions["gauss_fit_ok"]
            logn_diameter = dict_calculated_distributions["ln_fit_ok"]
            datasets_diameter = dict_calculated_distributions["datasets"]
            mean_diameter = dict_calculated_distributions["mean"]
            if not gaus_diameter:
                st.session_state["show_gaus_diameter"] = False
            if not logn_diameter:
                st.session_state["show_logn_diameter"] = False
            with col_approx:
                show_mean_diameter = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_diameter"
                )
                show_gaus_diameter = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_diameter",
                    disabled=(not gaus_diameter)
                )
                show_logn_diameter = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_diameter",
                    disabled=(not logn_diameter)
                )
            fig_diameter = make_distribution_figs_and_data(dict_calculated_distributions,
                                                                nbins, 'orange', xlable, ylable, LANG['Дані'],
                                                                show_gaus_diameter, show_logn_diameter,
                                                                show_mean_diameter, mean_diameter,
                                                                text_in_fig)
            st.pyplot(fig_diameter)
            if not gaus_diameter:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_diameter:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_diameter_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_diameter = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_diameter",
                    disabled=(role == "viewer")
                )
            if mk_zip_diameter:
                zip_data_diameter = make_zip_from_dict(datasets_diameter, fig_diameter, fig_diameter_fname)
                st.session_state["zip_diameter"] = zip_data_diameter
                st.session_state["zip_diameter_ready"] = True
            with col2:
                if st.session_state.get("zip_diameter_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_diameter,
                        file_name=zip_diameter_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_perimeter = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="perimeter1"
                )
            with col_yaxis:
                mode_y_perimeter = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="perimeter2"
                )
            prefix = "log(perimeter)" if mode_x_perimeter == "log" else "perimeter"
            key = f"{prefix}_{mode_y_perimeter}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_perimeter_fname = f"fig_{key}.png"
            zip_perimeter_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за периметром'],
                    LANG_EN['Розподіл структур за периметром'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від периметра'],
                    LANG_EN['Залежність густини структур від периметра'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_perimeter, ylable = titles[mode_y_perimeter]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Периметр (нм)']})"
                if mode_x_perimeter == "log"
                else LANG['Периметр (нм)']
            )
            gaus_perimeter = dict_calculated_distributions["gauss_fit_ok"]
            logn_perimeter = dict_calculated_distributions["ln_fit_ok"]
            datasets_perimeter = dict_calculated_distributions["datasets"]
            mean_perimeter = dict_calculated_distributions["mean"]
            if not gaus_perimeter:
                st.session_state["show_gaus_perimeter"] = False
            if not logn_perimeter:
                st.session_state["show_logn_perimeter"] = False
            with col_approx:
                show_mean_perimeter = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_perimeter"
                )
                show_gaus_perimeter = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_perimeter",
                    disabled=(not gaus_perimeter)
                )
                show_logn_perimeter = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_perimeter",
                    disabled=(not logn_perimeter)
                )
            fig_perimeter = make_distribution_figs_and_data(dict_calculated_distributions,
                                                                nbins, 'orange', xlable, ylable, LANG['Дані'],
                                                                show_gaus_perimeter, show_logn_perimeter,
                                                                show_mean_perimeter, mean_perimeter,
                                                                text_in_fig)
            st.pyplot(fig_perimeter)
            if not gaus_perimeter:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_perimeter:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_perimeter_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_perimeter = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_perimeter",
                    disabled=(role == "viewer")
                )
            if mk_zip_perimeter:
                zip_data_perimeter = make_zip_from_dict(datasets_perimeter, fig_perimeter, fig_perimeter_fname)
                st.session_state["zip_perimeter"] = zip_data_perimeter
                st.session_state["zip_perimeter_ready"] = True
            with col2:
                if st.session_state.get("zip_perimeter_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_perimeter,
                        file_name=zip_perimeter_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

        # 1. Розподіл структур за геометрією
        with tabs[1]:
            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_circularity = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="circularity1",
                    index = 0,  # "none"
                    disabled = True
                )
            with col_yaxis:
                mode_y_circularity = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="circularity2"
                )
            prefix = "log(circularity)" if mode_x_circularity == "log" else "circularity"
            key = f"{prefix}_{mode_y_circularity}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_circularity_fname = f"fig_{key}.png"
            zip_circularity_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за коефіцієнтом округлості'],
                    LANG_EN['Розподіл структур за коефіцієнтом округлості'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від коефіцієнта округлості'],
                    LANG_EN['Залежність густини структур від коефіцієнта округлості'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_circularity, ylable = titles[mode_y_circularity]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Коефцієнт окуглості']})"
                if mode_x_circularity == "log"
                else LANG['Коефцієнт окуглості']
            )
            gaus_circularity = dict_calculated_distributions["gauss_fit_ok"]
            logn_circularity = dict_calculated_distributions["ln_fit_ok"]
            datasets_circularity = dict_calculated_distributions["datasets"]
            mean_circularity = dict_calculated_distributions["mean"]
            if not gaus_circularity:
                st.session_state["show_gaus_circularity"] = False
            if not logn_circularity:
                st.session_state["show_logn_circularity"] = False
            with col_approx:
                show_mean_circularity = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_circularity"
                )
                show_gaus_circularity = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_circularity",
                    disabled=(not gaus_circularity)
                )
                show_logn_circularity = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_circularity",
                    disabled=(not logn_circularity)
                )
            fig_circularity = make_distribution_figs_and_data(dict_calculated_distributions,
                                                                nbins, 'green', xlable, ylable, LANG['Дані'],
                                                                show_gaus_circularity, show_logn_circularity,
                                                                show_mean_circularity, mean_circularity,
                                                                text_in_fig)
            st.pyplot(fig_circularity)
            if not gaus_circularity:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_circularity:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_circularity_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_circularity = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_circularity",
                    disabled=(role == "viewer")
                )
            if mk_zip_circularity:
                zip_data_circularity = make_zip_from_dict(datasets_circularity, fig_circularity, fig_circularity_fname)
                st.session_state["zip_circularity"] = zip_data_circularity
                st.session_state["zip_circularity_ready"] = True
            with col2:
                if st.session_state.get("zip_circularity_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_circularity,
                        file_name=zip_circularity_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_aspect = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="aspect1",
                    index = 0,  # "none"
                    disabled = True
                )
            with col_yaxis:
                mode_y_aspect = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="aspect2"
                )
            prefix = "log(aspect)" if mode_x_aspect == "log" else "aspect"
            key = f"{prefix}_{mode_y_aspect}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_aspect_fname = f"fig_{key}.png"
            zip_aspect_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за коефіцієнтом витягнутості'],
                    LANG_EN['Розподіл структур за коефіцієнтом витягнутості'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від коефіцієнта витягнутості'],
                    LANG_EN['Залежність густини структур від коефіцієнта витягнутості'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_aspect, ylable = titles[mode_y_aspect]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Коефіцієнт витягнутості']})"
                if mode_x_aspect == "log"
                else LANG['Коефіцієнт витягнутості']
            )
            gaus_aspect = dict_calculated_distributions["gauss_fit_ok"]
            logn_aspect = dict_calculated_distributions["ln_fit_ok"]
            datasets_aspect = dict_calculated_distributions["datasets"]
            mean_aspect = dict_calculated_distributions["mean"]
            if not gaus_aspect:
                st.session_state["show_gaus_aspect"] = False
            if not logn_aspect:
                st.session_state["show_logn_aspect"] = False
            with col_approx:
                show_mean_aspect = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_aspect"
                )
                show_gaus_aspect = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_aspect",
                    disabled=(not gaus_aspect)
                )
                show_logn_aspect = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_aspect",
                    disabled=(not logn_aspect)
                )
            fig_aspect = make_distribution_figs_and_data(dict_calculated_distributions,
                                                              nbins, 'green', xlable, ylable, LANG['Дані'],
                                                              show_gaus_aspect, show_logn_aspect,
                                                                show_mean_aspect, mean_aspect,
                                                                text_in_fig)
            st.pyplot(fig_aspect)
            if not gaus_aspect:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_aspect:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_aspect_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_aspect = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_aspect",
                    disabled=(role == "viewer")
                )
            if mk_zip_aspect:
                zip_data_aspect = make_zip_from_dict(datasets_aspect, fig_aspect, fig_aspect_fname)
                st.session_state["zip_aspect"] = zip_data_aspect
                st.session_state["zip_aspect_ready"] = True
            with col2:
                if st.session_state.get("zip_aspect_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_aspect,
                        file_name=zip_aspect_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_majoraxis = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="majoraxis1"
                )
            with col_yaxis:
                mode_y_majoraxis = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="majoraxis2"
                )
            prefix = "log(majoraxis)" if mode_x_majoraxis == "log" else "majoraxis"
            key = f"{prefix}_{mode_y_majoraxis}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_majoraxis_fname = f"fig_{key}.png"
            zip_majoraxis_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за довжиною великої вісі еліпса'],
                    LANG_EN['Розподіл структур за довжиною великої вісі еліпса'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від довжини великої вісі еліпса'],
                    LANG_EN['Залежність густини структур від довжини великої вісі еліпса'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_majoraxis, ylable = titles[mode_y_majoraxis]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Довжина великої вісі еліпса (нм)']})"
                if mode_x_majoraxis == "log"
                else LANG['Довжина великої вісі еліпса (нм)']
            )
            gaus_majoraxis = dict_calculated_distributions["gauss_fit_ok"]
            logn_majoraxis = dict_calculated_distributions["ln_fit_ok"]
            datasets_majoraxis = dict_calculated_distributions["datasets"]
            mean_majoraxis = dict_calculated_distributions["mean"]
            if not gaus_majoraxis:
                st.session_state["show_gaus_majoraxis"] = False
            if not logn_majoraxis:
                st.session_state["show_logn_majoraxis"] = False
            with col_approx:
                show_mean_majoraxis = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_majoraxis"
                )
                show_gaus_majoraxis = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_majoraxis",
                    disabled=(not gaus_majoraxis)
                )
                show_logn_majoraxis = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_majoraxis",
                    disabled=(not logn_majoraxis)
                )
            fig_majoraxis = make_distribution_figs_and_data(dict_calculated_distributions,
                                                              nbins, 'green', xlable, ylable, LANG['Дані'],
                                                              show_gaus_majoraxis, show_logn_majoraxis,
                                                                show_mean_majoraxis, mean_majoraxis,
                                                                text_in_fig)
            st.pyplot(fig_majoraxis)
            if not gaus_majoraxis:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_majoraxis:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_majoraxis_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_majoraxis = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_majoraxis",
                    disabled=(role == "viewer")
                )
            if mk_zip_majoraxis:
                zip_data_majoraxis = make_zip_from_dict(datasets_majoraxis, fig_majoraxis, fig_majoraxis_fname)
                st.session_state["zip_majoraxis"] = zip_data_majoraxis
                st.session_state["zip_majoraxis_ready"] = True
            with col2:
                if st.session_state.get("zip_majoraxis_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_majoraxis,
                        file_name=zip_majoraxis_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_minoraxis = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="minoraxis1"
                )
            with col_yaxis:
                mode_y_minoraxis = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="minoraxis2"
                )
            prefix = "log(minoraxis)" if mode_x_minoraxis == "log" else "minoraxis"
            key = f"{prefix}_{mode_y_minoraxis}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_minoraxis_fname = f"fig_{key}.png"
            zip_minoraxis_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за довжиною малої вісі еліпса'],
                    LANG_EN['Розподіл структур за довжиною малої вісі еліпса'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від довжини малої вісі еліпса'],
                    LANG_EN['Залежність густини структур від довжини малої вісі еліпса'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_minoraxis, ylable = titles[mode_y_minoraxis]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Довжина малої вісі еліпса (нм)']})"
                if mode_x_minoraxis == "log"
                else LANG['Довжина малої вісі еліпса (нм)']
            )
            gaus_minoraxis = dict_calculated_distributions["gauss_fit_ok"]
            logn_minoraxis = dict_calculated_distributions["ln_fit_ok"]
            datasets_minoraxis = dict_calculated_distributions["datasets"]
            mean_minoraxis = dict_calculated_distributions["mean"]
            if not gaus_minoraxis:
                st.session_state["show_gaus_minoraxis"] = False
            if not logn_minoraxis:
                st.session_state["show_logn_minoraxis"] = False
            with col_approx:
                show_mean_minoraxis = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_minoraxis"
                )
                show_gaus_minoraxis = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_minoraxis",
                    disabled=(not gaus_minoraxis)
                )
                show_logn_minoraxis = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_minoraxis",
                    disabled=(not logn_minoraxis)
                )
            fig_minoraxis = make_distribution_figs_and_data(dict_calculated_distributions,
                                                            nbins, 'green', xlable, ylable, LANG['Дані'],
                                                            show_gaus_minoraxis, show_logn_minoraxis,
                                                                show_mean_minoraxis, mean_minoraxis,
                                                                text_in_fig)
            st.pyplot(fig_minoraxis)
            if not gaus_minoraxis:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_minoraxis:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_minoraxis_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_minoraxis = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_minoraxis",
                    disabled=(role == "viewer")
                )
            if mk_zip_minoraxis:
                zip_data_minoraxis = make_zip_from_dict(datasets_minoraxis, fig_minoraxis, fig_minoraxis_fname)
                st.session_state["zip_minoraxis"] = zip_data_minoraxis
                st.session_state["zip_minoraxis_ready"] = True
            with col2:
                if st.session_state.get("zip_minoraxis_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_minoraxis,
                        file_name=zip_minoraxis_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_angle = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="angle1"
                )
            with col_yaxis:
                mode_y_angle = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="angle2"
                )
            prefix = "log(angle)" if mode_x_angle == "log" else "angle"
            key = f"{prefix}_{mode_y_angle}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_angle_fname = f"fig_{key}.png"
            zip_angle_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл структур за кутом повороту еліпса'],
                    LANG_EN['Розподіл структур за кутом повороту еліпса'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від кута повороту еліпса'],
                    LANG_EN['Залежність густини структур від кута повороту еліпса'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_angle, ylable = titles[mode_y_angle]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Кут повороту еліпса (°)']})"
                if mode_x_angle == "log"
                else LANG['Кут повороту еліпса (°)']
            )
            gaus_angle = dict_calculated_distributions["gauss_fit_ok"]
            logn_angle = dict_calculated_distributions["ln_fit_ok"]
            datasets_angle = dict_calculated_distributions["datasets"]
            mean_angle = dict_calculated_distributions["mean"]
            if not gaus_angle:
                st.session_state["show_gaus_angle"] = False
            if not logn_angle:
                st.session_state["show_logn_angle"] = False
            with col_approx:
                show_mean_angle = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_angle"
                )
                show_gaus_angle = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_angle",
                    disabled=(not gaus_angle)
                )
                show_logn_angle = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_angle",
                    disabled=(not logn_angle)
                )
            fig_angle = make_distribution_figs_and_data(dict_calculated_distributions,
                                                            nbins, 'green', xlable, ylable, LANG['Дані'],
                                                            show_gaus_angle, show_logn_angle,
                                                                show_mean_angle, mean_angle,
                                                                text_in_fig)
            st.pyplot(fig_angle)
            if not gaus_angle:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_angle:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_angle_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_angle = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_angle",
                    disabled=(role == "viewer")
                )
            if mk_zip_angle:
                zip_data_angle = make_zip_from_dict(datasets_angle, fig_angle, fig_angle_fname)
                st.session_state["zip_angle"] = zip_data_angle
                st.session_state["zip_angle_ready"] = True
            with col2:
                if st.session_state.get("zip_angle_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_angle,
                        file_name=zip_angle_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )
        # 2. Розподіл відстаней між структурами
        with tabs[2]:
            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_distances_centers = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="distances_centers1"
                )
            with col_yaxis:
                mode_y_distances_centers = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="distances_centers2",
                    index = 0,  # "none"
                    disabled = True
                )
            prefix = "log(distances_centers)" if mode_x_distances_centers == "log" else "distances_centers"
            key = f"{prefix}_{mode_y_distances_centers}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_distances_centers_fname = f"fig_{key}.png"
            zip_distances_centers_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл найближчих міжцентрових відстаней між структурами'],
                    LANG_EN['Розподіл найближчих міжцентрових відстаней між структурами'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від кута повороту еліпса'],
                    LANG_EN['Залежність густини структур від кута повороту еліпса'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_distances_centers, ylable = titles[mode_y_distances_centers]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Найближча міжцентрова відстань (нм)']})"
                if mode_x_distances_centers == "log"
                else LANG['Найближча міжцентрова відстань (нм)']
            )
            gaus_distances_centers = dict_calculated_distributions["gauss_fit_ok"]
            logn_distances_centers = dict_calculated_distributions["ln_fit_ok"]
            datasets_distances_centers = dict_calculated_distributions["datasets"]
            mean_distances_centers = dict_calculated_distributions["mean"]
            if not gaus_distances_centers:
                st.session_state["show_gaus_distances_centers"] = False
            if not logn_distances_centers:
                st.session_state["show_logn_distances_centers"] = False
            with col_approx:
                show_mean_distances_centers = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_distances_centers"
                )
                show_gaus_distances_centers = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_distances_centers",
                    disabled=(not gaus_distances_centers)
                )
                show_logn_distances_centers = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_distances_centers",
                    disabled=(not logn_distances_centers)
                )
            R_value = st.session_state.centroids_stat.loc[
                st.session_state.centroids_stat["Param"] == "R-Index center", "Value"].values[0]
            fig_label = f"{LANG['Дані: Індекс Кларка-Еванса']} (R={R_value:.2f})"
            fig_distances_centers = make_distribution_figs_and_data(dict_calculated_distributions,
                                                        nbins, 'teal', xlable, ylable, fig_label,
                                                        show_gaus_distances_centers, show_logn_distances_centers,
                                                                show_mean_distances_centers, mean_distances_centers,
                                                                text_in_fig)
            st.pyplot(fig_distances_centers)
            if not gaus_distances_centers:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_distances_centers:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_distances_centers_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_distances_centers = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_distances_centers",
                    disabled=(role == "viewer")
                )
            if mk_zip_distances_centers:
                zip_data_distances_centers = make_zip_from_dict(datasets_distances_centers, fig_distances_centers, fig_distances_centers_fname)
                st.session_state["zip_distances_centers"] = zip_data_distances_centers
                st.session_state["zip_distances_centers_ready"] = True
            with col2:
                if st.session_state.get("zip_distances_centers_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_distances_centers,
                        file_name=zip_distances_centers_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

            st.divider()

            col_xaxis, col_yaxis, col_approx = st.columns(3)
            with col_xaxis:
                mode_x_distances_edge2edge = st.radio(
                    f"{LANG['Формат розмірів']}",
                    list(option_for_xaxis.keys()),
                    format_func=lambda x: option_for_xaxis[x],
                    key="distances_edge2edge1"
                )
            with col_yaxis:
                mode_y_distances_edge2edge = st.radio(
                    f"{LANG['Тип гістограми']}",
                    list(option_for_yaxis.keys()),
                    format_func=lambda x: option_for_yaxis[x],
                    key="distances_edge2edge2",
                    index = 0,  # "none"
                    disabled = True
                )
            prefix = "log(distances_edge2edge)" if mode_x_distances_edge2edge == "log" else "distances_edge2edge"
            key = f"{prefix}_{mode_y_distances_edge2edge}"
            dict_calculated_distributions = st.session_state.dict_calculated_distributions.get(key)
            fig_distances_edge2edge_fname = f"fig_{key}.png"
            zip_distances_edge2edge_fname = f"{key}_analysis.zip"
            titles = {
                "dist": (
                    LANG['Розподіл відстаней між межами структур'],
                    LANG_EN['Розподіл відстаней між межами структур'],
                    LANG['Частота зустрічання']
                ),
                "dens": (
                    LANG['Залежність густини структур від кута повороту еліпса'],
                    LANG_EN['Залежність густини структур від кута повороту еліпса'],
                    LANG['Густина структур (см⁻²)']
                )
            }
            title, caption_distances_edge2edge, ylable = titles[mode_y_distances_edge2edge]
            st.markdown(f"**{title}**")

            xlable = (
                f"log₁₀({LANG['Відстань між межами структур (нм)']})"
                if mode_x_distances_edge2edge == "log"
                else LANG['Відстань між межами структур (нм)']
            )
            gaus_distances_edge2edge = dict_calculated_distributions["gauss_fit_ok"]
            logn_distances_edge2edge = dict_calculated_distributions["ln_fit_ok"]
            datasets_distances_edge2edge = dict_calculated_distributions["datasets"]
            mean_distances_edge2edge = dict_calculated_distributions["mean"]
            if not gaus_distances_edge2edge:
                st.session_state["show_gaus_distances_edge2edge"] = False
            if not logn_distances_edge2edge:
                st.session_state["show_logn_distances_edge2edge"] = False
            with col_approx:
                show_mean_distances_edge2edge = st.checkbox(
                    LANG["Показати середнє значення"],
                    key="show_mean_distances_edge2edge"
                )
                show_gaus_distances_edge2edge = st.checkbox(
                    LANG["Показати Gaussian fit"],
                    key="show_gaus_distances_edge2edge",
                    disabled=(not gaus_distances_edge2edge)
                )
                show_logn_distances_edge2edge = st.checkbox(
                    LANG["Показати Log-Normal fit"],
                    key="show_logn_distances_edge2edge",
                    disabled=(not logn_distances_edge2edge)
                )
            R_value = st.session_state.centroids_stat.loc[
                st.session_state.centroids_stat["Param"] == "R-Index grains", "Value"].values[0]
            fig_label = f"{LANG['Дані: Індекс Кларка-Еванса']} (R={R_value:.2f})"
            fig_distances_edge2edge = make_distribution_figs_and_data(dict_calculated_distributions,
                                                        nbins, 'teal', xlable, ylable, fig_label,
                                                        show_gaus_distances_edge2edge, show_logn_distances_edge2edge,
                                                                show_mean_distances_edge2edge, mean_distances_edge2edge,
                                                                text_in_fig)
            st.pyplot(fig_distances_edge2edge)
            if not gaus_distances_edge2edge:
                st.warning(LANG["Gaussian fit не зійшовся"])
            if not logn_distances_edge2edge:
                st.warning(LANG["Log-Normal fit не зійшовся"])

            st.session_state["zip_distances_edge2edge_ready"] = False
            col1, col2 = st.columns(2)
            with col1:
                mk_zip_distances_edge2edge = st.button(
                    f"📦 {LANG['Зробити ZIP архів з даними']}",
                    key="mk_zip_distances_edge2edge",
                    disabled=(role == "viewer")
                )
            if mk_zip_distances_edge2edge:
                zip_data_distances_edge2edge = make_zip_from_dict(datasets_distances_edge2edge, fig_distances_edge2edge, fig_distances_edge2edge_fname)
                st.session_state["zip_distances_edge2edge"] = zip_data_distances_edge2edge
                st.session_state["zip_distances_edge2edge_ready"] = True
            with col2:
                if st.session_state.get("zip_distances_edge2edge_ready", False):
                    st.download_button(
                        label=f"💾 {LANG['Завантажити всі дані у ZIP файл']}",
                        data=zip_data_distances_edge2edge,
                        file_name=zip_distances_edge2edge_fname,
                        mime="application/zip",
                        disabled=(role == "viewer")
                    )

        # 3. CLUSTERING
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
                st.session_state.clustering = plot_data

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

                if st.session_state.lang != "EN":
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

                st.markdown(f"**{LANG['Зв’язки між розміром структур, коефіцієнтом округлості та кутом нахилу еліпса']}**")

                fig_pairplot.fig.text(s=text_in_fig, **watermark_style)
                st.pyplot(fig_pairplot.fig)

                buf_p = io.BytesIO()
                fig_pairplot.savefig(buf_p, format="png", dpi=300, bbox_inches='tight')
                buf_p.seek(0)
                st.download_button(
                    label=f"💾 {LANG['Завантажити Pairplot']}",
                    data=buf_p,
                    file_name="fig_pairplot.png",
                    mime="image/png",
                    disabled=(role == "viewer")
                )


                st.markdown(f"**{LANG['Розподіл даних у різних групах']}**")
                fig_violinplot, ax_v = plt.subplots(figsize=(10, 5))
                if st.session_state.lang != "EN":
                    ua_to_key = {v: k for k, v in labels_ua.items() if k in plot_data["vars"]}
                    selected_ua = st.selectbox(LANG["Параметр"], list(ua_to_key.keys()))
                    param = ua_to_key[selected_ua]
                    ax_v.set_ylabel(labels_ua[param])
                else:
                    en_to_key = {v: k for k, v in labels_en.items() if k in plot_data["vars"]}
                    selected_en = st.selectbox(LANG["Параметр"], list(en_to_key.keys()))
                    param = en_to_key[selected_en]
                    ax_v.set_ylabel(labels_en[param])

                sns.violinplot(
                    data=plot_data["df"],
                    x='Label',
                    y=param,
                    ax=ax_v,
                    palette='Set2',
                    order=plot_data["order"]
                )

                if st.session_state.lang != "EN":
                    ax_v.set_xticklabels([size_ua[k] for k in plot_data["order"]])
                ax_v.set_xlabel(LANG["Кластери структур за розмірами"])
                fig_violinplot.text(s=text_in_fig, **watermark_style)
                st.pyplot(fig_violinplot)
                buf_v = io.BytesIO()
                fig_violinplot.savefig(buf_v, format="png", dpi=300, bbox_inches='tight')
                buf_v.seek(0)
                file_name_v = f"fig_violinplot_{param}.png"
                st.download_button(
                    label=f"💾 {LANG['Завантажити Violinplot']}",
                    data=buf_v,
                    file_name=file_name_v,
                    mime="image/png",
                    disabled=(role == "viewer")
                )

        # REPORT
        with tabs[4]:
            image_name = st.session_state.original_image_file_name
            st.markdown(f"**{LANG['Формування звіту за результатами аналізу зображення']} ({image_name})**")
            col1d, col2d = st.columns(2)
            with col1d:
                gen_rep = st.button(
                    f"▶️ {LANG['Згенерувати PDF звіту']}",
                    #disabled=(role == "viewer")
                )
            if gen_rep:
                if st.session_state.roughness is not None:
                    df_roughness = st.session_state.table_roughness
                    df_roughness = (df_roughness.rename(columns={"Param": LANG_EN["Параметр"], "Value": LANG_EN["Значення"]}))
                    cols_names = roughness_en
                    df_roughness[LANG_EN["Параметр"]] = df_roughness[LANG_EN["Параметр"]].map(cols_names)

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

                tables_dict_without_index = {
                    "Surface roughness parameters": df_roughness
                }
                tables_dict_with_index = {
                    st.session_state.table_caption_EN: df_statistics
                }

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

                figs_dict_heights = {LANG_EN['Розподіл висот']: fig_heights}

                if st.session_state.res_sens is not None:
                    figs_dict_num_size = {LANG_EN['Залежність кількості структур та середнього розміру від порогу висоти поверхні']: fig_num_size}
                else:
                    figs_dict_num_size = None

                if st.session_state.clustering is not None:
                    figs_dict_clustering_pairplot = {LANG_EN['Зв’язки між розміром структур, коефіцієнтом округлості та кутом нахилу еліпса']: fig_pairplot.fig}
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
                    figs_dict_filtered_image = {f"{LANG_EN['Відфільтроване зображення']}: {len(df)} {LANG_EN['структур ідентифіковано']}": pdf.image_to_figure(img, text_in_fig, watermark_style_picture)}
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
