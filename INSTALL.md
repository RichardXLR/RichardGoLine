# Instalação do RichardGoLine

## Instalação Rápida (Recomendado)

```bash
# 1. Instalar dependências
python3 -m pip install yt-dlp --user

# 2. Adicionar ao PATH (opcional)
echo 'export PATH="$PATH:/var/mnt/hd/projetos/YT"' >> ~/.bashrc
source ~/.bashrc

# 3. Testar
RichardGoLine --help
RichardGoLine "https://youtube.com/watch?v=..."
```

## Instalação como Comando Global (Opcional)

```bash
# Criar symlink em ~/.local/bin (já no PATH na maioria das distros)
mkdir -p ~/.local/bin
ln -sf /var/mnt/hd/projetos/YT/RichardGoLine ~/.local/bin/RichardGoLine

# Verificar
RichardGoLine --help
```

## Instalação via pipx (Isolado)

```bash
pipx install git+file:///var/mnt/hd/projetos/YT
# ou se tiver setup.py
pipx install /var/mnt/hd/projetos/YT
```

## Verificar Instalação

```bash
# Verifica dependências
RichardGoLine --list-formats "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Teste download áudio
RichardGoLine -a "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Teste download vídeo
RichardGoLine "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

## Dependências Necessárias

| Pacote | Comando Instalação |
|--------|-------------------|
| yt-dlp | `pip install yt-dlp --user` ou `dnf install yt-dlp` |
| ffmpeg | `dnf install ffmpeg` / `apt install ffmpeg` / `brew install ffmpeg` |
| python3 | Já incluso na maioria das distros |

## Estrutura do Projeto

```
/var/mnt/hd/projetos/YT/
├── RichardGoLine.py      # Script principal Python
├── RichardGoLine         # Wrapper bash executável
├── README.md             # Documentação completa
├── INSTALL.md            # Este arquivo
└── urls_teste.txt        # Exemplo arquivo batch
```

## Uso Diário

```bash
# Baixar música (MP3 320kbps)
RichardGoLine -a "https://youtube.com/watch?v=..."

# Baixar vídeo 4K máximo qualidade
RichardGoLine -f "313+251" --merge-format mkv "https://youtube.com/watch?v=..."

# Playlist com SponsorBlock (remove patrocínios)
RichardGoLine --sponsorblock "https://youtube.com/playlist?list=..."

# Batch de URLs
RichardGoLine --batch urls.txt -a --sponsorblock

# Apenas listar formatos
RichardGoLine --list-formats "https://youtube.com/watch?v=..."
```