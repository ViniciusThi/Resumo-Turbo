import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import requests
from bs4 import BeautifulSoup
from io import BytesIO
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
    .stAudio {margin-top:16px;}
    .feature-grid {background:white;border:1px solid rgba(15,23,42,0.06);border-radius:16px;padding:18px 22px;margin-bottom:18px;display:grid;gap:14px;}
    .feature-grid > label {font-weight:600;border:1px solid rgba(99,102,241,0.12);border-radius:14px;padding:14px 16px;box-shadow:0 20px 32px -28px rgba(79,70,229,0.5);}
    .feature-grid > label:hover {border-color:#6366f1;}
    .stRadio > div[role="radiogroup"] {background:white;border:1px solid rgba(15,23,42,0.08);padding:12px;border-radius:16px;gap:12px;}
    .stRadio > div[role="radiogroup"] > label {border-radius:12px;padding:10px 16px;font-weight:600;}
    .stTextInput > label, .stTextArea > label, .stFileUploader > label {font-weight:600;}
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

def extrair_texto_url(url):
    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        texto = soup.get_text()
        linhas = (linha.strip() for linha in texto.splitlines())
        pedacos = (frase.strip() for linha in linhas for frase in linha.split("  "))
        texto = ' '.join(pedaco for pedaco in pedacos if pedaco)
        
        return texto
    except Exception as e:
        st.error(f"Erro ao extrair texto da URL: {str(e)}")
        return None

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

def gerar_mapa_mental(texto):
    prompt = """Crie um mapa mental em formato de texto estruturado do seguinte conteúdo. 
    Use emojis e indentação para mostrar a hierarquia. Formato:
    
    🎯 TEMA CENTRAL
    ├── 📌 Tópico Principal 1
    │   ├── 🔹 Subtópico 1.1
    │   └── 🔹 Subtópico 1.2
    ├── 📌 Tópico Principal 2
    │   ├── 🔹 Subtópico 2.1
    │   └── 🔹 Subtópico 2.2
    """
    resposta = gerar_com_gemini(prompt, texto)
    if not resposta:
        raise ValueError("Nenhuma resposta retornada pelo modelo para o mapa mental.")
    return resposta

def gerar_questoes(texto):
    prompt = """Gere exatamente 10 questões de múltipla escolha (A, B, C, D) baseadas no texto a seguir. 
    Para cada questão:
    1. Faça a pergunta
    2. Liste as 4 alternativas (A, B, C, D)
    3. Indique a resposta correta
    4. Dê uma breve explicação
    
    Formate assim:
    
    **Questão 1:** [pergunta]
    A) [alternativa]
    B) [alternativa]
    C) [alternativa]
    D) [alternativa]
    **Resposta:** [letra]
    **Explicação:** [explicação]
    """
    resposta = gerar_com_gemini(prompt, texto)
    if not resposta:
        raise ValueError("Nenhuma resposta retornada pelo modelo para as questões.")
    return resposta

def gerar_flashcards(texto):
    prompt = """Crie 10 flashcards do conteúdo a seguir. Para cada flashcard:
    - Frente: Uma pergunta ou conceito-chave
    - Verso: A resposta ou explicação
    
    Formate assim:
    
    **🎴 Flashcard 1**
    **Frente:** [pergunta/conceito]
    **Verso:** [resposta/explicação]
    
    ---
    """
    resposta = gerar_com_gemini(prompt, texto)
    if not resposta:
        raise ValueError("Nenhuma resposta retornada pelo modelo para os flashcards.")
    return resposta

def texto_para_audio(texto, idioma='pt'):
    try:
        tts = gTTS(text=texto, lang=idioma, slow=False)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        st.error(f"Erro ao gerar áudio: {str(e)}")
        return None

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

def render_audio_section(titulo, icone, audio_buffer, nome_arquivo):
    if not audio_buffer:
        return
    audio_buffer.seek(0)
    dados = audio_buffer.read()
    base = base64.b64encode(dados).decode()
    link = criar_link_download(dados, nome_arquivo, "audio/mp3")
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title"><span>{icone}</span>{titulo}</div>
            <div class="card-content">
                <audio controls style="width:100%;" src="data:audio/mp3;base64,{base}"></audio>
            </div>
            {link}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div class='main-title'>🚀 Resumo Turbo</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Transforme PDFs, textos e links em trilhas de estudo personalizadas com IA.</div>", unsafe_allow_html=True)

st.markdown("---")

opcao = st.radio(
    "Escolha como deseja inserir o conteúdo:",
    ["📄 Upload de PDF", "✏️ Texto Direto", "🔗 Link/URL"],
    horizontal=True
)

texto_conteudo = None

if opcao == "📄 Upload de PDF":
    arquivo_upload = st.file_uploader("Faça upload do seu PDF", type=['pdf'])
    if arquivo_upload:
        with st.spinner("Extraindo texto do PDF..."):
            texto_conteudo = extrair_texto_pdf(arquivo_upload)
            st.success(f"✅ PDF processado! {len(texto_conteudo)} caracteres extraídos.")

elif opcao == "✏️ Texto Direto":
    texto_conteudo = st.text_area(
        "Cole seu texto aqui:",
        height=200,
        placeholder="Digite ou cole o texto que deseja resumir..."
    )

elif opcao == "🔗 Link/URL":
    url_input = st.text_input("Cole a URL do artigo/página:")
    if url_input and st.button("Extrair texto da URL"):
        with st.spinner("Extraindo conteúdo da URL..."):
            texto_conteudo = extrair_texto_url(url_input)
            if texto_conteudo:
                st.success(f"✅ Conteúdo extraído! {len(texto_conteudo)} caracteres.")

if texto_conteudo and len(texto_conteudo.strip()) > 100:
    
    st.markdown("---")
    st.markdown("<h3 style='font-weight:700;margin-bottom:1rem;'>🎯 Escolha os blocos que deseja gerar</h3>", unsafe_allow_html=True)
    texto_preparado = reduzir_texto(texto_conteudo)
    if len(texto_conteudo) > TEXTO_LIMITE:
        st.info("O texto foi truncado para se adequar ao limite de 12.000 caracteres da API do Gemini.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gerar_resumo_check = st.checkbox("📝 Resumo", value=True)
        gerar_mapa_check = st.checkbox("🧠 Mapa Mental", value=True)
        gerar_questoes_check = st.checkbox("❓ 10 Questões", value=True)
    
    with col2:
        gerar_flashcards_check = st.checkbox("🎴 Flashcards", value=True)
        gerar_audio_check = st.checkbox("🔊 Áudio do Resumo", value=True)
    
    if st.button("✨ Gerar Conteúdo", type="primary", use_container_width=True):
        resultados = {}
        mensagens = []
        audio_resumo = None
        
        if gerar_resumo_check:
            with st.spinner("Gerando resumo com o Gemini..."):
                try:
                    resultados["resumo"] = gerar_resumo(texto_preparado)
                except ValueError as e:
                    mensagens.append(("Resumo", str(e)))
                except Exception as e:
                    mensagens.append(("Resumo", f"Erro ao gerar resumo: {str(e)}"))
        
        if gerar_mapa_check:
            with st.spinner("Desenhando mapa mental..."):
                try:
                    resultados["mapa"] = gerar_mapa_mental(texto_preparado)
                except ValueError as e:
                    mensagens.append(("Mapa mental", str(e)))
                except Exception as e:
                    mensagens.append(("Mapa mental", f"Erro ao gerar mapa mental: {str(e)}"))
        
        if gerar_questoes_check:
            with st.spinner("Criando questões desafiadoras..."):
                try:
                    resultados["questoes"] = gerar_questoes(texto_preparado)
                except ValueError as e:
                    mensagens.append(("Questões", str(e)))
                except Exception as e:
                    mensagens.append(("Questões", f"Erro ao gerar questões: {str(e)}"))
        
        if gerar_flashcards_check:
            with st.spinner("Montando flashcards..."):
                try:
                    resultados["flashcards"] = gerar_flashcards(texto_preparado)
                except ValueError as e:
                    mensagens.append(("Flashcards", str(e)))
                except Exception as e:
                    mensagens.append(("Flashcards", f"Erro ao gerar flashcards: {str(e)}"))
        
        if gerar_audio_check and "resumo" in resultados:
            with st.spinner("Narrando o resumo em áudio..."):
                audio_resumo = texto_para_audio(resultados["resumo"])
                if not audio_resumo:
                    mensagens.append(("Áudio", "Não foi possível gerar o áudio do resumo."))
        
        if resultados:
            st.markdown("---")
            st.markdown("<h3 style='font-weight:700;margin-bottom:1.2rem;'>✨ Seu material está pronto</h3>", unsafe_allow_html=True)
        
        if "resumo" in resultados:
            render_text_section("Resumo Inteligente", "📝", resultados["resumo"], "resumo.txt")
        
        if audio_resumo:
            render_audio_section("Áudio do Resumo", "🔊", audio_resumo, "resumo.mp3")
        
        if "mapa" in resultados:
            render_text_section("Mapa Mental", "🧠", resultados["mapa"], "mapa_mental.txt")
        
        if "questoes" in resultados:
            render_text_section("Questões para Revisar", "❓", resultados["questoes"], "questoes.txt")
        
        if "flashcards" in resultados:
            render_text_section("Flashcards de Bolso", "🎴", resultados["flashcards"], "flashcards.txt")
        
        if mensagens:
            for titulo, msg in mensagens:
                st.warning(f"{titulo}: {msg}")
        
        if resultados and not mensagens:
            st.success("Conteúdo gerado com sucesso!")
        elif not resultados:
            st.error("Não foi possível gerar conteúdo. Tente novamente com outro texto ou aguarde alguns instantes.")

elif texto_conteudo and len(texto_conteudo.strip()) <= 100:
    st.warning("⚠️ O texto é muito curto. Por favor, insira um conteúdo com mais de 100 caracteres.")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>💡 <strong>Resumo Turbo</strong> - Powered by Google Gemini AI</p>
    <p>Desenvolvido para facilitar seus estudos 📚</p>
</div>
""", unsafe_allow_html=True)

