# Notch Win 🚀

Uma barra de produtividade elegante e funcional inspirada no "Notch" do macOS, projetada especificamente para Windows. Construída com **Python** e **PyQt6**, ela flutua no topo da sua tela, oferecendo acesso instantâneo a ferramentas essenciais enquanto mantém sua área de trabalho limpa.

---

## ✨ Funcionalidades

### 🎵 Multimídia e Produtividade
- **Spotify Hub**: Visualize a faixa atual e controle sua música (Play/Pause, Anterior, Próxima) diretamente do Notch.
- **Pomodoro Timer**: Ciclos de foco configuráveis (15, 20, 25, 30, 45 ou 60 min) com notificações nativas.
- **Clipboard Manager**: Histórico inteligente dos últimos itens copiados para acesso rápido.
- **YouTube Feed**: Acompanhe atualizações do seu feed favorito sem abrir o navegador.

### 🛠️ Ferramentas Rápidas (Popups)
Acesso instantâneo com um clique:
- 📝 **Notas Rápidas**: Bloco de notas persistente para lembretes instantâneos.
- ✅ **Tarefas (Todo)**: Lista de afazeres simples e eficaz.
- ⏰ **Despertador**: Configure alarmes rápidos para não perder compromissos.
- 🧮 **Calculadoras**: Acesso à calculadora do sistema e uma exclusiva **Calculadora de Horas** (ideal para somar tempos de projetos).
- 🖼️ **Galeria**: Slideshow de fotos flutuante.
- 💡 **Motivação**: Citações aleatórias para inspirar seu dia.

### 🎮 Diversão e Bem-estar
- 🐲 **Zona Anti-Stress**: Um mini-game rápido com monstros para relaxar entre tarefas.
- 🐾 **Pokémon Diário**: Descubra um Pokémon aleatório a qualquer momento.

---

## 🎨 Design e Personalização

- **Auto-Hide Inteligente**: A barra se esconde automaticamente após 10 segundos de inatividade para economizar espaço. Basta encostar o mouse no topo da tela para ela reaparecer.
- **Temas Dinâmicos**: Mais de 17 presets de cores, incluindo:
  - **Dark**: Space Gray, Graphite, Midnight, Ocean, Forest, Ember, Obsidian, e mais.
  - **Light**: Arctic, Sand, Sky, Mint, Lavender, etc.
- **Layout Customizável**: Através da janela de configurações, escolha exatamente quais módulos deseja ver na sua barra.
- **Surgical Drag**: Clique e arraste para posicionar o Notch onde preferir.

---

## 🚀 Instalação

### Pré-requisitos
- Python 3.10 ou superior
- Pip (gerenciador de pacotes)

### Passo a Passo

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/notch-win.git
   cd notch-win
   ```

2. **Criar e ativar ambiente virtual:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuração

### Spotify (Opcional)
Para habilitar o controle de música:
1. Vá para o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Crie um App e defina o Redirect URI como: `http://localhost:8888/callback`.
3. Copie o `Client ID` e o `Client Secret`.
4. Clique com o botão direito no Notch -> **Configurações** e insira suas credenciais.

### YouTube
Para o feed do YouTube, você pode configurar sua API Key na mesma janela de configurações.

---

## ⌨️ Atalhos e Uso

| Ação | Comando |
|---|---|
| **Mostrar/Ocultar** | Encostar o mouse no topo ou Duplo clique no ícone da bandeja |
| **Menu de Temas** | Clique com o botão direito no corpo da barra |
| **Mover Barra** | Clique e arraste em qualquer área vazia do Notch |
| **Configurações** | Botão direito -> Configurações |
| **Sair** | Botão direito -> Sair |

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **PyQt6**: Interface gráfica e animações.
- **Spotipy**: Integração com API do Spotify.
- **Requests**: Chamadas de API para Pokémon e YouTube.
- **Plyer**: Notificações nativas do sistema.

---
Desenvolvido com ❤️ para usuários que amam produtividade e estética.
