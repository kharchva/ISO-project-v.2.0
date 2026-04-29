import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# def image_to_figure(img):
#     fig, ax = plt.subplots()
#     ax.imshow(img)
#     ax.axis("off")
#     return fig

def image_to_figure(img, text_in_fig, watermark_style):
    h, w = img.shape[:2]
    dpi = 300
    fig, ax = plt.subplots(figsize=(w/dpi, h/dpi), dpi=dpi)
    # fig, ax = plt.subplots(figsize=(w/100, h/100), dpi=dpi)
    ax.imshow(img)
    ax.axis("off")
    angle = np.degrees(np.arctan2(h, w))
    style = dict(
        x=0.5,
        y=0.5,
        fontsize=min(w, h) / 40,
        color="gray",
        alpha=0.7,
        ha="center",
        va="center",
        rotation=angle
    )
    style["s"] = text_in_fig
    fig.text(**style)
    # fig.text(s=text_in_fig, **watermark_style)
    return fig


from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Image, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import PageBreak


def input_figure(caption, fig, size):
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, dpi=300, bbox_inches="tight")
    img_buffer.seek(0)
    w, h = fig.get_size_inches()
    aspect = h / w
    pdf_width = size * cm
    pdf_height = pdf_width * aspect
    img = Image(img_buffer)
    img.drawWidth = pdf_width
    img.drawHeight = pdf_height
    img.hAlign = "CENTER"
    return img

def generate_pdf_report(filename,width,height,conditions1,conditions2,dots_holes,
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
    figs_dict_clustering_violinplot):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []
    fig_counter = 1
    table_counter = 1
    sec_counter = 1

    # title = "Image Analysis Report: " + filename
    title = "Image Analysis Report"
    elements.append(Paragraph(title, styles["Title"]))
    # elements.append(Paragraph("Image Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 25))
    elements.append(
        Paragraph(f"<b>{sec_counter}. Structure of input data</b>", styles["Heading1"])
    )
    elements.append(Spacer(1, 25))


    #####################################################################################
    caption_img, fig = next(iter(figs_dict_original_image.items()))
    img = input_figure(caption_img, fig, 8)
    # table
    caption_tbl, df = next(iter(tables_dict_without_index.items()))
    data = [df.columns.tolist()] + df.round(2).values.tolist()
    tbl = Table(data)
    tbl.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )
    # captions
    fig_caption = Paragraph(f"<b>{caption_img}</b>", styles["Normal"])
    tbl_caption = Paragraph(f"<b>Table {table_counter}. {caption_tbl}</b>", styles["Normal"])
    # layout table filename,width,height
    layout = Table(
        [
            [Paragraph(f"<b>Image file</b>", styles["Normal"]), Paragraph(f"<b>Width = {width} (nm)</b>", styles["Normal"])],
            [Paragraph(f"<b>{filename}</b>", styles["Normal"]), Paragraph(f"<b>Height = {height} (nm)</b>", styles["Normal"])],
            [img, tbl],
            [fig_caption, tbl_caption]
        ],
        colWidths=[8 * cm, 9 * cm]
    )
    layout.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP")
        ])
    )
    elements.append(layout)
    table_counter += 1
    elements.append(Spacer(1, 25))
    #####################################################################################

    # # input image
    # caption, fig = next(iter(figs_dict_original_image.items()))
    # img = input_figure(caption, fig, 10)
    # elements.append(img)
    # elements.append(Spacer(1, 6))
    # elements.append(Paragraph(f"<b>{caption}</b>", styles["Normal"]))
    #
    # #  Table Roughness
    # caption, df = next(iter(tables_dict_without_index.items()))
    # elements.append(Spacer(1, 10))
    # data = [df.columns.tolist()] + df.round(2).values.tolist()
    # table = Table(data, hAlign="CENTER")
    # table.setStyle(
    #     TableStyle([
    #         ("GRID", (0, 0), (-1, -1), 1, colors.black),
    #         ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    #         ("ALIGN", (0, 0), (-1, -1), "CENTER")
    #     ])
    # )
    # elements.append(table)
    # elements.append(Spacer(1, 6))
    # elements.append(
    #     Paragraph(f"<b>Table {table_counter}. {caption}</b>", styles["Normal"])
    # )
    # elements.append(Spacer(1, 25))


    # heights distribution
    caption, fig = next(iter(figs_dict_heights.items()))
    img = input_figure(caption, fig, 14)
    elements.append(img)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(f"<b>Figure {fig_counter}. {caption}</b>", styles["Normal"]))
    elements.append(Spacer(1, 25))
    fig_counter += 1

    if figs_dict_num_size is not None:
        sec_counter += 1
        elements.append(PageBreak())
        elements.append(
            Paragraph(f"<b>{sec_counter}. Height-dependent analysis of the number and size of structures {dots_holes}</b>", styles["Heading1"])
        )
        elements.append(Spacer(1, 25))

        elements.append(Paragraph(f"<b>Limitations:</b>", styles["Normal"]))
        if conditions1[0]:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"Minimal diameter : {conditions1[1]} nm", styles["Normal"]))

        if conditions1[2]:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"Maximal diameter : {conditions1[3]} nm", styles["Normal"]))

        if conditions1[4] == "periodic_conditions":
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Periodic boundary conditions", styles["Normal"]))
        elif conditions1[4] == "exclude_border":
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Excluded structures at borders", styles["Normal"]))
        else:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Boundaries remain as in the original", styles["Normal"]))

        elements.append(Spacer(1, 25))
        # Number and size
        caption, fig = next(iter(figs_dict_num_size.items()))
        img = input_figure(caption, fig, 14)
        elements.append(img)
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(f"<b>Figure {fig_counter}. {caption}</b>", styles["Normal"]))
        elements.append(Spacer(1, 25))
        fig_counter += 1

    elements.append(PageBreak())
    sec_counter += 1
    elements.append(
        Paragraph(f"<b>{sec_counter}. Segmentation, Filtering & Analysis of {dots_holes}</b>", styles["Heading1"])
    )
    elements.append(Spacer(1, 25))
    # segmented image
    caption, fig = next(iter(figs_dict_filtered_image.items()))
    img = input_figure(caption, fig, 10)

    elements.append(Paragraph(f"<b>Selected height:</b> {conditions2[5]} nm" , styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Limitations:</b>", styles["Normal"]))

    if conditions2[0]:
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"Minimal diameter : {conditions2[1]} nm", styles["Normal"]))

    if conditions2[2]:
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"Maximal diameter : {conditions2[3]} nm", styles["Normal"]))

    if conditions2[4] == "periodic_conditions":
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("Periodic boundary conditions", styles["Normal"]))
    elif conditions2[4] == "exclude_border":
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("Excluded structures at borders", styles["Normal"]))
    else:
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("Boundaries remain as in the original", styles["Normal"]))

    # layout = Table([[text_elements, img]], colWidths=[8 * cm, 9 * cm])
    # layout.setStyle(
    #     TableStyle([
    #         ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    #         ("VALIGN", (0, 0), (-1, -1), "TOP")
    #     ])
    # )
    # elements.append(layout)

    elements.append(Spacer(1, 10))
    elements.append(img)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(f"<b>{caption}</b>", styles["Normal"]))
    elements.append(Spacer(1, 25))
    # Table statistics
    caption, df = next(iter(tables_dict_with_index.items()))

    caption = caption.replace("₀", "0")

    df_pdf = df.copy()
    df_pdf.index = df_pdf.index.str.replace("₀", "0")
    df2 = df_pdf.reset_index()
    data = [df2.columns.tolist()] + df2.round(2).values.tolist()
    table = Table(data, hAlign="CENTER")
    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(
        Paragraph(f"<b>Table {table_counter}. {caption}</b>", styles["Normal"])
    )
    # elements.append(Spacer(1, 25))
    table_counter += 1

    elements.append(PageBreak())
    elements.append(
        Paragraph(f"<b>{sec_counter}.1. Size distributions</b>", styles["Heading3"])
    )
    for caption, fig in figs_dict_size.items():
        img = input_figure(caption, fig, 14)
        elements.append(img)
        elements.append(Spacer(1, 3))
        elements.append(
            Paragraph(f"<b>Figure {fig_counter}. {caption}</b>", styles["Normal"])
        )
        elements.append(Spacer(1, 25))
        fig_counter += 1

    elements.append(PageBreak())
    elements.append(
        Paragraph(f"<b>{sec_counter}.2. Geometry of structures</b>", styles["Heading3"])
    )
    for caption, fig in figs_dict_geometry.items():
        img = input_figure(caption, fig, 14)
        elements.append(img)
        elements.append(Spacer(1, 3))
        elements.append(
            Paragraph(f"<b>Figure {fig_counter}. {caption}</b>", styles["Normal"])
        )
        elements.append(Spacer(1, 25))
        fig_counter += 1

    elements.append(PageBreak())
    elements.append(
        Paragraph(f"<b>{sec_counter}.3. Distribution of distances</b>", styles["Heading3"])
    )
    for caption, fig in figs_dict_distances.items():
        img = input_figure(caption, fig, 14)
        elements.append(img)
        elements.append(Spacer(1, 3))
        elements.append(
            Paragraph(f"<b>Figure {fig_counter}. {caption}</b>", styles["Normal"])
        )
        elements.append(Spacer(1, 25))
        fig_counter += 1

    if figs_dict_clustering_pairplot is not None:
        sec_counter += 1
        elements.append(PageBreak())
        elements.append(
            Paragraph(f"<b>{sec_counter}. Clustering</b>", styles["Heading1"])
        )
        elements.append(Spacer(1, 25))
        caption, fig = next(iter(figs_dict_clustering_pairplot.items()))
        elements.append(
            Paragraph(f"<b>{sec_counter}.1. {caption}</b>", styles["Heading3"])
        )
        elements.append(Spacer(1, 25))
        img = input_figure(caption, fig, 17)
        elements.append(img)
        elements.append(Spacer(1, 25))
        elements.append(PageBreak())
        elements.append(
            Paragraph(f"<b>{sec_counter}.2. Violin plots showing distributions of morphological parameters</b>", styles["Heading3"])
        )
        # elements.append(Spacer(1, 25))
        for caption, fig in figs_dict_clustering_violinplot.items():
            img = input_figure(caption, fig, 14)
            elements.append(img)
            elements.append(Spacer(1, 6))
            elements.append(
                Paragraph(f"<b>Figure {fig_counter}. {caption}</b>", styles["Normal"])
            )
            elements.append(Spacer(1, 25))
            fig_counter += 1

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf