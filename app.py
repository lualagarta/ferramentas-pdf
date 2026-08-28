import streamlit as st
import io
import os
import zipfile
from PIL import Image
from pypdf import PdfReader, PdfWriter

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PDF & Image Tools", page_icon="📄", layout="centered")

EXTENSOES_IMAGEM = ['.webp', '.jpg', '.jpeg', '.png']
LARGURA_PADRAO_DEFAULT = 1200

# --- FUNÇÕES AUXILIARES ---
def redimensionar_proporcional(img, largura_alvo):
    largura_original, altura_original = img.size
    proporcao = largura_alvo / float(largura_original)
    altura_alvo = int((float(altura_original) * float(proporcao)))
    return img.resize((largura_alvo, altura_alvo), Image.Resampling.LANCZOS)

def image_to_pdf_bytes(img_bytes, largura_alvo):
    img = Image.open(img_bytes)
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    img_redim = redimensionar_proporcional(img, largura_alvo)
    pdf_io = io.BytesIO()
    img_redim.save(pdf_io, format="PDF", resolution=100.0)
    pdf_io.seek(0)
    return pdf_io

def carregar_imagem_padrao(img_bytes, largura_alvo):
    img = Image.open(img_bytes)
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    return redimensionar_proporcional(img, largura_alvo)

# --- MENU LATERAL ---
st.sidebar.title("🛠️ Ferramentas PDF")
opcao = st.sidebar.radio(
    "Escolha uma ação:",
    ["1. Inserir Página", "2. Substituir Página", "3. Extrair Imagens", "4. Criar PDF de Imagens"]
)

st.sidebar.markdown("---")
st.sidebar.info("App criado para processar PDFs e Imagens de forma fácil, mantendo alta qualidade (Lanczos).")


# ==========================================
# OPÇÃO 1: INSERIR PÁGINA
# ==========================================
if opcao == "1. Inserir Página":
    st.title("➕ Inserir Página em PDF")
    st.write("Adicione uma imagem ou página PDF no meio do seu arquivo, padronizando a largura.")

    pdf_origem = st.file_uploader("1. Envie o PDF Original", type=["pdf"])
    item_novo = st.file_uploader("2. Envie a Nova Página (PDF ou Imagem)", type=["pdf", "png", "jpg", "jpeg", "webp"])
    
    col1, col2 = st.columns(2)
    with col1:
        largura_alvo = st.number_input("Largura Alvo (px)", value=LARGURA_PADRAO_DEFAULT)
    with col2:
        posicao = st.number_input("Posição para inserir (1 = Início)", min_value=1, value=1)

    if st.button("Processar e Inserir") and pdf_origem and item_novo:
        try:
            with st.spinner("Processando..."):
                ext = os.path.splitext(item_novo.name)[1].lower()
                
                # Prepara a nova página
                if ext in EXTENSOES_IMAGEM:
                    nova_pagina_io = image_to_pdf_bytes(item_novo, largura_alvo)
                else:
                    nova_pagina_io = item_novo

                reader_principal = PdfReader(pdf_origem)
                reader_nova = PdfReader(nova_pagina_io)
                writer = PdfWriter()

                pagina_nova = reader_nova.pages[0]
                if ext == '.pdf':
                    fator = largura_alvo / float(pagina_nova.mediabox.width)
                    pagina_nova.scale_by(fator)

                total_paginas = len(reader_principal.pages)
                posicao_efetiva = min(posicao - 1, total_paginas) # Ajusta para índice 0

                for i in range(total_paginas):
                    if i == posicao_efetiva:
                        writer.add_page(pagina_nova)
                    writer.add_page(reader_principal.pages[i])

                if posicao_efetiva == total_paginas:
                    writer.add_page(pagina_nova)

                out_io = io.BytesIO()
                writer.write(out_io)
                out_io.seek(0)

            st.success("✅ PDF gerado com sucesso!")
            st.download_button("⬇️ Baixar Novo PDF", data=out_io, file_name="pdf_inserido.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Erro: {e}")


# ==========================================
# OPÇÃO 2: SUBSTITUIR PÁGINA
# ==========================================
elif opcao == "2. Substituir Página":
    st.title("🔄 Substituir Página em PDF")
    st.write("Troque uma página existente por uma nova imagem ou PDF.")

    pdf_origem = st.file_uploader("1. Envie o PDF Original", type=["pdf"])
    item_novo = st.file_uploader("2. Envie a Página Substituta (PDF ou Imagem)", type=["pdf", "png", "jpg", "jpeg", "webp"])
    
    col1, col2 = st.columns(2)
    with col1:
        largura_alvo = st.number_input("Largura Alvo (px)", value=LARGURA_PADRAO_DEFAULT)
    with col2:
        posicao = st.number_input("Qual página substituir? (ex: 1 = primeira)", min_value=1, value=1)

    if st.button("Substituir Página") and pdf_origem and item_novo:
        try:
            with st.spinner("Processando..."):
                ext = os.path.splitext(item_novo.name)[1].lower()
                
                if ext in EXTENSOES_IMAGEM:
                    nova_pagina_io = image_to_pdf_bytes(item_novo, largura_alvo)
                else:
                    nova_pagina_io = item_novo

                reader_principal = PdfReader(pdf_origem)
                reader_nova = PdfReader(nova_pagina_io)
                writer = PdfWriter()

                pagina_nova = reader_nova.pages[0]
                if ext == '.pdf':
                    fator = largura_alvo / float(pagina_nova.mediabox.width)
                    pagina_nova.scale_by(fator)

                total_paginas = len(reader_principal.pages)
                posicao_efetiva = posicao - 1

                if posicao_efetiva >= total_paginas:
                    st.error(f"O PDF tem apenas {total_paginas} páginas.")
                else:
                    for i in range(total_paginas):
                        if i == posicao_efetiva:
                            writer.add_page(pagina_nova)
                        else:
                            writer.add_page(reader_principal.pages[i])

                    out_io = io.BytesIO()
                    writer.write(out_io)
                    out_io.seek(0)

                    st.success("✅ Página substituída com sucesso!")
                    st.download_button("⬇️ Baixar Novo PDF", data=out_io, file_name="pdf_substituido.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Erro: {e}")


# ==========================================
# OPÇÃO 3: EXTRAIR IMAGENS
# ==========================================
elif opcao == "3. Extrair Imagens":
    st.title("📸 Extrair Imagens de PDF")
    st.write("Obtenha todas as imagens de dentro de um arquivo PDF. Você baixará um arquivo ZIP com todas elas.")

    pdf_origem = st.file_uploader("Envie o PDF", type=["pdf"])

    if st.button("Extrair Imagens") and pdf_origem:
        try:
            with st.spinner("Lendo páginas e extraindo..."):
                reader = PdfReader(pdf_origem)
                zip_io = io.BytesIO()
                total_imagens = 0

                with zipfile.ZipFile(zip_io, "w") as zipf:
                    for i, pagina in enumerate(reader.pages):
                        for num_img, imagem_objeto in enumerate(pagina.images):
                            extensao = os.path.splitext(imagem_objeto.name)[1]
                            if not extensao: extensao = ".png"
                            nome_arquivo = f"pagina_{i + 1:03d}_img_{num_img + 1}{extensao}"
                            zipf.writestr(nome_arquivo, imagem_objeto.data)
                            total_imagens += 1
                
                zip_io.seek(0)

            if total_imagens > 0:
                st.success(f"✅ Extração concluída! {total_imagens} imagens encontradas.")
                st.download_button("⬇️ Baixar Imagens (ZIP)", data=zip_io, file_name="imagens_extraidas.zip", mime="application/zip")
            else:
                st.warning("⚠️ Nenhuma imagem encontrada neste PDF.")
        except Exception as e:
            st.error(f"Erro: {e}")


# ==========================================
# OPÇÃO 4: CRIAR PDF DE IMAGENS
# ==========================================
elif opcao == "4. Criar PDF de Imagens":
    st.title("📚 Criar PDF a partir de Imagens")
    st.write("Selecione várias imagens (capítulos/páginas) para uni-las em um único PDF de alta qualidade.")

    largura_alvo = st.number_input("Largura Alvo (px)", value=LARGURA_PADRAO_DEFAULT)
    
    st.subheader("Imagens Principais")
    imagens_upload = st.file_uploader("Selecione todas as imagens na ordem correta", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    
    st.subheader("Opcionais (Padrões)")
    col1, col2 = st.columns(2)
    with col1:
        img_inicio = st.file_uploader("Imagem Inicial (Capa/Aviso)", type=["png", "jpg", "jpeg", "webp"])
    with col2:
        img_fim = st.file_uploader("Imagem Final (Fim/Créditos)", type=["png", "jpg", "jpeg", "webp"])

    if st.button("Gerar PDF") and imagens_upload:
        try:
            with st.spinner("Redimensionando e unindo imagens..."):
                lista_imagens_pdf = []

                if img_inicio:
                    lista_imagens_pdf.append(carregar_imagem_padrao(img_inicio, largura_alvo))

                for img_up in imagens_upload:
                    lista_imagens_pdf.append(carregar_imagem_padrao(img_up, largura_alvo))

                if img_fim:
                    lista_imagens_pdf.append(carregar_imagem_padrao(img_fim, largura_alvo))

                if lista_imagens_pdf:
                    out_io = io.BytesIO()
                    primeira_img = lista_imagens_pdf[0]
                    outras_imgs = lista_imagens_pdf[1:]

                    primeira_img.save(
                        out_io, "PDF", resolution=100.0, save_all=True,
                        append_images=outras_imgs, optimize=True
                    )
                    out_io.seek(0)
                    
                    st.success("✅ PDF criado com sucesso!")
                    st.download_button("⬇️ Baixar Arquivo PDF", data=out_io, file_name="capitulo_unido.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")