# 🚀 Resumo Turbo

Aplicativo inteligente de estudo que transforma PDFs, textos e links em material de aprendizado usando IA do Google Gemini.

## ✨ Funcionalidades

- 📄 **Upload de PDF** - Processe documentos PDF automaticamente
- ✏️ **Texto Direto** - Cole qualquer texto para análise
- 🔗 **Extração de Links** - Extraia conteúdo de páginas web
- 📝 **Resumo Inteligente** - Resumos estruturados e detalhados
- 🧠 **Mapa Mental** - Visualização hierárquica do conteúdo
- ❓ **10 Questões** - Questões de múltipla escolha com respostas
- 🎴 **Flashcards** - Cards de estudo frente/verso
- 🔊 **Áudio** - Converta resumos em áudio para escutar

## 🛠️ Tecnologias

- **Streamlit** - Interface web interativa
- **Google Gemini AI** - Processamento de linguagem natural
- **PyPDF2** - Extração de texto de PDFs
- **gTTS** - Conversão texto para fala
- **BeautifulSoup4** - Web scraping

## 📦 Instalação Local

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/ViniciusThi/Resumo-Turbo.git
cd Resumo-Turbo
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure a API Key (opcional):
   - Copie `.env.example` para `.env`
   - Adicione sua chave da API do Gemini (já configurada no código)

4. Execute o aplicativo:
```bash
streamlit run app.py
```

5. Acesse no navegador:
```
http://localhost:8501
```

## ☁️ Deploy no Streamlit Cloud

### Passo a Passo

1. **Faça fork ou clone este repositório**

2. **Acesse Streamlit Cloud:**
   - Vá para [share.streamlit.io](https://share.streamlit.io)
   - Faça login com sua conta GitHub

3. **Deploy:**
   - Clique em "New app"
   - Selecione o repositório: `ViniciusThi/Resumo-Turbo`
   - Branch: `main`
   - Main file: `app.py`
   - Clique em "Deploy"

4. **Configure Secrets (se necessário):**
   - No painel do app, vá em Settings > Secrets
   - Adicione:
   ```toml
   GEMINI_API_KEY = "sua_chave_api_aqui"
   ```

5. **Pronto!** Seu app estará disponível em: `https://seu-app.streamlit.app`

## 🎯 Como Usar

1. **Escolha o método de entrada:**
   - Upload de arquivo PDF
   - Cole texto diretamente
   - Insira URL de um artigo/página

2. **Selecione as funcionalidades desejadas:**
   - Marque os checkboxes do que deseja gerar
   - Todas vêm selecionadas por padrão

3. **Clique em "Gerar Conteúdo"**
   - Aguarde o processamento
   - Visualize os resultados

4. **Faça download:**
   - Cada seção tem botão de download
   - Salve em formato TXT ou MP3 (áudio)

## 📝 Exemplos de Uso

### Para Estudantes
- Resuma apostilas e livros didáticos
- Crie material de revisão para provas
- Gere questões para auto-avaliação

### Para Profissionais
- Resuma artigos e papers
- Crie apresentações a partir de documentos
- Extraia insights de relatórios

### Para Pesquisadores
- Analise múltiplos artigos rapidamente
- Organize informações em mapas mentais
- Crie fichas de estudo estruturadas

## 🔑 API Key do Google Gemini

Este projeto usa a API do Google Gemini. Para obter sua própria chave:

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave gerada
5. Substitua no código ou configure via secrets

## ⚙️ Configuração

### Limites de Texto

O aplicativo processa textos de qualquer tamanho, mas para melhor performance:
- **Mínimo:** 100 caracteres
- **Recomendado:** 500-5000 caracteres
- **Máximo:** Limitado pela API do Gemini

### Formatos Suportados

- **PDF:** Qualquer PDF com texto extraível
- **Texto:** UTF-8, qualquer idioma
- **URLs:** Sites com conteúdo HTML padrão

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto é de código aberto e está disponível sob a [MIT License](LICENSE).

## 👨‍💻 Autor

**Vinicius Thi**
- GitHub: [@ViniciusThi](https://github.com/ViniciusThi)

## 🙏 Agradecimentos

- Google Gemini pela API de IA
- Streamlit pela framework incrível
- Comunidade open source

## 📞 Suporte

Encontrou um bug ou tem uma sugestão? 
- Abra uma [issue](https://github.com/ViniciusThi/Resumo-Turbo/issues)
- Entre em contato via GitHub

---

<div align="center">
  <p>Feito com ❤️ para facilitar seus estudos</p>
  <p>⭐ Se este projeto te ajudou, considere dar uma estrela!</p>
</div>

