#!/usr/bin/env python3
"""
RichardGoLine - YouTube Downloader com máxima qualidade e velocidade
Um downloader CLI ultra-rápido para YouTube usando yt-dlp
"""

import argparse
import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class RichardGoLine:
    def __init__(self, output_dir: str = ".", max_concurrent: int = 4):
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        
    def check_dependencies(self) -> bool:
        """Verifica se yt-dlp e ffmpeg estão instalados"""
        deps = {
            'yt-dlp': ['yt-dlp', '--version'],
            'ffmpeg': ['ffmpeg', '-version']
        }
        
        missing = []
        for name, cmd in deps.items():
            try:
                subprocess.run(cmd, capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(name)
        
        if missing:
            print(f"❌ Dependências faltando: {', '.join(missing)}")
            print("   Instale com: pip install yt-dlp && sudo apt install ffmpeg")
            return False
        return True
    
    def get_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """Obtém todos os formatos disponíveis para o vídeo"""
        cmd = ['yt-dlp', '-J', '--no-warnings', url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return info.get('formats', [])
        except Exception as e:
            print(f"❌ Erro ao obter formatos: {e}")
            return []
    
    def list_formats(self, url: str) -> None:
        """Lista todos os formatos disponíveis de forma organizada"""
        formats = self.get_available_formats(url)
        
        if not formats:
            print("Nenhum formato encontrado")
            return
        
        print(f"\n{'ID':<10} {'Ext':<6} {'Resolução':<15} {'Codec':<20} {'Tamanho':<12} {'Tipo':<10} {'Nota'}")
        print("─" * 95)
        
        video_formats = []
        audio_formats = []
        
        for f in formats:
            fmt_id = f.get('format_id', 'N/A')
            ext = f.get('ext', 'N/A')
            resolution = f.get('resolution', 'audio only')
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            filesize = f.get('filesize') or f.get('filesize_approx', 0)
            note = f.get('format_note', '')
            
            # Formatar tamanho
            if filesize:
                if filesize > 1024**3:
                    size_str = f"{filesize/1024**3:.1f}GB"
                elif filesize > 1024**2:
                    size_str = f"{filesize/1024**2:.1f}MB"
                else:
                    size_str = f"{filesize/1024:.1f}KB"
            else:
                size_str = "Desconhecido"
            
            # Determinar tipo
            if vcodec != 'none' and acodec != 'none':
                fmt_type = "Vídeo+Áudio"
            elif vcodec != 'none':
                fmt_type = "Apenas Vídeo"
            else:
                fmt_type = "Apenas Áudio"
            
            codec_str = f"{vcodec}/{acodec}" if vcodec != 'none' else acodec
            
            row = f"{fmt_id:<10} {ext:<6} {resolution:<15} {codec_str:<20} {size_str:<12} {fmt_type:<10} {note}"
            
            if vcodec != 'none':
                video_formats.append(row)
            else:
                audio_formats.append(row)
        
        if video_formats:
            print("\n📹 FORMATOS DE VÍDEO:")
            for row in video_formats:
                print(row)
        
        if audio_formats:
            print("\n🎵 FORMATOS DE ÁUDIO:")
            for row in audio_formats:
                print(row)
    
    def build_ydl_cmd(self, url: str, args: argparse.Namespace) -> List[str]:
        """Constrói o comando yt-dlp baseado nos argumentos"""
        cmd = ['yt-dlp']
        
        # Diretório de saída
        cmd.extend(['-P', str(self.output_dir)])
        
        # Template de nome do arquivo
        if args.output_template:
            cmd.extend(['-o', args.output_template])
        else:
            cmd.extend(['-o', '%(title)s [%(id)s].%(ext)s'])
        
        # Seleção de formato
        if args.format:
            cmd.extend(['-f', args.format])
        elif args.audio_only:
            # Melhor áudio disponível
            cmd.extend(['-f', 'bestaudio/best'])
        elif args.video_only:
            # Melhor vídeo sem áudio
            cmd.extend(['-f', 'bestvideo/best'])
        else:
            # Melhor qualidade combinada (vídeo + áudio)
            cmd.extend(['-f', 'bestvideo+bestaudio/best'])
        
        # Merge para combinar vídeo+áudio
        if not args.audio_only and not args.video_only and not args.format:
            cmd.extend(['--merge-output-format', args.merge_format or 'mkv'])
        
        # Pós-processamento de áudio
        if args.audio_only or args.extract_audio:
            cmd.extend(['-x', '--audio-format', args.audio_format or 'mp3'])
            if args.audio_quality:
                cmd.extend(['--audio-quality', args.audio_quality])
        
        # Legendas
        if args.subtitles:
            cmd.extend(['--write-subs', '--write-auto-subs'])
            if args.sub_langs:
                cmd.extend(['--sub-langs', args.sub_langs])
        
        # Thumbnail
        if args.thumbnail:
            cmd.extend(['--write-thumbnail'])
        
        # Metadados
        if args.metadata:
            cmd.extend(['--add-metadata', '--embed-thumbnail'])
        
        # Patrocinadores (SponsorBlock)
        if args.sponsorblock:
            cmd.extend(['--sponsorblock-remove', 'all'])
        
        # Velocidade e conexões
        cmd.extend(['--concurrent-fragments', str(args.concurrent_fragments)])
        if args.throttle:
            cmd.extend(['--throttled-rate', args.throttle])
        
        # Retry
        cmd.extend(['--retries', str(args.retries)])
        cmd.extend(['--fragment-retries', str(args.fragment_retries)])
        
        # Ignorar erros
        if args.ignore_errors:
            cmd.append('--ignore-errors')
        
        # No warnings
        cmd.append('--no-warnings')
        
        # Verbose
        if args.verbose:
            cmd.append('-v')
        
        # Playlist
        if args.playlist_items:
            cmd.extend(['--playlist-items', args.playlist_items])
        if args.playlist_start:
            cmd.extend(['--playlist-start', str(args.playlist_start)])
        if args.playlist_end:
            cmd.extend(['--playlist-end', str(args.playlist_end)])
        
        # Data
        if args.date_after:
            cmd.extend(['--dateafter', args.date_after])
        if args.date_before:
            cmd.extend(['--datebefore', args.date_before])
        
        # URL final
        cmd.append(url)
        
        return cmd
    
    def download(self, url: str, args: argparse.Namespace) -> int:
        """Executa o download"""
        if not self.check_dependencies():
            return 1
        
        cmd = self.build_ydl_cmd(url, args)
        
        print(f"🚀 RichardGoLine - Iniciando download...")
        print(f"📁 Diretório: {self.output_dir}")
        print(f"🔗 URL: {url}")
        print(f"⚡ Comando: {' '.join(cmd)}")
        print("─" * 60)
        
        try:
            result = subprocess.run(cmd, check=True)
            print("─" * 60)
            print("✅ Download concluído com sucesso!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no download (código {e.returncode})")
            return e.returncode
        except KeyboardInterrupt:
            print("\n⏹️  Download cancelado pelo usuário")
            return 130
    
    def download_batch(self, urls: List[str], args: argparse.Namespace) -> int:
        """Baixa múltiplas URLs"""
        failed = 0
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Baixando: {url}")
            if self.download(url, args) != 0:
                failed += 1
        
        if failed:
            print(f"\n⚠️  {failed} de {len(urls)} downloads falharam")
            return 1
        return 0


def main():
    parser = argparse.ArgumentParser(
        prog='RichardGoLine',
        description='🚀 RichardGoLine - YouTube Downloader Ultra-Rápido com Máxima Qualidade',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Melhor qualidade (vídeo + áudio)
  RichardGoLine.py "https://youtube.com/watch?v=..."
  
  # Apenas áudio MP3 320kbps
  RichardGoLine.py -a "https://youtube.com/watch?v=..."
  
  # Apenas áudio em formato específico
  RichardGoLine.py -a --audio-format opus --audio-quality 0 "https://youtube.com/watch?v=..."
  
  # Lista formatos disponíveis
  RichardGoLine.py --list-formats "https://youtube.com/watch?v=..."
  
  # Formato específico por ID
  RichardGoLine.py -f "248+251" "https://youtube.com/watch?v=..."
  
  # Playlist completa com SponsorBlock
  RichardGoLine.py --sponsorblock "https://youtube.com/playlist?list=..."
  
  # Múltiplas URLs de arquivo
  RichardGoLine.py --batch urls.txt
  
  # Diretório de saída personalizado
  RichardGoLine.py -o ~/Videos/YouTube "https://youtube.com/watch?v=..."
        """
    )
    
    # Argumentos principais
    parser.add_argument('urls', nargs='*', help='URL(s) do YouTube para baixar')
    parser.add_argument('-o', '--output', dest='output_dir', default='.', 
                        help='Diretório de saída (padrão: pasta atual)')
    parser.add_argument('--output-template', dest='output_template',
                        help='Template do nome do arquivo (ex: %%(title)s.%%(ext)s)')
    
    # Modo de operação
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--audio-only', action='store_true',
                       help='Baixar apenas áudio (melhor qualidade)')
    group.add_argument('--video-only', action='store_true',
                       help='Baixar apenas vídeo (sem áudio)')
    group.add_argument('-f', '--format', dest='format',
                       help='Formato específico (ex: "248+251", "bestvideo+bestaudio")')
    group.add_argument('--list-formats', action='store_true',
                       help='Listar todos os formatos disponíveis e sair')
    
    # Áudio
    parser.add_argument('--extract-audio', action='store_true',
                        help='Extrair áudio do vídeo baixado')
    parser.add_argument('--audio-format', choices=['mp3', 'm4a', 'opus', 'flac', 'wav', 'vorbis', 'aac'],
                        default='mp3', help='Formato de áudio (padrão: mp3)')
    parser.add_argument('--audio-quality', 
                        help='Qualidade do áudio (ex: 0=melhor, 5=padrão, 10=pior)')
    
    # Vídeo
    parser.add_argument('--merge-format', choices=['mkv', 'mp4', 'webm', 'mov'],
                        default='mkv', help='Formato de merge vídeo+áudio (padrão: mkv)')
    
    # Legendas
    parser.add_argument('-s', '--subtitles', action='store_true',
                        help='Baixar legendas')
    parser.add_argument('--sub-langs', help='Idiomas das legendas (ex: "pt,en,es")')
    
    # Extras
    parser.add_argument('-t', '--thumbnail', action='store_true',
                        help='Baixar thumbnail')
    parser.add_argument('-m', '--metadata', action='store_true',
                        help='Adicionar metadados e embed thumbnail')
    parser.add_argument('--sponsorblock', action='store_true',
                        help='Remover segmentos de patrocínio (SponsorBlock)')
    
    # Performance
    parser.add_argument('--concurrent-fragments', type=int, default=4,
                        help='Fragments simultâneos (padrão: 4, max: 16)')
    parser.add_argument('--throttle', help='Limitar velocidade (ex: "1M", "500K")')
    parser.add_argument('--retries', type=int, default=10, help='Tentativas de retry (padrão: 10)')
    parser.add_argument('--fragment-retries', type=int, default=10, help='Retries de fragments (padrão: 10)')
    parser.add_argument('--ignore-errors', action='store_true', help='Ignorar erros e continuar')
    
    # Playlist
    parser.add_argument('--playlist-items', help='Itens da playlist (ex: "1,3,5-10")')
    parser.add_argument('--playlist-start', type=int, help='Iniciar no item N')
    parser.add_argument('--playlist-end', type=int, help='Terminar no item N')
    
    # Data
    parser.add_argument('--date-after', help='Baixar apenas após data (YYYYMMDD)')
    parser.add_argument('--date-before', help='Baixar apenas antes da data (YYYYMMDD)')
    
    # Batch
    parser.add_argument('--batch', dest='batch_file',
                        help='Arquivo com URLs (uma por linha)')
    
    # Verbose
    parser.add_argument('-v', '--verbose', action='store_true', help='Saída verbosa')
    
    # Versão
    parser.add_argument('--version', action='version', version='RichardGoLine 1.0.0')
    
    args = parser.parse_args()
    
    # Validar concurrent fragments
    if args.concurrent_fragments > 16:
        args.concurrent_fragments = 16
        print("⚠️  Limitando concurrent-fragments a 16 (máximo do yt-dlp)")
    
    # Criar instância
    downloader = RichardGoLine(output_dir=args.output_dir)
    
    # Coletar URLs
    urls = list(args.urls)
    
    # Batch file
    if args.batch_file:
        try:
            with open(args.batch_file, 'r') as f:
                batch_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                urls.extend(batch_urls)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {args.batch_file}")
            return 1
    
    if not urls and not args.list_formats:
        parser.print_help()
        return 1
    
    # Se list-formats, usar primeira URL
    if args.list_formats:
        if not urls:
            print("❌ Forneça uma URL para listar formatos")
            return 1
        downloader.list_formats(urls[0])
        return 0
    
    # Download
    if len(urls) == 1:
        return downloader.download(urls[0], args)
    else:
        return downloader.download_batch(urls, args)


if __name__ == '__main__':
    sys.exit(main())