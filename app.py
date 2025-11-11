import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import tempfile
import requests
from bs4 import BeautifulSoup
from io import BytesIO

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Configure a variavel GEMINI_API_KEY nos secrets do Streamlit ou nas variaveis de ambiente.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 1024,
}

modelo_texto = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=GENERATION_CONFIG,
)

st.set_page_config(
    page_title="Resumo Turbo",
    page_icon="🚀",
    layout="wide"
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
    resposta = modelo_texto.generate_content(prompt_completo)
    return extrair_texto_resposta(resposta)

def extrair_texto_resposta(resposta):
    if not resposta or not getattr(resposta, "candidates", None):
        return None
    for candidato in resposta.candidates:
        if getattr(candidato, "content", None):
            partes = []
            for parte in candidato.content.parts:
                texto = getattr(parte, "text", None)
                if texto:
                    partes.append(texto)
            if partes:
                return "\n".join(partes).strip()
    return None

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

st.title("🚀 Resumo Turbo")
st.subheader("Transforme seus PDFs, textos e links em conteúdo de estudo inteligente!")

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
    st.subheader("🎯 Escolha as funcionalidades que deseja gerar:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gerar_resumo_check = st.checkbox("📝 Resumo", value=True)
        gerar_mapa_check = st.checkbox("🧠 Mapa Mental", value=True)
        gerar_questoes_check = st.checkbox("❓ 10 Questões", value=True)
    
    with col2:
        gerar_flashcards_check = st.checkbox("🎴 Flashcards", value=True)
        gerar_audio_check = st.checkbox("🔊 Áudio do Resumo", value=True)
    
    if st.button("✨ Gerar Conteúdo", type="primary", use_container_width=True):
        
        if gerar_resumo_check:
            with st.spinner("Gerando resumo..."):
                try:
                    resumo = gerar_resumo(texto_conteudo)
                    st.markdown("## 📝 Resumo")
                    st.markdown(resumo)
                    st.download_button(
                        "⬇️ Download Resumo",
                        resumo,
                        file_name="resumo.txt",
                        mime="text/plain"
                    )
                    
                    if gerar_audio_check:
                        with st.spinner("Gerando áudio do resumo..."):
                            audio = texto_para_audio(resumo)
                            if audio:
                                st.audio(audio, format='audio/mp3')
                                st.download_button(
                                    "⬇️ Download Áudio",
                                    audio,
                                    file_name="resumo.mp3",
                                    mime="audio/mp3"
                                )
                    
                    st.markdown("---")
                except Exception as e:
                    st.error(f"Erro ao gerar resumo: {str(e)}")
        
        if gerar_mapa_check:
            with st.spinner("Criando mapa mental..."):
                try:
                    mapa = gerar_mapa_mental(texto_conteudo)
                    st.markdown("## 🧠 Mapa Mental")
                    st.markdown(mapa)
                    st.download_button(
                        "⬇️ Download Mapa Mental",
                        mapa,
                        file_name="mapa_mental.txt",
                        mime="text/plain"
                    )
                    st.markdown("---")
                except Exception as e:
                    st.error(f"Erro ao gerar mapa mental: {str(e)}")
        
        if gerar_questoes_check:
            with st.spinner("Gerando questões..."):
                try:
                    questoes = gerar_questoes(texto_conteudo)
                    st.markdown("## ❓ Questões de Estudo")
                    st.markdown(questoes)
                    st.download_button(
                        "⬇️ Download Questões",
                        questoes,
                        file_name="questoes.txt",
                        mime="text/plain"
                    )
                    st.markdown("---")
                except Exception as e:
                    st.error(f"Erro ao gerar questões: {str(e)}")
        
        if gerar_flashcards_check:
            with st.spinner("Criando flashcards..."):
                try:
                    flashcards = gerar_flashcards(texto_conteudo)
                    st.markdown("## 🎴 Flashcards")
                    st.markdown(flashcards)
                    st.download_button(
                        "⬇️ Download Flashcards",
                        flashcards,
                        file_name="flashcards.txt",
                        mime="text/plain"
                    )
                    st.markdown("---")
                except Exception as e:
                    st.error(f"Erro ao gerar flashcards: {str(e)}")
        
        st.success("✅ Conteúdo gerado com sucesso!")

elif texto_conteudo and len(texto_conteudo.strip()) <= 100:
    st.warning("⚠️ O texto é muito curto. Por favor, insira um conteúdo com mais de 100 caracteres.")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>💡 <strong>Resumo Turbo</strong> - Powered by Google Gemini AI</p>
    <p>Desenvolvido para facilitar seus estudos 📚</p>
</div>
""", unsafe_allow_html=True)

