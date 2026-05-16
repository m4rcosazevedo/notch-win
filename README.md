# Notch Win

Barra de produtividade estilo "notch" do Mac para Windows, feita com Python + PyQt6.

## Funcionalidades

- **Spotify** — nome da faixa atual + controles (anterior, play/pause, próxima)
- **Pomodoro** — timer 25/5/15 min com notificações nativas
- **Clipboard manager** — histórico dos últimos 15 itens copiados

## Instalação

```bash
cd notch-win

# Crie um ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

## Configuração do Spotify

1. Acesse https://developer.spotify.com/dashboard
2. Clique em **Create app**
3. Defina o Redirect URI como: `http://localhost:8888/callback`
4. Copie o **Client ID** e **Client Secret**

```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

## Executar

```bash
python main.py
```

Na primeira execução o Spotify abrirá o browser para autorização. Após isso o token fica em cache (`.spotify_cache`).

## Uso

| Ação | Como |
|---|---|
| Mover a barra | Clique e arraste |
| Play/Pause Spotify | Botão ⏸/▶ |
| Pomodoro iniciar/pausar | Botão ▶/⏸ |
| Pomodoro resetar | Botão ↺ |
| Ver clipboard | Botão ▾ → clique no item para copiar |
| Ocultar/mostrar | Duplo clique no ícone da bandeja |
| Sair | Botão direito no ícone da bandeja → Sair |
