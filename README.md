# 🥗 Nutri IA

Aplicativo em Streamlit que cria uma dieta personalizada, cardápio semanal e lista de compras completa a partir de seis perguntas rápidas. Ideal para quem quer organizar refeições de forma prática usando a Google Gemini API.

## ✨ Funcionalidades

- 🧑‍⚕️ **Plano alimentar personalizado** com macros e refeições distribuídas ao longo do dia
- 🗓️ **Cardápio semanal pronto** adaptado ao tempo disponível para cozinhar
- 🛒 **Lista de compras organizada por categorias** com quantidades aproximadas
- 🍲 **Receitas sugeridas** simples e alinhadas às restrições informadas
- 📄 **Versão imprimível (PDF)** gerada automaticamente para salvar ou compartilhar

## 🛠️ Tecnologias

- **Streamlit** para a interface web
- **Google Gemini API** para geração do plano nutricional
- **FPDF** para montar o PDF imprimível
- **Python 3.9+**

## ⚙️ Configuração

### 1. Clonar o projeto
```bash
git clone https://github.com/ViniciusThi/Resumo-Turbo.git
cd Resumo-Turbo
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Definir a chave da API Gemini
- Gere uma chave em: [Google AI Studio](https://aistudio.google.com/app/apikey)
- No Streamlit Cloud, adicione em **Settings → Secrets**:
  ```toml
  GEMINI_API_KEY = "sua_chave_aqui"
  ```
- Para uso local (PowerShell):
  ```powershell
  $env:GEMINI_API_KEY="sua_chave_aqui"
  ```

### 4. Executar o app
```bash
streamlit run app.py
```

## ☁️ Deploy no Streamlit Cloud
1. Faça login em [share.streamlit.io](https://share.streamlit.io)
2. Clique em **New app**
3. Informe:
   - Repository: `ViniciusThi/Resumo-Turbo`
   - Branch: `main`
   - Main file path: `app.py`
4. Em **Settings → Secrets**, salve a chave `GEMINI_API_KEY`
5. Aguarde o deploy automático

## 🧪 Como usar
1. Informe idade, peso, altura, objetivo, tempo para cozinhar, alergias e orçamento
2. Clique em **Gerar plano alimentar**
3. Visualize o plano detalhado em abas expansíveis
4. Baixe o plano em texto ou PDF para imprimir/compartilhar

## 📌 Observações
- Certifique-se de usar uma chave criada com o fluxo "Create API key in new project" (API v1)
- Limites do plano gratuito podem restringir o número de planos por dia
- Ajuste as respostas do formulário caso o modelo sinalize dúvidas ou restrições

## 👨‍💻 Autor
- **Vinicius Thi** – [github.com/ViniciusThi](https://github.com/ViniciusThi)

Boa dieta! 🥦🍚🍎

