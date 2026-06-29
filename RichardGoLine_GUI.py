#!/usr/bin/env python3
"""
RichardGoLine GUI - Interface Gráfica Moderna (PyQt6)
YouTube Downloader Ultra-Rápido com Máxima Qualidade
"""

import sys
import os
import subprocess
import threading
import queue
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QSpinBox, QFileDialog, QProgressBar, QTextEdit, QGroupBox,
    QRadioButton, QButtonGroup, QGridLayout, QFormLayout, QScrollArea,
    QMessageBox, QFrame, QSizePolicy, QSpacerItem, QStyle,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QSettings
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QTextCursor, QAction,
    QDesktopServices
)
from PyQt6.QtMultimedia import QSoundEffect


class FormatDialog(QDialog):
    """Diálogo para mostrar formatos disponíveis"""
    
    def __init__(self, parent, formats: List[Dict]):
        super().__init__(parent)
        self.setWindowTitle("Formatos Disponíveis")
        self.setMinimumSize(800, 600)
        self.formats = formats
        self.selected_format = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filtro
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Digite para filtrar (ex: 1080p, opus, 4k)...")
        self.filter_edit.textChanged.connect(self.filter_list)
        filter_layout.addWidget(self.filter_edit)
        layout.addLayout(filter_layout)
        
        # Lista
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemDoubleClicked.connect(self.accept_format)
        layout.addWidget(self.list_widget)
        
        # Preencher lista
        self.populate_list()
        
        # Botões
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept_format)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def populate_list(self):
        self.list_widget.clear()
        for f in self.formats:
            fmt_id = f.get('format_id', 'N/A')
            ext = f.get('ext', 'N/A')
            resolution = f.get('resolution', 'audio only')
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            filesize = f.get('filesize') or f.get('filesize_approx', 0)
            note = f.get('format_note', '')
            
            if filesize:
                if filesize > 1024**3:
                    size_str = f"{filesize/1024**3:.1f}GB"
                elif filesize > 1024**2:
                    size_str = f"{filesize/1024**2:.1f}MB"
                else:
                    size_str = f"{filesize/1024:.1f}KB"
            else:
                size_str = "?"
            
            if vcodec != 'none' and acodec != 'none':
                type_str = "📹 Vídeo+Áudio"
            elif vcodec != 'none':
                type_str = "🎬 Apenas Vídeo"
            else:
                type_str = "🎵 Apenas Áudio"
            
            codec_str = f"{vcodec}/{acodec}" if vcodec != 'none' else acodec
            
            text = f"[{fmt_id:>8}] {ext:>5} | {resolution:<15} | {codec_str:<20} | {size_str:>8} | {type_str}"
            if note:
                text += f" | {note}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, fmt_id)
            self.list_widget.addItem(item)
            
    def filter_list(self, text: str):
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())
            
    def accept_format(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_format = item.data(Qt.ItemDataRole.UserRole)
            self.accept()


class DownloadWorker(QThread):
    """Worker thread para downloads"""
    
    log_signal = pyqtSignal(str, str)  # message, level
    progress_signal = pyqtSignal(str)  # progress text
    finished_signal = pyqtSignal(int, str)  # exit_code, output
    
    def __init__(self, cmd: List[str], cwd: str):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.process = None
        self._cancelled = False
        
    def run(self):
        try:
            self.log_signal.emit(f"🚀 Iniciando: {' '.join(self.cmd)}", "cmd")
            
            self.process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            for line in iter(self.process.stdout.readline, ''):
                if self._cancelled:
                    self.process.terminate()
                    break
                line = line.rstrip()
                output_lines.append(line)
                self.parse_output(line)
                
            self.process.wait()
            exit_code = self.process.returncode
            output = '\n'.join(output_lines)
            
            if exit_code == 0:
                self.log_signal.emit("✅ Download concluído com sucesso!", "success")
            elif self._cancelled:
                self.log_signal.emit("⏹️ Download cancelado pelo usuário", "warning")
            else:
                self.log_signal.emit(f"❌ Erro no download (código {exit_code})", "error")
                
            self.finished_signal.emit(exit_code, output)
            
        except Exception as e:
            self.log_signal.emit(f"❌ Erro: {e}", "error")
            self.finished_signal.emit(-1, str(e))
            
    def parse_output(self, line: str):
        """Parse yt-dlp output for progress"""
        if '[download]' in line and '%' in line:
            self.progress_signal.emit(line)
            self.log_signal.emit(line, "progress")
        elif '[ExtractAudio]' in line or '[Merger]' in line or '[ffmpeg]' in line:
            self.log_signal.emit(line, "info")
        elif 'ERROR:' in line or 'Error:' in line:
            self.log_signal.emit(line, "error")
        elif 'WARNING:' in line:
            self.log_signal.emit(line, "warning")
        elif line.strip() and not line.startswith('['):
            self.log_signal.emit(line, "info")
            
    def cancel(self):
        self._cancelled = True
        if self.process:
            self.process.terminate()


class RichardGoLineGUI(QMainWindow):
    """Janela principal do RichardGoLine GUI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 RichardGoLine - YouTube Downloader Ultra-Rápido")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        
        # Estado
        self.worker: Optional[DownloadWorker] = None
        self.output_dir = str(Path.home() / "Videos" / "YouTube")
        self.settings = QSettings("RichardGoLine", "RichardGoLineGUI")
        
        # Carregar configurações
        self.load_settings()
        
        # Setup UI
        self.setup_ui()
        self.apply_theme()
        self.check_dependencies()
        
    def setup_ui(self):
        # Widget central com tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Aba 1: Download Principal
        self.tab_main = QWidget()
        self.tabs.addTab(self.tab_main, "📥 Download")
        self.build_main_tab()
        
        # Aba 2: Avançado
        self.tab_advanced = QWidget()
        self.tabs.addTab(self.tab_advanced, "⚙️ Avançado")
        self.build_advanced_tab()
        
        # Aba 3: Log
        self.tab_log = QWidget()
        self.tabs.addTab(self.tab_log, "📋 Log")
        self.build_log_tab()
        
        # Status bar
        self.statusBar().showMessage("✅ Pronto - RichardGoLine carregado")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.statusBar().addPermanentWidget(self.progress_bar, 1)
        
        # Menu
        self.create_menu()
        
    def create_menu(self):
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu("📁 Arquivo")
        file_menu.addAction("📂 Abrir Pasta de Download", self.open_output_folder)
        file_menu.addAction("🗑️ Limpar Log", self.clear_log)
        file_menu.addSeparator()
        file_menu.addAction("❌ Sair", self.close)
        
        # Menu Ferramentas
        tools_menu = menubar.addMenu("🔧 Ferramentas")
        tools_menu.addAction("📋 Ver Formatos (URL atual)", self.show_formats_dialog)
        tools_menu.addAction("🔍 Verificar Atualizações yt-dlp", self.check_yt_dlp_update)
        tools_menu.addAction("⚙️ Configurações", self.show_settings)
        
        # Menu Ajuda
        help_menu = menubar.addMenu("❓ Ajuda")
        help_menu.addAction("📖 Documentação", self.show_docs)
        help_menu.addAction("🐛 Reportar Bug", self.report_bug)
        help_menu.addAction("ℹ️ Sobre", self.show_about)
        
    def build_main_tab(self):
        layout = QVBoxLayout(self.tab_main)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel("🚀 RichardGoLine")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a73e8;")
        layout.addWidget(title)
        
        subtitle = QLabel("YouTube Downloader - Máxima Qualidade & Velocidade Ultra")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)
        
        # URL Section
        url_group = QGroupBox("🔗 URL do YouTube")
        url_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        url_layout = QVBoxLayout(url_group)
        
        url_input_layout = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Cole aqui: https://youtube.com/watch?v=... | https://youtube.com/playlist?list=... | https://youtu.be/...")
        self.url_edit.setFont(QFont("Segoe UI", 11))
        self.url_edit.returnPressed.connect(self.start_download)
        url_input_layout.addWidget(self.url_edit)
        
        paste_btn = QPushButton("📋 Colar")
        paste_btn.clicked.connect(self.paste_url)
        paste_btn.setFixedWidth(100)
        url_input_layout.addWidget(paste_btn)
        url_layout.addLayout(url_input_layout)
        
        url_hint = QLabel("💡 Suporta: vídeos, playlists, canais, Shorts, Music, URLs encurtadas (youtu.be)")
        url_hint.setStyleSheet("color: #666; font-size: 11px;")
        url_layout.addWidget(url_hint)
        layout.addWidget(url_group)
        
        # Modo de Download
        mode_group = QGroupBox("🎯 Modo de Download")
        mode_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        mode_layout = QGridLayout(mode_group)
        
        self.mode_group = QButtonGroup(self)
        self.mode_best = QRadioButton("🎬 Vídeo + Áudio (Máxima Qualidade)")
        self.mode_audio = QRadioButton("🎵 Apenas Áudio (MP3/Opus/FLAC...)")
        self.mode_video = QRadioButton("📹 Apenas Vídeo (Sem Áudio)")
        self.mode_custom = QRadioButton("🎯 Formato Específico (ID)")
        
        self.mode_best.setChecked(True)
        for btn in [self.mode_best, self.mode_audio, self.mode_video, self.mode_custom]:
            self.mode_group.addButton(btn)
            btn.toggled.connect(self.on_mode_changed)
            
        mode_layout.addWidget(self.mode_best, 0, 0)
        mode_layout.addWidget(self.mode_audio, 0, 1)
        mode_layout.addWidget(self.mode_video, 1, 0)
        mode_layout.addWidget(self.mode_custom, 1, 1)
        layout.addWidget(mode_group)
        
        # Opções específicas por modo
        self.custom_format_frame = QFrame()
        custom_layout = QHBoxLayout(self.custom_format_frame)
        custom_layout.addWidget(QLabel("Format ID:"))
        self.custom_format_edit = QLineEdit()
        self.custom_format_edit.setPlaceholderText("Ex: 313+251 (4K VP9 + Opus) | 137+140 (1080p AVC + AAC)")
        custom_layout.addWidget(self.custom_format_edit)
        self.btn_formats = QPushButton("📋 Ver Formatos")
        self.btn_formats.clicked.connect(self.show_formats_dialog)
        custom_layout.addWidget(self.btn_formats)
        self.custom_format_frame.hide()
        layout.addWidget(self.custom_format_frame)
        
        # Opções de Áudio
        self.audio_options_frame = QGroupBox("🎵 Opções de Áudio")
        self.audio_options_frame.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        audio_layout = QFormLayout(self.audio_options_frame)
        
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "opus", "flac", "m4a", "wav", "vorbis", "aac"])
        self.audio_format_combo.setCurrentText("mp3")
        audio_layout.addRow("Formato:", self.audio_format_combo)
        
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["0 (melhor)", "1", "2", "3", "4", "5 (padrão)", "6", "7", "8", "9", "10 (pior)"])
        self.audio_quality_combo.setCurrentText("0 (melhor)")
        audio_layout.addRow("Qualidade:", self.audio_quality_combo)
        
        self.audio_options_frame.hide()
        layout.addWidget(self.audio_options_frame)
        
        # Opções de Vídeo (merge)
        self.video_options_frame = QGroupBox("🎬 Opções de Vídeo")
        self.video_options_frame.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        video_layout = QFormLayout(self.video_options_frame)
        
        self.merge_format_combo = QComboBox()
        self.merge_format_combo.addItems(["mkv", "mp4", "webm", "mov"])
        self.merge_format_combo.setCurrentText("mkv")
        video_layout.addRow("Merge Format:", self.merge_format_combo)
        
        layout.addWidget(self.video_options_frame)
        
        # Diretório de saída
        output_group = QGroupBox("📁 Diretório de Saída")
        output_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        output_layout = QHBoxLayout(output_group)
        
        self.output_edit = QLineEdit(self.output_dir)
        self.output_edit.setFont(QFont("Segoe UI", 10))
        output_layout.addWidget(self.output_edit)
        
        browse_btn = QPushButton("📂 Escolher")
        browse_btn.clicked.connect(self.choose_output_dir)
        browse_btn.setFixedWidth(120)
        output_layout.addWidget(browse_btn)
        layout.addWidget(output_group)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_download = QPushButton("🚀 BAIXAR AGORA")
        self.btn_download.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_download.setMinimumHeight(45)
        self.btn_download.setMinimumWidth(200)
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #1557b0; }
            QPushButton:pressed { background-color: #0d47a1; }
            QPushButton:disabled { background-color: #ccc; color: #888; }
        """)
        self.btn_download.clicked.connect(self.start_download)
        btn_layout.addWidget(self.btn_download)
        
        self.btn_cancel = QPushButton("⏹️ Cancelar")
        self.btn_cancel.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_cancel.setMinimumHeight(45)
        self.btn_cancel.setMinimumWidth(140)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_download)
        btn_layout.addWidget(self.btn_cancel)
        
        formats_btn = QPushButton("📋 Ver Formatos")
        formats_btn.setFont(QFont("Segoe UI", 11))
        formats_btn.setMinimumHeight(45)
        formats_btn.clicked.connect(self.show_formats_dialog)
        btn_layout.addWidget(formats_btn)
        
        clear_btn = QPushButton("🗑️ Limpar Log")
        clear_btn.setFont(QFont("Segoe UI", 11))
        clear_btn.setMinimumHeight(45)
        clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
    def build_advanced_tab(self):
        # Scroll area para muitas opções
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Extras
        extras_group = QGroupBox("✨ Extras")
        extras_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        extras_layout = QVBoxLayout(extras_group)
        
        self.sponsorblock_check = QCheckBox("🚫 SponsorBlock - Remover patrocínios/intros/outros automaticamente")
        self.sponsorblock_check.setChecked(True)
        extras_layout.addWidget(self.sponsorblock_check)
        
        self.subtitles_check = QCheckBox("📝 Baixar Legendas")
        self.subtitles_check.toggled.connect(self.toggle_sub_langs)
        extras_layout.addWidget(self.subtitles_check)
        
        self.sub_langs_frame = QWidget()
        sub_langs_layout = QHBoxLayout(self.sub_langs_frame)
        sub_langs_layout.setContentsMargins(20, 0, 0, 0)
        sub_langs_layout.addWidget(QLabel("Idiomas:"))
        self.sub_langs_edit = QLineEdit("pt,en,es")
        self.sub_langs_edit.setPlaceholderText("ex: pt,en,es,fr,de")
        sub_langs_layout.addWidget(self.sub_langs_edit)
        self.sub_langs_frame.hide()
        extras_layout.addWidget(self.sub_langs_frame)
        
        self.thumbnail_check = QCheckBox("🖼️ Baixar Thumbnail")
        extras_layout.addWidget(self.thumbnail_check)
        
        self.metadata_check = QCheckBox("🏷️ Embed Metadados + Thumbnail no arquivo")
        extras_layout.addWidget(self.metadata_check)
        
        self.ignore_errors_check = QCheckBox("⚠️ Ignorar erros e continuar (útil para playlists)")
        extras_layout.addWidget(self.ignore_errors_check)
        
        self.verbose_check = QCheckBox("🔍 Verbose (log detalhado)")
        extras_layout.addWidget(self.verbose_check)
        
        layout.addWidget(extras_group)
        
        # Performance
        perf_group = QGroupBox("⚡ Performance")
        perf_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        perf_layout = QFormLayout(perf_group)
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 16)
        self.concurrent_spin.setValue(4)
        self.concurrent_spin.setToolTip("Fragments paralelos (1-16). Mais = mais rápido, mas mais CPU/RAM")
        perf_layout.addRow("Fragments Paralelos:", self.concurrent_spin)
        
        self.throttle_edit = QLineEdit()
        self.throttle_edit.setPlaceholderText("Ex: 5M, 10M, 500K (vazio = ilimitado)")
        self.throttle_edit.setToolTip("Limite de velocidade de download")
        perf_layout.addRow("Limite Velocidade:", self.throttle_edit)
        
        layout.addWidget(perf_group)
        
        # Playlist/Filtros
        pl_group = QGroupBox("📋 Playlist / Filtros")
        pl_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        pl_layout = QFormLayout(pl_group)
        
        self.pl_items_edit = QLineEdit()
        self.pl_items_edit.setPlaceholderText("Ex: 1,3,5-10")
        pl_layout.addRow("Itens:", self.pl_items_edit)
        
        self.pl_start_edit = QLineEdit()
        self.pl_start_edit.setPlaceholderText("Número do item inicial")
        pl_layout.addRow("Iniciar em:", self.pl_start_edit)
        
        self.pl_end_edit = QLineEdit()
        self.pl_end_edit.setPlaceholderText("Número do item final")
        pl_layout.addRow("Terminar em:", self.pl_end_edit)
        
        self.date_after_edit = QLineEdit()
        self.date_after_edit.setPlaceholderText("YYYYMMDD (ex: 20240101)")
        pl_layout.addRow("Após data:", self.date_after_edit)
        
        self.date_before_edit = QLineEdit()
        self.date_before_edit.setPlaceholderText("YYYYMMDD (ex: 20241231)")
        pl_layout.addRow("Antes da data:", self.date_before_edit)
        
        layout.addWidget(pl_group)
        
        # Template
        template_group = QGroupBox("📝 Template Nome do Arquivo")
        template_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        template_layout = QVBoxLayout(template_group)
        
        self.template_edit = QLineEdit("%(title)s [%(id)s].%(ext)s")
        template_layout.addWidget(self.template_edit)
        
        template_help = QLabel("Variáveis: %(title)s %(id)s %(ext)s %(uploader)s %(upload_date)s %(resolution)s %(height)s %(width)s %(fps)s %(vcodec)s %(acodec)s")
        template_help.setStyleSheet("color: #666; font-size: 11px;")
        template_help.setWordWrap(True)
        template_layout.addWidget(template_help)
        
        layout.addWidget(template_group)
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self.tab_advanced)
        main_layout.addWidget(scroll)
        
    def build_log_tab(self):
        layout = QVBoxLayout(self.tab_log)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Limpar")
        clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_btn)
        
        save_btn = QPushButton("💾 Salvar Log")
        save_btn.clicked.connect(self.save_log)
        toolbar.addWidget(save_btn)
        
        copy_btn = QPushButton("📋 Copiar Tudo")
        copy_btn.clicked.connect(self.copy_log)
        toolbar.addWidget(copy_btn)
        
        toolbar.addStretch()
        
        self.log_filter_combo = QComboBox()
        self.log_filter_combo.addItems(["Todos", "Info", "Sucesso", "Aviso", "Erro", "Progresso", "Comando"])
        self.log_filter_combo.currentTextChanged.connect(self.filter_log)
        toolbar.addWidget(QLabel("Filtrar:"))
        toolbar.addWidget(self.log_filter_combo)
        
        layout.addLayout(toolbar)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #e0e0e0;
                border: 2px solid #3d3d3d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Log inicial
        self.log("🚀 RichardGoLine GUI iniciado", "success")
        self.log(f"📁 Pasta padrão: {self.output_dir}", "info")
        self.log("✅ Pronto para downloads", "info")
        
    def apply_theme(self):
            """Aplica tema escuro moderno com alto contraste"""
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #3d3d3d;
                    border-radius: 8px;
                    margin-top: 14px;
                    padding-top: 12px;
                    background-color: #252526;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: #4fc3f7;
                    background-color: #252526;
                }
                QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {
                    background-color: #1e1e1e;
                    border: 2px solid #3d3d3d;
                    border-radius: 6px;
                    padding: 8px;
                    color: #ffffff;
                    selection-background-color: #1a73e8;
                    selection-color: #ffffff;
                }
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                    border: 2px solid #1a73e8;
                    background-color: #252526;
                }
                QLineEdit::placeholder, QComboBox::placeholder {
                    color: #888888;
                }
                QPushButton {
                    background-color: #2d2d2d;
                    border: 2px solid #3d3d3d;
                    border-radius: 6px;
                    padding: 10px 18px;
                    font-weight: 600;
                    color: #ffffff;
                    min-height: 20px;
                }
                QPushButton:hover { 
                    background-color: #383838; 
                    border-color: #4fc3f7;
                }
                QPushButton:pressed { 
                    background-color: #1a73e8; 
                    border-color: #1a73e8;
                }
                QPushButton:disabled { 
                    background-color: #1e1e1e; 
                    border-color: #2d2d2d;
                    color: #555555; 
                }
                QRadioButton, QCheckBox {
                    spacing: 10px;
                    color: #ffffff;
                    font-size: 13px;
                }
                QRadioButton::indicator, QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #4fc3f7;
                    border-radius: 4px;
                    background-color: #1e1e1e;
                }
                QRadioButton::indicator:checked {
                    background-color: #1a73e8;
                    border-color: #1a73e8;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3QgeD0iMiIgeT0iMiIgd2lkdGg9IjgiIGhlaWdodD0iOCIgZmlsbD0id2hpdGUiLz4KPC9zdmc+);
                }
                QCheckBox::indicator:checked {
                    background-color: #1a73e8;
                    border-color: #1a73e8;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNkw1IDhMOSAzIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4=);
                }
                QTabWidget::pane {
                    border: 2px solid #3d3d3d;
                    border-radius: 6px;
                    background-color: #252526;
                    top: -1px;
                }
                QTabBar::tab {
                    background-color: #1e1e1e;
                    border: 2px solid #3d3d3d;
                    border-bottom: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    padding: 12px 24px;
                    margin-right: 4px;
                    color: #cccccc;
                    font-weight: 600;
                    min-width: 120px;
                }
                QTabBar::tab:selected {
                    background-color: #252526;
                    border-color: #1a73e8;
                    border-bottom: 2px solid #252526;
                    color: #4fc3f7;
                }
                QTabBar::tab:hover { 
                    background-color: #2d2d2d; 
                    color: #ffffff;
                }
                QTabBar::tab:!selected { margin-top: 2px; }
                QScrollBar:vertical {
                    background-color: #1e1e1e;
                    width: 12px;
                    border-radius: 6px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background-color: #4fc3f7;
                    border-radius: 6px;
                    min-height: 40px;
                    margin: 2px;
                }
                QScrollBar::handle:vertical:hover { background-color: #81d4fa; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
                QProgressBar {
                    border: none;
                    background-color: #2d2d2d;
                    border-radius: 3px;
                    height: 6px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a73e8, stop:1 #4fc3f7);
                    border-radius: 3px;
                }
                QListWidget {
                    background-color: #1e1e1e;
                    border: 2px solid #3d3d3d;
                    border-radius: 6px;
                    alternate-background-color: #252526;
                    color: #ffffff;
                    outline: none;
                }
                QListWidget::item {
                    padding: 8px 12px;
                    border-bottom: 1px solid #2d2d2d;
                }
                QListWidget::item:selected {
                    background-color: #1a73e8;
                    color: #ffffff;
                }
                QListWidget::item:hover {
                    background-color: #2d2d2d;
                }
                QListWidget::item:alternate {
                    background-color: #252526;
                }
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QDialog QLabel {
                    color: #ffffff;
                }
                QDialog QPushButton {
                    min-width: 100px;
                }
                QMessageBox {
                    background-color: #252526;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QComboBox::down-arrow {
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNkw2IDlNOSA2IiBzdHJva2U9IiM0ZmMzZjciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #252526;
                    border: 2px solid #3d3d3d;
                    border-radius: 6px;
                    selection-background-color: #1a73e8;
                    color: #ffffff;
                    outline: none;
                }
                QToolTip {
                    background-color: #2d2d2d;
                    border: 1px solid #4fc3f7;
                    border-radius: 4px;
                    color: #ffffff;
                    padding: 8px;
                }
                QMenu {
                    background-color: #252526;
                    border: 2px solid #3d3d3d;
                    border-radius: 6px;
                    color: #ffffff;
                }
                QMenu::item {
                    padding: 8px 24px;
                }
                QMenu::item:selected {
                    background-color: #1a73e8;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-bottom: 1px solid #3d3d3d;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 16px;
                }
                QMenuBar::item:selected {
                    background-color: #2d2d2d;
                }
                QStatusBar {
                    background-color: #1e1e1e;
                    color: #cccccc;
                    border-top: 1px solid #3d3d3d;
                }
            """)
        
    def load_settings(self):
        self.output_dir = self.settings.value("output_dir", str(Path.home() / "Videos" / "YouTube"))
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
    def save_settings(self):
        self.settings.setValue("output_dir", self.output_dir)
        self.settings.setValue("geometry", self.saveGeometry())
        
    def closeEvent(self, event):
        self.save_settings()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        event.accept()
        
    def check_dependencies(self):
        """Verifica yt-dlp e ffmpeg"""
        missing = []
        
        # yt-dlp
        try:
            result = subprocess.run([sys.executable, '-m', 'yt_dlp', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.log(f"✅ yt-dlp {result.stdout.strip()} encontrado", "success")
            else:
                missing.append("yt-dlp")
        except:
            missing.append("yt-dlp")
            
        # ffmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ver = result.stdout.split('\n')[0]
                self.log(f"✅ {ver}", "success")
            else:
                missing.append("ffmpeg")
        except:
            missing.append("ffmpeg")
            
        if missing:
            self.log(f"❌ Dependências faltando: {', '.join(missing)}", "error")
            self.log("   Instale: pip install yt-dlp && sudo dnf install ffmpeg", "error")
            QMessageBox.warning(self, "Dependências Faltando", 
                f"Faltando: {', '.join(missing)}\n\n"
                "Instale com:\n"
                "  pip install yt-dlp --user\n"
                "  sudo dnf install ffmpeg\n\n"
                "A GUI funcionará mas downloads podem falhar.")
        else:
            self.log("✅ Todas as dependências OK", "success")
            
    def on_mode_changed(self):
        mode = self.get_mode()
        
        self.custom_format_frame.setVisible(mode == "custom")
        self.audio_options_frame.setVisible(mode == "audio")
        self.video_options_frame.setVisible(mode in ["best", "video"])
        
    def get_mode(self) -> str:
        if self.mode_best.isChecked():
            return "best"
        elif self.mode_audio.isChecked():
            return "audio"
        elif self.mode_video.isChecked():
            return "video"
        else:
            return "custom"
            
    def toggle_sub_langs(self, checked: bool):
        self.sub_langs_frame.setVisible(checked)
        
    def paste_url(self):
        clipboard = QApplication.clipboard()
        self.url_edit.setText(clipboard.text())
        
    def choose_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Escolher Pasta de Download", self.output_dir)
        if dir_path:
            self.output_dir = dir_path
            self.output_edit.setText(dir_path)
            
    def open_output_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir))
        
    def start_download(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Necessária", "Cole uma URL do YouTube primeiro!")
            return
            
        # Preparar comando
        cmd = self.build_command(url)
        if not cmd:
            return
            
        # UI state
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.statusBar().showMessage("🔄 Baixando...")
        self.tabs.setCurrentWidget(self.tab_log)
        
        # Log comando
        self.log(f"🚀 Iniciando download...", "success")
        self.log(f"📁 Pasta: {self.output_dir}", "info")
        self.log(f"🔗 URL: {url}", "info")
        self.log(f"⚡ Comando: {' '.join(cmd)}", "cmd")
        
        # Worker thread
        self.worker = DownloadWorker(cmd, self.output_dir)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        
    def build_command(self, url: str) -> List[str]:
        """Constrói comando yt-dlp baseado nas opções"""
        cmd = [sys.executable, '-m', 'yt_dlp']
        
        # Output dir
        cmd.extend(['-P', self.output_dir])
        
        # Template
        template = self.template_edit.text().strip()
        if template:
            cmd.extend(['-o', template])
        else:
            cmd.extend(['-o', '%(title)s [%(id)s].%(ext)s'])
            
        # Modo
        mode = self.get_mode()
        if mode == "audio":
            cmd.extend(['-f', 'bestaudio/best'])
            cmd.extend(['-x', '--audio-format', self.audio_format_combo.currentText()])
            aq = self.audio_quality_combo.currentText().split()[0]
            cmd.extend(['--audio-quality', aq])
        elif mode == "video":
            cmd.extend(['-f', 'bestvideo/best'])
        elif mode == "custom":
            fmt = self.custom_format_edit.text().strip()
            if not fmt:
                QMessageBox.warning(self, "Formato Necessário", "Digite um Format ID (ex: 313+251)")
                return None
            cmd.extend(['-f', fmt])
        else:  # best
            cmd.extend(['-f', 'bestvideo+bestaudio/best'])
            cmd.extend(['--merge-output-format', self.merge_format_combo.currentText()])
            
        # Legendas
        if self.subtitles_check.isChecked():
            cmd.extend(['--write-subs', '--write-auto-subs'])
            langs = self.sub_langs_edit.text().strip()
            if langs:
                cmd.extend(['--sub-langs', langs])
                
        # Thumbnail
        if self.thumbnail_check.isChecked():
            cmd.extend(['--write-thumbnail'])
            
        # Metadados
        if self.metadata_check.isChecked():
            cmd.extend(['--add-metadata', '--embed-thumbnail'])
            
        # SponsorBlock
        if self.sponsorblock_check.isChecked():
            cmd.extend(['--sponsorblock-remove', 'all'])
            
        # Performance
        cmd.extend(['--concurrent-fragments', str(self.concurrent_spin.value())])
        throttle = self.throttle_edit.text().strip()
        if throttle:
            cmd.extend(['--throttled-rate', throttle])
            
        # Retries
        cmd.extend(['--retries', '10', '--fragment-retries', '10'])
        
        # Ignorar erros
        if self.ignore_errors_check.isChecked():
            cmd.append('--ignore-errors')
            
        # Playlist
        pl_items = self.pl_items_edit.text().strip()
        if pl_items:
            cmd.extend(['--playlist-items', pl_items])
        pl_start = self.pl_start_edit.text().strip()
        if pl_start:
            cmd.extend(['--playlist-start', pl_start])
        pl_end = self.pl_end_edit.text().strip()
        if pl_end:
            cmd.extend(['--playlist-end', pl_end])
            
        # Data
        date_after = self.date_after_edit.text().strip()
        if date_after:
            cmd.extend(['--dateafter', date_after])
        date_before = self.date_before_edit.text().strip()
        if date_before:
            cmd.extend(['--datebefore', date_before])
            
        # Verbose
        if self.verbose_check.isChecked():
            cmd.append('-v')
            
        cmd.append('--no-warnings')
        cmd.append(url)
        
        return cmd
        
    def cancel_download(self):
        if self.worker:
            self.log("⏹️ Cancelando download...", "warning")
            self.worker.cancel()
            self.btn_cancel.setEnabled(False)
            
    def on_progress(self, text: str):
        self.statusBar().showMessage(text)
        
    def on_finished(self, exit_code: int, output: str):
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if exit_code == 0:
            self.statusBar().showMessage("✅ Download concluído!")
            # Abrir pasta
            reply = QMessageBox.question(self, "Concluído", 
                "Download concluído com sucesso!\n\nAbrir pasta de download?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.open_output_folder()
        else:
            self.statusBar().showMessage(f"❌ Erro (código {exit_code})")
            
        self.worker = None
        
    def show_formats_dialog(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Necessária", "Cole uma URL primeiro!")
            return
            
        self.log(f"📋 Obtendo formatos para: {url}", "info")
        self.btn_formats.setEnabled(False)
        self.statusBar().showMessage("📋 Obtendo formatos...")
        
        # Thread para buscar formatos
        self.formats_worker = FormatsWorker(url)
        self.formats_worker.finished_signal.connect(self.on_formats_ready)
        self.formats_worker.start()
        
    def on_formats_ready(self, formats: List[Dict], error: str):
        self.btn_formats.setEnabled(True)
        self.statusBar().showMessage("✅ Pronto")
        
        if error:
            self.log(f"❌ Erro ao obter formatos: {error}", "error")
            QMessageBox.critical(self, "Erro", f"Falha ao obter formatos:\n{error}")
            return
            
        if not formats:
            self.log("❌ Nenhum formato encontrado", "error")
            return
            
        dialog = FormatDialog(self, formats)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_format:
            self.custom_format_edit.setText(dialog.selected_format)
            self.mode_custom.setChecked(True)
            self.log(f"✅ Formato selecionado: {dialog.selected_format}", "success")
            
    def log(self, message: str, level: str = "info"):
        """Adiciona mensagem ao log com cor"""
        colors = {
            "info": "#4fc3f7",
            "success": "#81c784",
            "warning": "#ffb74d",
            "error": "#e57373",
            "progress": "#fff176",
            "cmd": "#ce93d8"
        }
        color = colors.get(level, "#d4d4d4")
        
        # Timestamp
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        
        # Formatar
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.log_text.setTextColor(QColor(color))
        self.log_text.insertPlainText(f"[{ts}] {message}\n")
        self.log_text.setTextColor(QColor("#d4d4d4"))
        self.log_text.ensureCursorVisible()
        
        # Limitar linhas
        doc = self.log_text.document()
        if doc.blockCount() > 1000:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()
            
    def filter_log(self, filter_text: str):
        """Filtra log (simples - só mostra/oculta linhas)"""
        # Implementação simples: reaplicar log filtrado seria complexo
        # Por ora apenas muda título
        pass
        
    def clear_log(self):
        self.log_text.clear()
        self.log("🚀 Log limpo", "info")
        
    def save_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Log", "richardgoline_log.txt", "Text Files (*.txt)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log(f"💾 Log salvo em: {path}", "success")
            
    def copy_log(self):
        QApplication.clipboard().setText(self.log_text.toPlainText())
        self.log("📋 Log copiado para área de transferência", "success")
        
    def check_yt_dlp_update(self):
        self.log("🔍 Verificando atualizações do yt-dlp...", "info")
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp', '--user'],
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.log("✅ yt-dlp atualizado!", "success")
                self.log(result.stdout, "info")
            else:
                self.log(f"⚠️ {result.stderr}", "warning")
        except Exception as e:
            self.log(f"❌ Erro: {e}", "error")
            
    def show_settings(self):
        QMessageBox.information(self, "Configurações", 
            "Configurações salvas automaticamente:\n"
            "- Pasta de download\n"
            "- Tamanho/posição da janela\n\n"
            "Use o menu Arquivo > Abrir Pasta de Download para acessar.")
            
    def show_docs(self):
        QDesktopServices.openUrl(QUrl("https://github.com/yt-dlp/yt-dlp"))
        
    def report_bug(self):
        QDesktopServices.openUrl(QUrl("https://github.com/yt-dlp/yt-dlp/issues"))
        
    def show_about(self):
        QMessageBox.about(self, "Sobre RichardGoLine", 
            "<h3>🚀 RichardGoLine GUI v1.0.0</h3>"
            "<p>YouTube Downloader Ultra-Rápido com Máxima Qualidade</p>"
            "<p>Baseado no <b>yt-dlp</b> + <b>ffmpeg</b></p>"
            "<p>Interface: PyQt6</p>"
            "<p>Desenvolvido por Richard</p>"
            "<br>"
            "<p><b>Recursos:</b></p>"
            "<ul>"
            "<li>🎬 Vídeo 4K/8K + Áudio Opus/FLAC</li>"
            "<li>🎵 Áudio MP3/Opus/FLAC/M4A/WAV</li>"
            "<li>🚫 SponsorBlock automático</li>"
            "<li>📝 Legendas multi-idioma</li>"
            "<li>⚡ 16 fragments paralelos</li>"
            "<li>📋 Batch/Playlist com filtros</li>"
            "<li>🏷️ Metadados + Thumbnail embed</li>"
            "</ul>"
        )


class FormatsWorker(QThread):
    """Worker para buscar formatos"""
    finished_signal = pyqtSignal(list, str)  # formats, error
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            cmd = [sys.executable, '-m', 'yt_dlp', '-J', '--no-warnings', self.url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                formats = info.get('formats', [])
                self.finished_signal.emit(formats, "")
            else:
                self.finished_signal.emit([], result.stderr)
        except subprocess.TimeoutExpired:
            self.finished_signal.emit([], "Timeout ao buscar formatos")
        except Exception as e:
            self.finished_signal.emit([], str(e))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RichardGoLine")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RichardGoLine")
    
    # Fonte padrão
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = RichardGoLineGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()