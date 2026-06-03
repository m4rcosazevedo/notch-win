# Notch Win 🚀

Uma barra de produtividade elegante e funcional inspirada no "Notch" do macOS, projetada para Windows e Linux. Construída com **Python** e **PyQt6**, flutua no topo da tela oferecendo acesso instantâneo a ferramentas essenciais sem ocupar espaço de trabalho.

---

## ✨ Funcionalidades

### 🎵 Multimídia

| Widget | Descrição |
|--------|-----------|
| **Spotify** | Exibe a faixa em reprodução com controles de Play/Pause, Anterior e Próxima. Requer configuração via Spotify for Developers. |
| **YouTube Feed** | Acompanha novos vídeos de canais favoritos (até 20) sem abrir o navegador. Suporta múltiplas contas Google autenticadas via OAuth. |

---

### 📊 Monitoramento

| Widget | Descrição |
|--------|-----------|
| **Monitor de Recursos** | Exibe CPU (%), RAM (%) e Latência de Rede (Ping em ms) em tempo real na barra. |
| **GitHub** | Contagem de notificações não lidas com suporte a múltiplas contas via Personal Access Token. |
| **Calendário** | Eventos do dia integrado com **Google Calendar** e **Outlook / Office 365**. Suporta múltiplas contas de ambos os provedores. |
| **WhatsApp** | Feed de mensagens recentes via integração local com o WhatsApp Web. |
| **Clima** | Temperatura atual e previsão do tempo para qualquer cidade do mundo. Exibe condição, sensação térmica, umidade, vento, previsão por hora (próximas 8h) e por dias (5 dias). Sem necessidade de API key — powered by Open-Meteo. |

---

### ⏱️ Produtividade

| Widget | Descrição |
|--------|-----------|
| **Pomodoro Timer** | Ciclos de foco configuráveis (15, 20, 25, 30, 45 ou 60 min) com pausa, reset e notificações nativas. |
| **Clipboard Manager** | Histórico dos últimos itens copiados para acesso rápido com um clique. |
| **Tarefas (Todo)** | Lista de afazeres persistente com checkbox de conclusão e remoção individual. |
| **Notas Rápidas** | Bloco de notas flutuante com salvamento automático. |
| **Despertador** | Configure alarmes com hora e som de notificação. |
| **Calculadora** | Atalho para a calculadora nativa do sistema. |
| **Calculadora de Horas** | Calcula diferenças e somas de intervalos de horas (útil para controle de ponto). |

---

### 🎨 Utilidades

| Widget | Descrição |
|--------|-----------|
| **Color Picker** | Captura a cor de qualquer pixel da tela e copia o valor em HEX e RGB. |
| **Régua de Pixel** | Régua flutuante e redimensionável para medir elementos na tela com precisão. |
| **Galeria de Fotos** | Slideshow flutuante com imagens de uma pasta configurada. |
| **Motivação** | Exibe citações motivacionais aleatórias em português. |

---

### 🎮 Entretenimento

| Widget | Descrição |
|--------|-----------|
| **Pokémon Aleatório** | Busca e exibe as informações de um Pokémon aleatório a cada clique. |
| **Zona Anti-Stress** | Mini-game com monstros para uma pausa rápida entre tarefas. |
| **Navinha 🚀** | Jogo de nave espacial estilo arcade. Desvie de asteroides, destrua-os e sobreviva por **3 minutos**. Velocidade aumenta progressivamente a cada 30 segundos. Colecionáveis de bônus melhoram o armamento da nave. |

#### Navinha — detalhes do jogo

- **Controle**: segure o botão esquerdo do mouse → a nave se move suavemente em direção ao cursor
- **Tiros**: automáticos, com cadência crescente conforme o nível
- **Progressão**: a cada 30s sobe um nível, aumentando a velocidade e a quantidade de asteroides
- **Power-ups de tiro** (estrelas colecionáveis que caem do topo):
  - ★ **Dourada** (1 min) → Tiro Duplo — 2 balas simultâneas
  - ★ **Roxa** (2 min) → Tiro Triplo — 3 balas espalhadas em leque (−15°, 0°, +15°)
- **Vitória**: sobreviver os 3 minutos completos 🏆

---

## 🎨 Design e Personalização

### Temas

Mais de **17 presets** acessíveis com o botão direito na barra:

**Dark**
| | | | |
|-|-|-|-|
| Space Gray | Graphite | Midnight | Ocean |
| Viridian | Forest | Grape | Rosewood |
| Ember | Obsidian | | |

**Light**
| | | | |
|-|-|-|-|
| Arctic | Sand | Blossom | Sky |
| Mint | Lavender | Cream | |

### Comportamento

- **Auto-Hide inteligente**: a barra se retrai automaticamente após 3 segundos de inatividade. Encoste o mouse no topo da tela para reaparecer com animação suave.
- **Arrastar para mover**: clique e arraste em qualquer área vazia para reposicionar.
- **Ícone na bandeja**: acesso rápido a Mostrar/Ocultar e Sair sem precisar da barra visível.
- **Iniciar com o sistema**: opção para iniciar automaticamente com o Windows/Linux.

---

## ⚙️ Configurações

Acesse via **botão direito → Configurações** (ou `⚙ Configurações` no menu de contexto).

### Seções visíveis
Ative ou desative individualmente qualquer widget da barra.

### YouTube
1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com) e ative a **YouTube Data API v3**
2. Gere credenciais OAuth 2.0 (tipo "App para computador") e baixe o JSON
3. Em Configurações → YouTube, selecione o arquivo e conecte sua conta
4. Marque até **20 canais favoritos** para monitorar

### Spotify
1. Crie um app no [Spotify for Developers](https://developer.spotify.com/dashboard)
2. Adicione `http://127.0.0.1:8888/callback` como Redirect URI
3. Em Configurações → Spotify, insira o **Client ID** e o **Client Secret**

### GitHub
1. Gere um Personal Access Token em [GitHub Settings → Developer settings → Tokens](https://github.com/settings/tokens) com escopo `notifications`
2. Em Configurações → GitHub, adicione quantas contas desejar

### Calendário
- **Google**: use o mesmo arquivo JSON de credenciais do YouTube
- **Outlook**: registre um app no [Portal Azure](https://portal.azure.com) e cole o Application (client) ID

### Clima
Em Configurações → Clima, digite o nome de qualquer cidade (ex: `São Paulo`, `London`, `Tokyo`) e clique em **Salvar**. Não requer API key.

---

## 🚀 Instalação

### Pré-requisitos
- Python 3.10 ou superior
- pip

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/notch-win.git
cd notch-win

# 2. Criar e ativar ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar
python main.py
```

### Windows — instalador automático
Execute `Instalar_Notch.bat` para instalação guiada com atalho na área de trabalho.

---

## ⌨️ Referência de uso

| Ação | Como fazer |
|------|-----------|
| Mostrar a barra | Encoste o mouse no topo da tela |
| Ocultar a barra | Afaste o mouse por 3 segundos |
| Menu de temas | Clique com o botão direito na barra |
| Configurações | Botão direito → ⚙ Configurações |
| Mover a barra | Clique e arraste em área vazia |
| Minimizar para bandeja | Fechar a janela (X) |
| Restaurar da bandeja | Duplo clique no ícone da bandeja |
| Sair | Botão direito → Sair do Notch |

---

## 🛠️ Tecnologias

| Biblioteca | Uso |
|------------|-----|
| **PyQt6** | Interface gráfica, animações e game loop |
| **Spotipy** | API do Spotify |
| **google-api-python-client** | YouTube Data API v3 e Google Calendar |
| **google-auth-oauthlib** | Autenticação OAuth Google |
| **msal** | Autenticação Microsoft (Outlook/Office 365) |
| **PyGithub** | API do GitHub |
| **psutil** | Monitoramento de CPU e RAM |
| **ping3** | Medição de latência de rede |
| **playwright** | Integração com WhatsApp Web |
| **plyer** | Notificações nativas do sistema |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |

---

Desenvolvido com ❤️ para quem ama produtividade e estética.
