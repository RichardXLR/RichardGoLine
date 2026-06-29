# RichardGoLine - GitHub Actions Setup (100% Grátis)

## 🚀 Quick Start (5 minutos)

### 1. Crie um repositório no GitHub
```bash
# Opção A: Use este diretório como repo
cd /var/mnt/hd/projetos/YT
git init
git add .
git commit -m "RichardGoLine - GitHub Actions"
gh repo create RichardGoLine --public --source=. --push

# Opção B: Crie no site github.com/new e faça push
```

### 2. O workflow já está pronto!
O arquivo `.github/workflows/download.yml` já foi criado com:
- ✅ Trigger manual (botão "Run workflow")
- ✅ Trigger via API (`repository_dispatch`)
- ✅ 3 tentativas automáticas com backoff
- ✅ Upload artifact (7 dias retenção)
- ✅ Resumo bonito no GitHub

### 3. Configure secrets (opcional - para artifacts privados)
Settings → Secrets → Actions → New repository secret:
- `GH_TOKEN` - seu Personal Access Token (se repo privado)

---

## 📱 Como Usar

### Método 1: Interface Web (Mais Fácil)
1. Vá em: `https://github.com/SEU_USER/RichardGoLine/actions`
2. Clique em **"RichardGoLine - YouTube Downloader"**
3. Clique **"Run workflow"** (botão verde à direita)
4. Preencha:
   - **URL**: `https://youtube.com/watch?v=...`
   - **Modo**: `bestaudio (Apenas áudio)` ou `bestvideo+bestaudio (Máxima qualidade)`
   - **Formato áudio**: `opus` / `mp3` / `flac`
   - **SponsorBlock**: `true`
4. Clique **"Run workflow"**
5. Aguarde (ícone amarelo → verde)
6. Clique no run → aba **Artifacts** → baixe o ZIP

---

### Método 2: CLI com `gh-rgl` (Recomendado)

```bash
# Instala o wrapper
cp /var/mnt/hd/projetos/YT/gh-rgl ~/.local/bin/
chmod +x ~/.local/bin/gh-rgl

# Ou adiciona ao PATH
echo 'export PATH="$PATH:/var/mnt/hd/projetos/YT"' >> ~/.bashrc
source ~/.bashrc

# Uso básico
gh-rgl "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Áudio MP3 e espera baixar
gh-rgl "URL" -m audio -a mp3 -w

# Vídeo 1080p e espera
gh-rgl "URL" -m 1080p -w

# Formato customizado (4K VP9 + Opus)
gh-rgl "URL" -m custom -f "313+251" -w

# Playlist só itens 1,3,5-10
gh-rgl "https://youtube.com/playlist?list=..." -p "1,3,5-10" -w
```

---

### Método 3: API Direta (Para bots/apps)

```bash
# Trigger via curl
curl -X POST \
  -H "Authorization: token SEU_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/SEU_USER/RichardGoLine/dispatches \
  -d '{
    "event_type": "download-request",
    "client_payload": {
      "url": "https://youtube.com/watch?v=...",
      "mode": "bestaudio (Apenas áudio - MP3/Opus/FLAC)",
      "audio_format": "opus",
      "audio_quality": "0",
      "sponsorblock": true,
      "concurrent": "8"
    }
  }'

# Poll status
curl -H "Authorization: token SEU_PAT" \
  https://api.github.com/repos/SEU_USER/RichardGoLine/actions/runs?event=repository_dispatch
```

---

### Método 4: GitHub CLI (`gh`)

```bash
# Trigger
gh workflow run download.yml \
  -f url="https://youtube.com/watch?v=..." \
  -f mode="bestaudio (Apenas áudio - MP3/Opus/FLAC)" \
  -f audio_format="opus" \
  -f audio_quality="0"

# Lista runs
gh run list --workflow=download.yml --limit=5

# Acompanha ao vivo
gh run watch RUN_ID

# Baixa artifact
gh run download RUN_ID --dir ~/Downloads
```

---

## 🎯 Exemplos Práticos

| Objetivo | Comando |
|----------|---------|
| **Música MP3 320kbps** | `gh-rgl "URL" -m audio -a mp3 -w` |
| **Áudio Opus qualidade máxima** | `gh-rgl "URL" -m audio -a opus -q 0 -w` |
| **Vídeo 4K MKV** | `gh-rgl "URL" -m 4k -w` |
| **Vídeo 1080p MP4** | `gh-rgl "URL" -m 1080p -w` |
| **Só vídeo (sem áudio)** | `gh-rgl "URL" -m video -w` |
| **Com legendas PT/EN** | `gh-rgl "URL" -l -L "pt,en" -w` |
| **Com thumbnail + metadata** | `gh-rgl "URL" -t -M -w` |
| **Playlist itens 1-5** | `gh-rgl "URL" -p "1-5" -w` |
| **Só após 2024** | `gh-rgl "URL" -d "20240101" -w` |
| **Limitar velocidade** | `gh-rgl "URL" -T "5M" -w` |

---

## ⚠️ Limites Importantes

| Limite | Valor | Workaround |
|--------|-------|------------|
| **Arquivo máx** | ~2 GB (GitHub artifact) | Use modo áudio ou resolução menor |
| **Minutos/mês** | 2.000 (público) / 500 (privado) | Suficiente para ~40 downloads |
| **Tempo máx** | 6 horas/job | OK |
| **Retenção** | 7-90 dias (config) | Baixe rápido |
| **IP GitHub** | Pode ser bloqueado | Retry automático + throttle |

**Se der erro 403/429 (IP bloqueado):**
- O workflow já tem 3 retries com throttle progressivo
- Tente adicionar `-T "1M"` ou `-T "500K"`
- Use modo `audio` (menos tráfego)

---

## 📁 Estrutura do Projeto

```
/var/mnt/hd/projetos/YT/
├── .github/workflows/download.yml   # Workflow principal
├── gh-rgl                           # CLI wrapper
├── RichardGoLine.py                 # CLI local
├── RichardGoLine_GUI.py             # GUI local
├── README.md
└── INSTALL.md
```

---

## 🔧 Personalização

### Mudar retenção (dias)
Edite `.github/workflows/download.yml`:
```yaml
env:
  RETENTION_DAYS: 30  # Máx 90
```

### Mudar limite de arquivo
```yaml
env:
  MAX_FILESIZE: 1900M  # GitHub limit ~2GB
```

### Adicionar notificação Discord/Slack
No job `notify`, adicione:
```yaml
- name: 🔔 Discord
  if: always()
  run: |
    curl -X POST "$DISCORD_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d '{"content": "Download ${{ job.status }}: ${{ needs.validate.outputs.url }}"}'
  env:
    DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
```

---

## 🆘 Troubleshooting

| Erro | Solução |
|------|---------|
| `gh: command not found` | `sudo apt install gh` ou `brew install gh` |
| `gh auth status` falha | `gh auth login` |
| `Workflow not found` | Verifique se `.github/workflows/download.yml` existe no repo |
| `Artifact not found` | Aguarde job terminar; verifique se `upload-artifact` rodou |
| `File too large` | Use `-m audio` ou `-m 720p` ou `-T "2M"` |
| `403 Forbidden` | Adicione `-T "1M"`; tente novamente em alguns minutos |
| `Timeout` | Vídeo muito grande; use resolução menor |

---

## 💡 Dicas Pro

1. **Repo público = 2000 min/mês grátis** (vs 500 privado)
2. **Artifacts expiram em 7 dias** - baixe logo
3. **Use `-w` flag** no `gh-rgl` para auto-baixar
4. **Para playlists grandes**: use `-p "1-10"` para dividir em batches
5. **Combine com cron**: `gh workflow run` via GitHub Actions schedule para downloads agendados

---

## 🎉 Pronto!

Seu RichardGoLine agora roda **100% na nuvem, grátis, sem seu PC ligado**.

```bash
# Teste agora:
gh-rgl "https://youtu.be/dQw4w9WgXcQ" -m audio -a opus -w
```