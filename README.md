# RichardGoLine 🚀

**YouTube Downloader Ultra-Rápido com Máxima Qualidade**

Um wrapper Python potente para `yt-dlp` com foco em velocidade máxima, qualidade máxima e facilidade de uso.

## 🚀 Características

- ⚡ **Ultra-rápido**: Downloads paralelos com até 16 fragments simultâneos
- 🎯 **Máxima qualidade**: Seleciona automaticamente melhor vídeo + melhor áudio
- 🎵 **Áudio puro**: Extração direta para MP3, Opus, FLAC, M4A, WAV, etc.
- 🎬 **Vídeo + Áudio**: Merge automático em MKV/MP4/WebM/MOV
- 🚫 **SponsorBlock**: Remove patrocínios, intros, outros automaticamente
- 📝 **Legendas**: Download automático com suporte a múltiplos idiomas
- 🖼️ **Thumbnails & Metadados**: Embed automático de thumbnail e metadados
- 📋 **Playlists**: Suporte completo a playlists com filtros
- 📦 **Batch**: Processamento em lote via arquivo de URLs
- ⚡ **Retries inteligentes**: Retry automático com backoff exponencial
- 🎯 **Formato específico**: Seleção manual de formatos por ID

## 📦 Instalação

```bash
# Dependências
pip install yt-dlp

# OU no Fedora/RHEL
sudo dnf install yt-dlp

# OU no Ubuntu/Debian
sudo apt install yt-dlp

# OU no Arch
sudo pacman -S yt-dlp
```

```bash
# Clonar e usar
git clone <repo>
cd RichardGoLine
chmod +x RichardGoLine RichardGoLine.py

# Opcional: adicionar ao PATH
echo 'export PATH="$PATH:/caminho/para/RichardGoLine"' >> ~/.bashrc
source ~/.bashrc
```

## 🚀 Uso Rápido

```bash
# Melhor qualidade (vídeo + áudio) - PADRÃO
RichardGoLine "https://youtube.com/watch?v=..."

# Apenas áudio MP3 320kbps
RichardGoLine -a "https://youtube.com/watch?v=..."

# Apenas áudio Opus qualidade máxima
RichardGoLine -a --audio-format opus --audio-quality 0 "https://youtube.com/watch?v=..."

# Listar formatos disponíveis
RichardGoLine --list-formats "https://youtube.com/watch?v=..."

# Formato específico (ex: 4K VP9 + Opus)
RichardGoLine -f "313+251" "https://youtube.com/watch?v=..."

# Playlist completa com SponsorBlock
RichardGoLine --sponsorblock "https://youtube.com/playlist?list=..."

# Com legendas PT/EN
RichardGoLine -s --sub-langs "pt,en" "https://youtube.com/watch?v=..."

# Com thumbnail e metadados embedados
RichardGoLine -t -m "https://youtube.com/watch?v=..."

# Download em lote (arquivo com URLs)
RichardGoLine --batch urls.txt

# Diretório personalizado
RichardGoLine -o ~/Videos/YouTube "https://youtube.com/watch?v=..."

# Limitar velocidade (ex: 5MB/s)
RichardGoLine --throttle "5M" "https://youtube.com/watch?v=..."

# Mais velocidade (16 fragments paralelos)
RichardGoLine --concurrent-fragments 16 "https://youtube.com/watch?v=..."
```

## 📋 Exemplos Práticos

```bash
# Playlist de música - apenas MP3 320kbps com metadados
RichardGoLine -a -m --sponsorblock "https://youtube.com/playlist?list=PL..."

# Vídeo 4K + Áudio Opus (melhor qualidade)
RichardGoLine -f "313+251" --merge-format mkv "https://youtube.com/watch?v=..."

# Apenas vídeo 1080p (sem áudio) para edição
RichardGoLine --video-only "https://youtube.com/watch?v=..."

# Download apenas itens 1,3,5-10 da playlist
RichardGoLine --playlist-items "1,3,5-10" "https://youtube.com/playlist?list=..."

# Apenas vídeos após 2024
RichardGoLine --date-after "20240101" "https://youtube.com/playlist?list=..."

# Legendas em português, inglês e espanhol
RichardGoLine -s --sub-langs "pt,en,es" "https://youtube.com/watch?v=..."
```

## ⚙️ Opções Completas

```bash
RichardGoLine --help
```

| Opção | Descrição |
|-------|-----------|
| `-o, --output` | Diretório de saída |
| `--output-template` | Template nome arquivo (`%%(title)s.%%(ext)s`) |
| `-a, --audio-only` | Apenas áudio (melhor qualidade) |
| `--video-only` | Apenas vídeo (sem áudio) |
| `-f, --format` | Formato específico (ex: `313+251`) |
| `--list-formats` | Lista formatos e sai |
| `--extract-audio` | Extrai áudio do vídeo |
| `--audio-format` | mp3, m4a, opus, flac, wav, vorbis, aac |
| `--audio-quality` | 0=melhor ... 10=pior |
| `--merge-format` | mkv, mp4, webm, mov |
| `-s, --subtitles` | Baixar legendas |
| `--sub-langs` | Idiomas (ex: pt,en,es) |
| `-t, --thumbnail` | Baixar thumbnail |
| `-m, --metadata` | Metadados + embed thumbnail |
| `--sponsorblock` | Remove patrocínios |
| `--concurrent-fragments` | Fragments paralelos (1-16) |
| `--throttle` | Limite velocidade (ex: 5M) |
| `--retries` | Tentativas (padrão: 10) |
| `--ignore-errors` | Ignorar erros |
| `--playlist-items` | Itens playlist (1,3,5-10) |
| `--playlist-start` | Iniciar no item N |
| `--playlist-end` | Terminar no item N |
| `--date-after` | Após data (YYYYMMDD) |
| `--date-before` | Antes da data (YYYYMMDD) |
| `--batch` | Arquivo com URLs |
| `-v, --verbose` | Verboso |

## 🎯 Formatos Populares (YouTube)

| ID | Resolução | Codec | Tipo |
|----|-----------|-------|------|
| 313 | 2160p 4K | VP9 | Vídeo |
| 308 | 2160p 4K | AV1 | Vídeo |
| 271 | 1440p | VP9 | Vídeo |
| 248 | 1080p | VP9 | Vídeo |
| 137 | 1080p | AVC | Vídeo |
| 247 | 720p | VP9 | Vídeo |
| 136 | 720p | AVC | Vídeo |
| 251 | ~160kbps | Opus | Áudio |
| 140 | ~128kbps | AAC | Áudio |

**Melhor combinação qualidade**: `-f "313+251"` (4K VP9 + Opus) ou `-f "308+251"` (4K AV1 + Opus)

**Melhor combinação compatibilidade**: `-f "137+140"` (1080p AVC + AAC) → MP4

## 📦 Batch Processing

Crie um arquivo `urls.txt`:
```txt
# Comentários são ignorados
https://youtube.com/watch?v=video1
https://youtube.com/watch?v=video2
https://youtube.com/playlist?list=PL...
https://youtube.com/watch?v=video3
```

Execute:
```bash
RichardGoLine --batch urls.txt -a -m --sponsorblock
```

## 🔧 Requisitos

- Python 3.8+
- `yt-dlp` (instalado via pip ou gerenciador de pacotes)
- `ffmpeg` (para merge de vídeo+áudio e conversão de áudio)

```bash
# Fedora/RHEL
sudo dnf install yt-dlp ffmpeg

# Ubuntu/Debian
sudo apt install yt-dlp ffmpeg

# Arch
sudo pacman -S yt-dlp ffmpeg

# macOS
brew install yt-dlp ffmpeg
```

## 📁 Estrutura de Saída Padrão

```
~/Videos/YouTube/
├── "Título do Vídeo [videoID].mkv"          # Vídeo + Áudio mergeado
├── "Título do Vídeo [videoID].mp3"          # Apenas áudio
├── "Título do Vídeo [videoID].pt.vtt"       # Legendas PT
├── "Título do Vídeo [videoID].en.vtt"       # Legendas EN
└── "Título do Vídeo [videoID].jpg"          # Thumbnail
```

Com `--metadata -t`, o arquivo final tem:
- ✅ Título, artista, álbum, data
- ✅ Thumbnail embedded
- ✅ Capítulos (se disponível)
- ✅ Metadados completos para players

## 🎯 Dicas de Performance

1. **Máxima velocidade**: `--concurrent-fragments 16`
2. **SSD/NVMe**: Use `--concurrent-fragments 16` sem throttle
3. **HDD/Redes lentas**: Use `--throttle "5M" --concurrent-fragments 4`
4. **Muitos arquivos**: Use `--batch urls.txt --ignore-errors`
5. **Apenas áudio**: `-a` é muito mais rápido (menos dados)

## 🐛 Troubleshooting

```bash
# yt-dlp não encontrado
pip install --upgrade yt-dlp

# Erro de merge (ffmpeg)
sudo dnf install ffmpeg  # ou apt/pacman/brew

# Erro 403/429 (rate limit)
RichardGoLine --throttle "1M" --retries 20 "URL"

# Legendas não baixam
RichardGoLine -s --sub-langs "pt,en" --verbose "URL"

# Formato não disponível
RichardGoLine --list-formats "URL"  # Veja IDs disponíveis
```

## 📝 Licença

MIT License - Use livremente!

## 🤝 Contribuições

PRs bem-vindos! Reporte issues ou sugira melhorias.

---

**RichardGoLine** - Feito para velocidade e qualidade máxima 🚀