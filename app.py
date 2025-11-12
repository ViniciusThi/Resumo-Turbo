import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from io import BytesIO
import os

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
    "models/gemini-pro",
    "models/text-bison-001",
    "models/chat-bison-001",
]

st.set_page_config(
    page_title="Nutri IA",
    page_icon="🥗",
    layout="wide"
)

st.title("🥗 Nutri IA")
st.subheader("Planeje sua dieta personalizada e cardápio semanal em poucos minutos")

st.write("Preencha as perguntas abaixo e receba automaticamente uma dieta completa, lista de compras e receitas alinhadas aos seus objetivos.")


def gerar_com_gemini(prompt):
    erros = []
    for modelo_nome in PRIORIDADE_MODELOS:
        try:
            modelo = genai.GenerativeModel(
                model_name=modelo_nome,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS,
            )
            resposta = modelo.generate_content(prompt)
            texto = extrair_texto_resposta(resposta)
            if texto:
                return texto
            motivo = obter_motivo_resposta(resposta)
            if motivo:
                erros.append(f"{modelo_nome}: {motivo}")
        except Exception as erro:
            erros.append(f"{modelo_nome}: {erro}")
    raise ValueError(" | ".join(erros) if erros else "Nenhuma resposta retornada pela IA.")


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


def montar_prompt(dados_usuario):
    return f"""Você é um nutricionista brasileiro. Com base nos dados abaixo, elabore um plano alimentar individual detalhado.

Dados do usuário:
- Idade: {dados_usuario['idade']} anos
- Peso: {dados_usuario['peso']} kg
- Altura: {dados_usuario.get('altura', 'não informado')} cm
- Gênero biológico: {dados_usuario.get('genero', 'não informado')}
- Objetivo principal: {dados_usuario['objetivo']}
- Tempo disponível para preparo das refeições por dia: {dados_usuario['tempo']}
- Alergias ou restrições alimentares: {dados_usuario['alergias']}
- Orçamento semanal estimado: {dados_usuario['orcamento']}
- Preferências adicionais: {dados_usuario.get('preferencias', 'não informado')}

Regras:
1. Considere as informações de alergia e orçamento ao selecionar alimentos.
2. Ajuste quantidades à idade, peso e objetivo.
3. Mantenha linguagem em português do Brasil.

Formato obrigatório (Markdown):
## Resumo do Perfil
- 3 a 5 tópicos com insights principais do usuário.

## Dieta Personalizada
- Explique calorias estimadas e distribuição de macros.
- Descreva plano diário (café, lanche, almoço, lanche, jantar, ceia) com porções.

## Cardápio Semanal
- Tabela ou lista com refeições para segunda a domingo, adaptadas à rotina do usuário.

## Lista de Compras Semanal
- Organize por categorias (hortifruti, proteínas, grãos, laticínios, outros).
- Indique quantidades aproximadas.

## Receitas Sugeridas
- Forneça ao menos 3 receitas simples (ingredientes, preparo, tempo estimado).

## Dicas e Recomendações
- 4 a 6 bullets com orientações práticas.

## Plano de Acompanhamento
- Sugira métricas para acompanhar progresso e ajustes futuros.

Capriche no tom motivador, prático e profissional."""


def dividir_secoes(texto):
    secoes = {}
    titulo_atual = None
    linhas = texto.splitlines()
    for linha in linhas:
        if linha.startswith("## "):
            titulo_atual = linha[3:].strip()
            secoes[titulo_atual] = []
        elif titulo_atual:
            secoes[titulo_atual].append(linha)
    return {titulo: "\n".join(conteudo).strip() for titulo, conteudo in secoes.items()}


class PlanoPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Nutri IA - Plano Personalizado", ln=True, align="C")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def gerar_pdf(secoes):
    pdf = PlanoPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for titulo, conteudo in secoes.items():
        if not conteudo:
            continue
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 9, titulo)
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 11)
        for linha in conteudo.splitlines():
            texto = linha.strip()
            if not texto:
                pdf.ln(4)
            else:
                pdf.multi_cell(0, 6, texto)
        pdf.ln(5)

    buffer = BytesIO()
    pdf.output(buffer, "S")
    buffer.seek(0)
    return buffer


with st.form("form_nutri"):
    col1, col2, col3 = st.columns(3)

    with col1:
        idade = st.number_input("Idade", min_value=10, max_value=100, value=25)
        peso = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.5)
    with col2:
        altura = st.number_input("Altura (cm)", min_value=120, max_value=220, value=170)
        genero = st.selectbox("Gênero biológico", ["Feminino", "Masculino", "Outro", "Prefiro não informar"])
    with col3:
        objetivo = st.selectbox(
            "Objetivo principal",
            [
                "Perder peso de forma saudável",
                "Ganhar massa muscular",
                "Manter peso com energia",
                "Melhorar hábitos alimentares",
                "Plano vegetariano/vegano equilibrado",
            ],
        )
        tempo = st.selectbox(
            "Tempo disponível para cozinhar (por dia)",
            ["Até 20 minutos", "Entre 20 e 40 minutos", "Mais de 40 minutos"],
        )

    alergias = st.text_input("Alergias ou restrições", placeholder="Ex.: intolerância à lactose, alergia a frutos do mar")
    preferencias = st.text_input("Preferências gastronômicas", placeholder="Ex.: gosto de culinária mediterrânea, evitar frituras")
    orcamento = st.selectbox(
        "Orçamento semanal",
        ["Baixo", "Moderado", "Alto"],
        index=1,
    )

    gerar = st.form_submit_button("Gerar plano alimentar", use_container_width=True)

if gerar:
    dados = {
        "idade": idade,
        "peso": peso,
        "altura": altura,
        "genero": genero,
        "objetivo": objetivo,
        "tempo": tempo,
        "alergias": alergias or "Nenhuma informada",
        "preferencias": preferencias or "Nenhuma informada",
        "orcamento": orcamento,
    }

    with st.spinner("Consultando o Nutri IA..."):
        try:
            plano_texto = gerar_com_gemini(montar_prompt(dados))
            secoes = dividir_secoes(plano_texto)

            st.success("Plano gerado com sucesso! Confira os detalhes abaixo.")

            for titulo, conteudo in secoes.items():
                with st.expander(titulo, expanded=titulo in ["Resumo do Perfil", "Dieta Personalizada"]):
                    st.markdown(conteudo)

            st.download_button(
                "⬇️ Fazer download em texto",
                plano_texto,
                file_name="plano_nutri_ia.txt",
                mime="text/plain",
            )

            pdf_buffer = gerar_pdf(secoes)
            st.download_button(
                "⬇️ Versão imprimível (PDF)",
                pdf_buffer,
                file_name="plano_nutri_ia.pdf",
                mime="application/pdf",
            )

        except Exception as erro:
            st.error(f"Não foi possível gerar o plano. Detalhes: {erro}")
else:
    st.info("Preencha o formulário e clique em 'Gerar plano alimentar' para receber sua dieta personalizada.")

