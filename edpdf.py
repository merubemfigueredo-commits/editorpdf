"""Editor simples de PDF com texto usando Streamlit e PyMuPDF."""

from __future__ import annotations

import io
from typing import Any

import fitz
import streamlit as st
from PIL import Image


st.set_page_config(
    page_title="Escreva no PDF",
    page_icon="✍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Converte uma cor hexadecimal para a tupla RGB esperada pelo PyMuPDF."""
    value = hex_color.lstrip("#")
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4))  # type: ignore[return-value]


def apply_texts(page: fitz.Page, texts: list[dict[str, Any]]) -> None:
    """Aplica os textos cadastrados na página, sem alterar o PDF original em memória."""
    for item in texts:
        font_size = float(item["font_size"])
        page.insert_text(
            (float(item["x"]), float(item["y"]) + font_size),
            str(item["text"]),
            fontsize=font_size,
            fontname=str(item["font"]),
            color=hex_to_rgb(str(item["color"])),
            overlay=True,
        )


def render_page(
    pdf_bytes: bytes,
    page_number: int,
    texts: list[dict[str, Any]],
    scale: float = 1.35,
) -> Image.Image:
    """Renderiza a página com as edições atuais para a pré-visualização."""
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = document[page_number]
    apply_texts(page, [item for item in texts if item["page"] == page_number])
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    document.close()
    return image


def build_output(pdf_bytes: bytes, texts: list[dict[str, Any]]) -> bytes:
    """Gera o PDF final com todas as inserções."""
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_number in range(len(document)):
        apply_texts(
            document[page_number],
            [item for item in texts if item["page"] == page_number],
        )

    output = io.BytesIO()
    document.save(output, garbage=4, deflate=True)
    document.close()
    return output.getvalue()


def reset_for_new_file(file_signature: tuple[str, int]) -> None:
    if st.session_state.get("file_signature") != file_signature:
        st.session_state.file_signature = file_signature
        st.session_state.texts = []


if "texts" not in st.session_state:
    st.session_state.texts = []


st.title("Escreva no PDF")
st.write(
    "Adicione textos sobre qualquer página do seu PDF e baixe uma nova cópia "
    "com as edições aplicadas."
)

uploaded_file = st.file_uploader(
    "Escolha um arquivo PDF",
    type=["pdf"],
    help="O arquivo é processado localmente nesta sessão.",
)

if uploaded_file is None:
    st.info("Envie um PDF para começar.")
    left, right = st.columns(2)
    with left:
        st.subheader("Como usar")
        st.markdown(
            "1. Envie um arquivo PDF.\n"
            "2. Escolha a página e informe o texto.\n"
            "3. Ajuste posição, fonte e cor.\n"
            "4. Clique em **Adicionar texto**.\n"
            "5. Baixe o PDF editado."
        )
    with right:
        st.subheader("O que você pode fazer")
        st.markdown(
            "- Adicionar vários textos em páginas diferentes\n"
            "- Escrever textos com mais de uma linha\n"
            "- Escolher entre fontes básicas, tamanho e cor\n"
            "- Remover uma inserção antes de baixar\n"
            "- Trabalhar com PDFs de várias páginas"
        )
    st.caption("Formatos aceitos: PDF. As posições são medidas em pontos (pt).")
    st.stop()


pdf_bytes = uploaded_file.getvalue()
file_signature = (uploaded_file.name, len(pdf_bytes))
reset_for_new_file(file_signature)

try:
    source_document = fitz.open(stream=pdf_bytes, filetype="pdf")
except (fitz.FileDataError, RuntimeError):
    st.error("Não foi possível abrir este arquivo. Confira se ele é um PDF válido.")
    st.stop()

page_count = len(source_document)
page_sizes = [
    (float(page.rect.width), float(page.rect.height)) for page in source_document
]
source_document.close()

with st.sidebar:
    st.header("Inserir texto")
    page_number = st.selectbox(
        "Página",
        options=list(range(page_count)),
        format_func=lambda page: f"Página {page + 1}",
    )
    page_width, page_height = page_sizes[page_number]
    st.caption(f"Tamanho da página: {page_width:.1f} × {page_height:.1f} pt")

    text = st.text_area(
        "Texto",
        placeholder="Digite o que deseja escrever no PDF",
        height=110,
    )
    col_x, col_y = st.columns(2)
    with col_x:
        x_position = st.number_input(
            "X (pt)",
            min_value=0.0,
            max_value=max(0.0, page_width - 1),
            value=min(72.0, max(0.0, page_width - 1)),
            step=1.0,
            help="Distância a partir da borda esquerda.",
        )
    with col_y:
        y_position = st.number_input(
            "Y (pt)",
            min_value=0.0,
            max_value=max(0.0, page_height - 1),
            value=min(72.0, max(0.0, page_height - 1)),
            step=1.0,
            help="Distância a partir do topo.",
        )

    font_name = st.selectbox(
        "Fonte",
        options=["helv", "hebo", "tiro", "cour"],
        format_func={
            "helv": "Helvetica",
            "hebo": "Helvetica negrito",
            "tiro": "Times",
            "cour": "Courier",
        }.get,
    )
    font_size = st.slider("Tamanho", min_value=6, max_value=96, value=14)
    color = st.color_picker("Cor do texto", "#172033")

    if st.button("Adicionar texto", type="primary", use_container_width=True):
        if not text.strip():
            st.warning("Digite algum texto antes de adicionar.")
        else:
            st.session_state.texts.append(
                {
                    "page": page_number,
                    "text": text,
                    "x": x_position,
                    "y": y_position,
                    "font": font_name,
                    "font_size": font_size,
                    "color": color,
                }
            )
            st.success("Texto adicionado.")
            st.rerun()

    st.divider()
    st.caption(
        "Dica: use a prévia e ajuste X/Y. A origem (0, 0) fica no canto superior "
        "esquerdo da página."
    )

st.subheader(f"Prévia — Página {page_number + 1} de {page_count}")
preview = render_page(pdf_bytes, page_number, st.session_state.texts)
st.image(preview, use_container_width=True)

page_texts = [
    (index, item)
    for index, item in enumerate(st.session_state.texts)
    if item["page"] == page_number
]

if page_texts:
    st.subheader("Textos nesta página")
    for index, item in page_texts:
        row_left, row_middle, row_right = st.columns([6, 2, 1])
        with row_left:
            preview_text = str(item["text"]).replace("\n", " · ")
            st.write(f"**{preview_text}**")
            st.caption(
                f"Posição: ({float(item['x']):.0f}, {float(item['y']):.0f}) pt · "
                f"{item['font_size']} pt · {item['font']}"
            )
        with row_middle:
            st.color_picker(
                "Cor",
                value=str(item["color"]),
                key=f"color_preview_{index}",
                disabled=True,
                label_visibility="collapsed",
            )
        with row_right:
            if st.button("Remover", key=f"remove_{index}"):
                st.session_state.texts.pop(index)
                st.rerun()
else:
    st.caption("Nenhum texto foi adicionado a esta página ainda.")

st.divider()
total_texts = len(st.session_state.texts)
if total_texts:
    st.subheader("Exportar PDF")
    st.write(
        f"{total_texts} texto(s) pronto(s) para exportação em "
        f"{len({item['page'] for item in st.session_state.texts})} página(s)."
    )
    try:
        edited_pdf = build_output(pdf_bytes, st.session_state.texts)
        output_name = f"{uploaded_file.name.rsplit('.', 1)[0]}-editado.pdf"
        st.download_button(
            "Baixar PDF editado",
            data=edited_pdf,
            file_name=output_name,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    except (fitz.FileDataError, RuntimeError) as error:
        st.error(f"Não foi possível gerar o PDF editado: {error}")
else:
    st.info("Adicione pelo menos um texto para liberar o download.")
