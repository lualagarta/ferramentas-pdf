import streamlit as st
import io
import os
import zipfile
import re
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
    if hasattr(img_bytes, 'seek'):
        img_bytes.seek(0)
    img = Image.open(img_bytes)
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    img_redim = redimensionar_proporcional(img, largura_alvo)
    pdf_io = io.BytesIO()
    img_redim.save(pdf_io, format="PDF", resolution=100.0)
    pdf_io.seek(0)
    return pdf_io

def carregar_imagem_padrao(img_bytes, largura_alvo):
    if hasattr(img_bytes, 'seek'):
        img_bytes.seek(0)
    img = Image.open(img_bytes)
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    return redimensionar_proporcional(img, largura_alvo)

def ordenar_inteligentemente_tuplas(data):
    """Ordena tuplas (nome_arquivo, bytes) ex: img_2 antes de img_10"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key[0])]
    return sorted(data, key=alphanum_key)

def ordenar_inteligentemente_arquivos(arquivos):
    """Ordena arquivos do st.file_uploader ex: img_2 antes de img_10"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key.name)]
    return sorted(arquivos, key=alphanum_key)


# --- MENU LATERAL ---
st.sidebar.title("🛠️ Ferramentas PDF")
opcao = st.sidebar.radio(
    "Escolha uma ação:",
    [
        "1. Criar PDF(s) de Imagens", 
        "2. Inserir Página", 
        "3. Substituir Página", 
        "4. Extrair Imagens",
        "5. Empacotar em ZIP (Celular)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("App criado para processar PDFs e Imagens de forma fácil, mantendo alta qualidade (Lanczos).")


# ==========================================
# OPÇÃO 1: CRIAR PDF DE IMAGENS
# ==========================================
if opcao == "1. Criar PDF(s) de Imagens":
    st.title("📚 Criar PDF a partir de Imagens")
    st.write("Junte imagens para formar PDFs. Escolha usar um arquivo ZIP (várias pastas) ou arquivos avulsos.")

    largura_alvo = st.number_input("Largura Alvo (px)", value=LARGURA_PADRAO_DEFAULT)
    
    st.subheader("Opcionais (Padrões)")
    col1, col2 = st.columns(2)
    with col1:
        img_inicio = st.file_uploader("Imagem Inicial (Capa/Aviso)", type=["png", "jpg", "jpeg", "webp"], key="ini")
    with col2:
        img_fim = st.file_uploader("Imagem Final (Fim/Créditos)", type=["png", "jpg", "jpeg", "webp"], key="fim")

    st.markdown("---")
    st.markdown("### Escolha o método de envio:")
    
    aba_zip, aba_avulsas = st.tabs(["📂 Modo ZIP (Lote de Pastas)", "🖼️ Modo Avulso (Várias Imagens)"])
    
    # --- ABA 1: MODO ZIP ---
    with aba_zip:
        st.info("Envie um arquivo .ZIP contendo pastas. (Dica: Se estiver no celular, use a Ferramenta 5 para criar seu ZIP primeiro!).")
        arquivo_zip = st.file_uploader("Envie o arquivo .ZIP com as pastas", type=["zip"])
        
        if st.button("Gerar PDFs em Lote") and arquivo_zip:
            try:
                with st.spinner("Extraindo imagens e gerando PDFs..."):
                    pastas_dict = {}
                    
                    with zipfile.ZipFile(arquivo_zip, 'r') as z:
                        for file_info in z.infolist():
                            if file_info.is_dir() or "__MACOSX" in file_info.filename:
                                continue
                            
                            parts = file_info.filename.split('/')
                            if len(parts) >= 2:
                                pasta_nome = parts[-2]
                                arquivo_nome = parts[-1]
                            else:
                                pasta_nome = "Raiz"
                                arquivo_nome = parts[0]
                            
                            _, ext = os.path.splitext(arquivo_nome.lower())
                            if ext in EXTENSOES_IMAGEM:
                                if pasta_nome not in pastas_dict:
                                    pastas_dict[pasta_nome] = []
                                pastas_dict[pasta_nome].append((arquivo_nome, z.read(file_info.filename)))
                    
                    if not pastas_dict:
                        st.error("Nenhuma imagem suportada foi encontrada dentro deste ZIP.")
                    else:
                        zip_saida_io = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_saida_io, 'w') as zip_saida:
                            for pasta, lista_arquivos in pastas_dict.items():
                                lista_ordenada = ordenar_inteligentemente_tuplas(lista_arquivos)
                                lista_imagens_pdf = []
                                
                                if img_inicio:
                                    lista_imagens_pdf.append(carregar_imagem_padrao(img_inicio, largura_alvo))
                                
                                for nome_arq, dados_img in lista_ordenada:
                                    try:
                                        img_bytes_io = io.BytesIO(dados_img)
                                        img = Image.open(img_bytes_io)
                                        if img.mode in ('RGBA', 'P', 'LA'):
                                            img = img.convert('RGB')
                                        lista_imagens_pdf.append(redimensionar_proporcional(img, largura_alvo))
                                    except Exception as e:
                                        st.warning(f"Erro na imagem {nome_arq}: {e}")
                                
                                if img_fim:
                                    lista_imagens_pdf.append(carregar_imagem_padrao(img_fim, largura_alvo))
                                
                                if lista_imagens_pdf:
                                    pdf_io = io.BytesIO()
                                    primeira_img = lista_imagens_pdf[0]
                                    outras_imgs = lista_imagens_pdf[1:]
                                    
                                    primeira_img.save(
                                        pdf_io, "PDF", resolution=100.0, save_all=True,
                                        append_images=outras_imgs, optimize=True
                                    )
                                    zip_saida.writestr(f"{pasta}.pdf", pdf_io.getvalue())
                                    
                        zip_saida_io.seek(0)
                        st.success(f"✅ Lote finalizado! {len(pastas_dict)} PDFs gerados com sucesso.")
                        st.download_button("⬇️ Baixar todos os PDFs (ZIP)", data=zip_saida_io, file_name="pdfs_prontos.zip", mime="application/zip")
                        
            except Exception as e:
                st.error(f"Erro ao processar o lote: {e}")

    # --- ABA 2: MODO AVULSO ---
    with aba_avulsas:
        st.info("Selecione várias imagens avulsas para gerar **um único PDF**.")
        imagens_upload = st.file_uploader("Selecione todas as imagens", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
        
        if st.button("Gerar PDF Único") and imagens_upload:
            try:
                with st.spinner("Redimensionando e unindo imagens..."):
                    lista_imagens_pdf = []

                    if img_inicio:
                        lista_imagens_pdf.append(carregar_imagem_padrao(img_inicio, largura_alvo))

                    imagens_ordenadas = ordenar_inteligentemente_arquivos(imagens_upload)

                    for img_up in imagens_ordenadas:
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


# ==========================================
# OPÇÃO 2: INSERIR PÁGINA
# ==========================================
elif opcao == "2. Inserir Página":
    st.title("➕ Inserir Página em PDF")
    st.write("Adicione uma imagem ou página PDF no meio do seu arquivo.")

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
                posicao_efetiva = min(posicao - 1, total_paginas)

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
# OPÇÃO 3: SUBSTITUIR PÁGINA
# ==========================================
elif opcao == "3. Substituir Página":
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
# OPÇÃO 4: EXTRAIR IMAGENS
# ==========================================
elif opcao == "4. Extrair Imagens":
    st.title("📸 Extrair Imagens de PDF")
    st.write("Obtenha todas as imagens de dentro de um arquivo PDF.")

    pdf_origem = st.file_uploader("Envie o PDF", type=["pdf"])
    
    modo_download = st.radio(
        "Como você quer receber as imagens?",
        ["📦 Tudo junto em um arquivo ZIP", "🖼️ Imagens separadas (Baixar uma por uma)"]
    )

    if st.button("Extrair Imagens") and pdf_origem:
        try:
            with st.spinner("Lendo páginas e extraindo..."):
                reader = PdfReader(pdf_origem)
                imagens_extraidas = []
                
                # Extrai as imagens para a memória
                for i, pagina in enumerate(reader.pages):
                    for num_img, imagem_objeto in enumerate(pagina.images):
                        extensao = os.path.splitext(imagem_objeto.name)[1]
                        if not extensao: extensao = ".png"
                        nome_arquivo = f"pagina_{i + 1:03d}_img_{num_img + 1}{extensao}"
                        imagens_extraidas.append((nome_arquivo, imagem_objeto.data))
                
                total_imagens = len(imagens_extraidas)

            if total_imagens > 0:
                st.success(f"✅ Extração concluída! {total_imagens} imagens encontradas.")
                
                if "ZIP" in modo_download:
                    # Gera o ZIP
                    zip_io = io.BytesIO()
                    with zipfile.ZipFile(zip_io, "w") as zipf:
                        for nome, dados in imagens_extraidas:
                            zipf.writestr(nome, dados)
                    zip_io.seek(0)
                    st.download_button("⬇️ Baixar Imagens (ZIP)", data=zip_io, file_name="imagens_extraidas.zip", mime="application/zip")
                
                else:
                    # Exibe as imagens na tela com botões de download individuais
                    st.write("---")
                    for nome, dados in imagens_extraidas:
                        col_img, col_btn = st.columns([1, 2])
                        with col_img:
                            st.image(dados, width=150)
                        with col_btn:
                            st.write(f"**{nome}**")
                            st.download_button(f"⬇️ Baixar {nome}", data=dados, file_name=nome, mime="image/png", key=nome)
                        st.write("---")
            else:
                st.warning("⚠️ Nenhuma imagem encontrada neste PDF.")
        except Exception as e:
            st.error(f"Erro: {e}")


# ==========================================
# OPÇÃO 5: CRIAR ZIP (PARA CELULAR)
# ==========================================
elif opcao == "5. Empacotar em ZIP (Celular)":
    st.title("🗂️ Empacotar Imagens em ZIP")
    st.write("Criar arquivos ZIP no celular não é tão óbvio. Use esta ferramenta para juntar as imagens de um capítulo em um único arquivo ZIP.")
    
    nome_pasta = st.text_input("Nome do Capítulo/Pasta (ex: Capitulo_01)", value="Capitulo_01")
    arquivos = st.file_uploader("Selecione as imagens do capítulo", accept_multiple_files=True)
    
    if st.button("Gerar Arquivo ZIP") and arquivos:
        try:
            with st.spinner("Empacotando..."):
                zip_io = io.BytesIO()
                with zipfile.ZipFile(zip_io, "w") as zipf:
                    for arq in arquivos:
                        # Salva dentro da pasta com o nome informado
                        caminho_interno = f"{nome_pasta}/{arq.name}"
                        zipf.writestr(caminho_interno, arq.read())
                
                zip_io.seek(0)
                st.success("✅ Arquivo ZIP criado com sucesso!")
                st.download_button(
                    "⬇️ Baixar Meu Arquivo ZIP", 
                    data=zip_io, 
                    file_name=f"{nome_pasta}.zip", 
                    mime="application/zip"
                )
        except Exception as e:
            st.error(f"Erro ao criar ZIP: {e}")
