import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import html
import re
import base64

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Configure a variavel GEMINI_API_KEY nos secrets do Streamlit ou nas variaveis de ambiente.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

GENERATION_CONFIG = {
    "temperature": 0.65,
    "top_p": 0.85,
    "top_k": 32,
    "max_output_tokens": 1536,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_ONLY_HIGH"},
]

PRIORIDADE_MODELOS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "models/gemini-1.0-pro",
    "models/gemini-pro",
]

st.set_page_config(
    page_title="Resumo Turbo",
    page_icon="🚀",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main-title {font-size:2.8rem;font-weight:700;margin-bottom:0.35rem;line-height:1.1;}
    .sub-title {font-size:1.1rem;color:#5f6368;margin-bottom:2.2rem;}
    .card {background:linear-gradient(135deg,#ffffff 0%,#f8faff 100%);border:1px solid rgba(99,102,241,0.15);border-radius:18px;padding:28px;margin-bottom:22px;box-shadow:0 28px 46px -32px rgba(79,70,229,0.45);}
    .card-title {display:flex;align-items:center;gap:14px;font-weight:700;font-size:1.35rem;color:#1f2937;}
    .card-title span {display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:14px;background:rgba(99,102,241,0.08);font-size:1.5rem;}
    .card-content {margin-top:18px;background:white;border-radius:14px;padding:20px 22px;border:1px solid rgba(15,23,42,0.06);font-size:1rem;line-height:1.65;font-family:'Inter', sans-serif;}
    .card-content pre {background:rgba(242,244,255,0.9);padding:16px;border-radius:12px;overflow:auto;font-size:0.95rem;}
    .download-link {display:inline-flex;align-items:center;gap:8px;margin-top:16px;text-decoration:none;background:linear-gradient(135deg,#eef2ff,#e0e7ff);border:1px solid rgba(99,102,241,0.25);color:#312e81;font-weight:600;padding:0.55rem 1.15rem;border-radius:12px;transition:all 0.2s ease;}
    .download-link:hover {background:linear-gradient(135deg,#dce4ff,#c7d2fe);color:#1d1a65;}
    .stSpinner > div {font-size:1.05rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

def extrair_texto_pdf(arquivo_pdf):
    texto = ""
    leitor = PdfReader(arquivo_pdf)
    for pagina in leitor.pages:
        texto += pagina.extract_text()
    return texto

def gerar_com_gemini(prompt, texto):
    prompt_completo = f"{prompt}\n\nTexto:\n{texto}"
    erros = []
    for modelo_nome in PRIORIDADE_MODELOS:
        try:
            modelo = genai.GenerativeModel(
                model_name=modelo_nome,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS,
            )
            resposta = modelo.generate_content(prompt_completo)
            texto_extraido = extrair_texto_resposta(resposta)
            if texto_extraido:
                return texto_extraido
            motivo = obter_motivo_resposta(resposta)
            if motivo:
                erros.append(f"{modelo_nome}: {motivo}")
        except Exception as erro:
            erros.append(f"{modelo_nome}: {erro}")
    if erros:
        raise ValueError(" | ".join(erros))
    return None

def extrair_texto_resposta(resposta):
    if not resposta or not getattr(resposta, "candidates", None):
        return None
    for candidato in resposta.candidates:
        if getattr(candidato, "finish_reason", None) == "SAFETY":
            continue
        if getattr(candidato, "content", None):
            partes = []
            for parte in candidato.content.parts:
                texto = getattr(parte, "text", None)
                if texto:
                    partes.append(texto)
            if partes:
                return "\n".join(partes).strip()
    return None

def obter_motivo_resposta(resposta):
    if not resposta or not getattr(resposta, "candidates", None):
        return "Nenhum candidato retornado."
    motivos = []
    for candidato in resposta.candidates:
        motivo = getattr(candidato, "finish_reason", None)
        if motivo and motivo != "STOP":
            motivos.append(str(motivo))
    return ", ".join(motivos) if motivos else None

TEXTO_LIMITE = 12000
TRUNCATE_NOTICE = "\n\n[Conteúdo truncado para se adequar ao limite da API.]"

def reduzir_texto(texto, limite=TEXTO_LIMITE):
    if not texto:
        return texto
    if texto.endswith(TRUNCATE_NOTICE):
        return texto
    if len(texto) <= limite:
        return texto
    return texto[:limite] + TRUNCATE_NOTICE

def gerar_resumo(texto):
    prompt = "Faça um resumo detalhado e estruturado do seguinte texto. Organize em tópicos principais e subtópicos quando necessário:"
    resposta = gerar_com_gemini(prompt, texto)
    if not resposta:
        raise ValueError("Nenhuma resposta retornada pelo modelo para o resumo.")
    return resposta

def gerar_resumo_curto(texto):
    prompt = "Resuma o seguinte conteúdo de forma clara e objetiva, destacando os principais tópicos em até 6 parágrafos curtos:"
    resposta = gerar_com_gemini(prompt, texto)
    if not resposta:
        raise ValueError("Nenhuma resposta retornada pelo modelo para o resumo curto.")
    return resposta

def formatar_conteudo_html(texto):
    if not texto:
        return ""
    texto = texto.replace("\r\n", "\n")
    blocos_codigo = []

    def armazenar_bloco(match):
        blocos_codigo.append(match.group(1))
        return f"__CODE_BLOCK_{len(blocos_codigo) - 1}__"

    texto = re.sub(r"```([\s\S]+?)```", armazenar_bloco, texto)
    texto = html.escape(texto)
    texto = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"__(.*?)__", r"<strong>\1</strong>", texto)
    texto = re.sub(r"\*(.*?)\*", r"<em>\1</em>", texto)
    texto = texto.replace("\n- ", "<br>• ")
    texto = texto.replace("\n• ", "<br>• ")
    texto = texto.replace("\n", "<br>")

    for indice, bloco in enumerate(blocos_codigo):
        conteudo = html.escape(bloco)
        texto = texto.replace(f"__CODE_BLOCK_{indice}__", f"<pre>{conteudo}</pre>")

    return texto

def criar_link_download(dados, nome_arquivo, mime):
    if isinstance(dados, str):
        dados = dados.encode("utf-8")
    base = base64.b64encode(dados).decode()
    return f'<a class="download-link" href="data:{mime};base64,{base}" download="{nome_arquivo}">⬇️ Baixar {nome_arquivo}</a>'

def render_text_section(titulo, icone, conteudo, nome_arquivo):
    corpo = formatar_conteudo_html(conteudo)
    link = criar_link_download(conteudo, nome_arquivo, "text/plain")
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title"><span>{icone}</span>{titulo}</div>
            <div class="card-content">{corpo}</div>
            {link}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div class='main-title'>🚀 Resumo Turbo</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Transforme seus PDFs em resumos inteligentes com o poder do Google Gemini.</div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown("<h3 style='font-weight:700;margin-bottom:1rem;'>📄 Faça upload do PDF que deseja resumir</h3>", unsafe_allow_html=True)
arquivo_upload = st.file_uploader("Selecione um arquivo PDF", type=['pdf'])

if arquivo_upload:
    with st.spinner("Extraindo texto do PDF..."):
        texto_extraido = extrair_texto_pdf(arquivo_upload)
    if texto_extraido and len(texto_extraido.strip()) > 100:
        st.success(f"✅ PDF processado! {len(texto_extraido)} caracteres extraídos.")
        texto_preparado = reduzir_texto(texto_extraido)
        if len(texto_extraido) > TEXTO_LIMITE:
            st.info("O texto foi truncado para se adequar ao limite de 12.000 caracteres da API do Gemini.")

        if st.button("✨ Gerar resumo", type="primary", use_container_width=True):
            resumo_completo = None
            resumo_curto = None
            mensagens = []

            with st.spinner("Consultando o Gemini para criar o resumo detalhado..."):
                try:
                    resumo_completo = gerar_resumo(texto_preparado)
                except ValueError as e:
                    mensagens.append(str(e))
                except Exception as e:
                    mensagens.append(f"Erro ao gerar resumo detalhado: {str(e)}")

            if resumo_completo:
                with st.spinner("Gerando uma versão rápida do resumo..."):
                    try:
                        resumo_curto = gerar_resumo_curto(texto_preparado)
                    except ValueError as e:
                        mensagens.append(str(e))
                    except Exception as e:
                        mensagens.append(f"Erro ao gerar resumo curto: {str(e)}")

            st.markdown("---")
            st.markdown("<h3 style='font-weight:700;margin-bottom:1.2rem;'>✨ Resultado do resumo do PDF</h3>", unsafe_allow_html=True)

            if resumo_completo:
                render_text_section("Resumo Estruturado", "📝", resumo_completo, "resumo_detalhado.txt")

            if resumo_curto:
                render_text_section("Resumo Express", "⚡", resumo_curto, "resumo_express.txt")

            if mensagens:
                for msg in mensagens:
                    st.warning(msg)

            if resumo_completo or resumo_curto:
                st.success("Resumo gerado com sucesso!")
            else:
                st.error("Não foi possível gerar o resumo. Tente novamente com outro texto ou verifique sua chave da API.")
    else:
        st.warning("⚠️ Conteúdo insuficiente no PDF. Use um documento com mais de 100 caracteres.")
else:
    st.info("Envie um PDF para gerar o resumo com o Gemini.")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>💡 <strong>Resumo Turbo</strong> - Resumos inteligentes de PDFs com Google Gemini</p>
</div>
""", unsafe_allow_html=True)

