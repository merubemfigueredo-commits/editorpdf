# Editor de PDF com Streamlit

Aplicação em Python para inserir textos em páginas de PDFs, visualizar as alterações e baixar uma nova cópia editada.

## Run & Operate

- `streamlit run app.py --server.port 5000` — execute the editor
- `python main.py` — execute the editor through the compatibility entry point
- `pip install -r requirements.txt` — install Python dependencies

## Stack

- Python 3.13
- Streamlit
- PyMuPDF
- Pillow

## Onde ficam as coisas

- `app.py` — interface e processamento do editor
- `main.py` — ponto de entrada alternativo
- `requirements.txt` — dependências Python

## Decisões de arquitetura

- O arquivo original é mantido intacto em memória durante a sessão.
- As inserções são aplicadas sobre uma cópia somente quando a prévia é renderizada ou o download é gerado.
- As coordenadas usam pontos (pt), com origem no canto superior esquerdo, para facilitar o posicionamento visual.

## Produto

O usuário envia um PDF, escolhe uma página, escreve um ou mais textos, ajusta posição, fonte, tamanho e cor, visualiza o resultado e baixa o PDF editado.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

_Populate as you build — sharp edges, "always run X before Y" rules._

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
