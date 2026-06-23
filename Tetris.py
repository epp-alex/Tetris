#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tetris Deluxe Edition – PyQt5-Version
- Portiert von pygame → PyQt5 (QPainter-Rendering)
- 14-Sprachen-System
- Plattformübergreifende Einstellungs-Persistierung
- Highscore-Speicherung
- Partikel-System, Ghost-Piece, Hold, 5x Next-Preview
- Screen-Shake, Level-Up-Effekt
"""

import sys
import os
import json
import random
import math
import platform
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QGridLayout, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QTimer, QRect, QPoint, QSize, pyqtSignal, QElapsedTimer
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen, QBrush,
    QPainterPath, QLinearGradient
)

# ─────────────────────────── Sound (optional) ────────────────────────────────
try:
    from PyQt5.QtMultimedia import QSoundEffect
    from PyQt5.QtCore import QUrl
    _HAS_SOUND = True
except Exception:
    _HAS_SOUND = False


def resource_path(name):
    """Findet Ressourcen neben der .py-Datei (auch bei PyInstaller)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def load_sound(filename):
    if not _HAS_SOUND:
        return None
    path = resource_path(filename)
    if not os.path.exists(path):
        return None
    try:
        s = QSoundEffect()
        s.setSource(QUrl.fromLocalFile(path))
        return s
    except Exception:
        return None


def play_sound(sound, volume=1.0):
    if sound is None:
        return
    try:
        sound.setVolume(volume)
        sound.play()
    except Exception:
        pass


# ─────────────────────────── Konstanten ──────────────────────────────────────

COLUMNS       = 12
ROWS          = 27
CELL_SIZE     = 30
SIDE_PANEL    = 240
FPS           = 60

DIFFICULTY    = {'leicht': 1000, 'mittel': 500, 'schwer': 200}

LEVEL_BASE_SCORE          = 500
SPEEDUP_FACTOR_BEFORE_8   = 0.95
SPEEDUP_FACTOR_AFTER_7    = 0.97
MIN_FALL_INTERVAL         = 80

DEFAULT_MASTER_VOLUME     = 0.06
LEVELUP_VOLUME_FACTOR     = 0.60

# Qt-Farben
C_BLACK      = QColor(0,   0,   0)
C_GRAY       = QColor(40,  40,  40)
C_LGRAY      = QColor(150, 150, 150)
C_WHITE      = QColor(255, 255, 255)
C_YELLOW     = QColor(220, 220, 0)
C_GOLD       = QColor(255, 215, 0)
C_RED        = QColor(200, 0,   0)
C_GREEN      = QColor(0,   200, 0)
C_BLUE       = QColor(30,  144, 255)
C_GAME_BG    = QColor(50,  50,  50)

# Tetris-Formen
SHAPES = {
    'I': [[[1,1,1,1]], [[1],[1],[1],[1]]],
    'J': [[[1,0,0],[1,1,1]], [[1,1],[1,0],[1,0]], [[1,1,1],[0,0,1]], [[0,1],[0,1],[1,1]]],
    'L': [[[0,0,1],[1,1,1]], [[1,0],[1,0],[1,1]], [[1,1,1],[1,0,0]], [[1,1],[0,1],[0,1]]],
    'O': [[[1,1],[1,1]]],
    'S': [[[0,1,1],[1,1,0]], [[1,0],[1,1],[0,1]]],
    'T': [[[0,1,0],[1,1,1]], [[1,0],[1,1],[1,0]], [[1,1,1],[0,1,0]], [[0,1],[1,1],[0,1]]],
    'Z': [[[1,1,0],[0,1,1]], [[0,1],[1,1],[1,0]]]
}
SHAPE_KEYS = list(SHAPES.keys())
COLORS = [
    QColor(0,240,240), QColor(0,0,240), QColor(240,160,0),
    QColor(240,240,0), QColor(0,240,0), QColor(160,0,240), QColor(240,0,0)
]

# ─────────────────────────── 14-Sprachen ─────────────────────────────────────

LANGUAGES = {
    'Deutsch':'de','English':'en','Français':'fr','Español':'es',
    'Українська':'uk','Polski':'pl','Svenska':'sv','Italiano':'it',
    'Português':'pt','Русский':'ru','Ελληνικά':'el','Nederlands':'nl',
    'Türkçe':'tr','Čeština':'cs',
}

STRINGS = {
    'de': {
        'title':'Tetris Deluxe Edition','menu':'HAUPTMENÜ','difficulty':'SCHWIERIGKEIT',
        'easy':'Leicht','medium':'Mittel','hard':'Schwer','language':'SPRACHE',
        'volume':'LAUTSTÄRKE','start':'START','score':'SCORE:','level':'LEVEL:',
        'next_lvl':'NEXT Lvl:','best':'BEST:','next_pieces':'NEXT PIECES:',
        'hold':'HOLD:','pause':'PAUSE','game_over':'GAME OVER',
        'highscore':'Highscore gespeichert!',
        'menu_help':'Maus: Klicken | Pfeile & ENTER: Starten | ESC: Beenden'
    },
    'en': {
        'title':'Tetris Deluxe Edition','menu':'MAIN MENU','difficulty':'DIFFICULTY',
        'easy':'Easy','medium':'Medium','hard':'Hard','language':'LANGUAGE',
        'volume':'VOLUME','start':'START','score':'SCORE:','level':'LEVEL:',
        'next_lvl':'NEXT Lvl:','best':'BEST:','next_pieces':'NEXT PIECES:',
        'hold':'HOLD:','pause':'PAUSE','game_over':'GAME OVER',
        'highscore':'Highscore saved!',
        'menu_help':'Mouse: Click | Arrows & ENTER: Start | ESC: Exit'
    },
    'fr': {
        'title':'Tetris Deluxe Edition','menu':'MENU PRINCIPAL','difficulty':'DIFFICULTÉ',
        'easy':'Facile','medium':'Moyen','hard':'Difficile','language':'LANGUE',
        'volume':'VOLUME','start':'COMMENCER','score':'SCORE:','level':'NIVEAU:',
        'next_lvl':'PROCHAIN Niv:','best':'MEILLEUR:','next_pieces':'PROCHAINES PIÈCES:',
        'hold':'RÉSERVE:','pause':'PAUSE','game_over':'FIN DE JEU',
        'highscore':'Highscore enregistré!',
        'menu_help':'Souris: Clic | Flèches & ENTRÉE: Démarrer | ESC: Quitter'
    },
    'es': {
        'title':'Tetris Deluxe Edition','menu':'MENÚ PRINCIPAL','difficulty':'DIFICULTAD',
        'easy':'Fácil','medium':'Medio','hard':'Difícil','language':'IDIOMA',
        'volume':'VOLUMEN','start':'INICIAR','score':'PUNTOS:','level':'NIVEL:',
        'next_lvl':'PRÓXIMO Niv:','best':'MEJOR:','next_pieces':'PRÓXIMAS PIEZAS:',
        'hold':'RESERVA:','pause':'PAUSA','game_over':'FIN DEL JUEGO',
        'highscore':'¡Puntuación máxima guardada!',
        'menu_help':'Ratón: Clic | Flechas & ENTER: Iniciar | ESC: Salir'
    },
    'it': {
        'title':'Tetris Deluxe Edition','menu':'MENU PRINCIPALE','difficulty':'DIFFICOLTÀ',
        'easy':'Facile','medium':'Medio','hard':'Difficile','language':'LINGUA',
        'volume':'VOLUME','start':'INIZIA','score':'PUNTEGGIO:','level':'LIVELLO:',
        'next_lvl':'PROX. Liv:','best':'MIGLIORE:','next_pieces':'PROSSIMI PEZZI:',
        'hold':'RISERVA:','pause':'PAUSA','game_over':'GAME OVER',
        'highscore':'High score salvato!',
        'menu_help':'Mouse: Clic | Frecce & INVIO: Inizia | ESC: Esci'
    },
    'pt': {
        'title':'Tetris Deluxe Edition','menu':'MENU PRINCIPAL','difficulty':'DIFICULDADE',
        'easy':'Fácil','medium':'Médio','hard':'Difícil','language':'IDIOMA',
        'volume':'VOLUME','start':'COMEÇAR','score':'PONTUAÇÃO:','level':'NÍVEL:',
        'next_lvl':'PRÓX. Nív:','best':'MELHOR:','next_pieces':'PRÓXIMAS PEÇAS:',
        'hold':'RESERVA:','pause':'PAUSA','game_over':'FIM DE JOGO',
        'highscore':'Recorde salvo!',
        'menu_help':'Mouse: Clicar | Setas & ENTER: Começar | ESC: Sair'
    },
    'ru': {
        'title':'Tetris Deluxe Edition','menu':'ГЛАВНОЕ МЕНЮ','difficulty':'СЛОЖНОСТЬ',
        'easy':'Легкий','medium':'Средний','hard':'Сложный','language':'ЯЗЫК',
        'volume':'ГРОМКОСТЬ','start':'НАЧАТЬ','score':'ОЧКИ:','level':'УРОВЕНЬ:',
        'next_lvl':'СЛЕД. Ур:','best':'ЛУЧШИЙ:','next_pieces':'СЛЕДУЮЩИЕ ФИГУРЫ:',
        'hold':'РЕЗЕРВ:','pause':'ПАУЗА','game_over':'КОНЕЦ ИГРЫ',
        'highscore':'Рекорд сохранен!',
        'menu_help':'Мышь: Клик | Стрелки & ENTER: Старт | ESC: Выход'
    },
    'el': {
        'title':'Tetris Deluxe Edition','menu':'ΚΥΡΙΟ ΜΕΝΟΥ','difficulty':'ΔΥΣΚΟΛΙΑ',
        'easy':'Εύκολο','medium':'Μεσαίο','hard':'Δύσκολο','language':'ΓΛΩΣΣΑ',
        'volume':'ΗΧΟΣ','start':'ΕΝΑΡΞΗ','score':'ΣΚΟΡ:','level':'ΕΠΙΠΕΔΟ:',
        'next_lvl':'ΕΠΟΜ. Ε:','best':'ΚΑΛΥΤΕΡΟ:','next_pieces':'ΕΠΟΜΕΝΑ ΚΟΜΜΑΤΙΑ:',
        'hold':'ΚΡΑΤΗΣΗ:','pause':'ΠΑΥΣΗ','game_over':'ΤΕΛΟΣ ΠΑΙΧΝΙΔΙΟΥ',
        'highscore':'Αποθηκεύθηκε!',
        'menu_help':'Ποντίκι: Κλικ | Βέλη & ENTER: Έναρξη'
    },
    'uk': {
        'title':'Tetris Deluxe Edition','menu':'ГОЛОВНЕ МЕНЮ','difficulty':'СКЛАДНІСТЬ',
        'easy':'Легко','medium':'Середньо','hard':'Важко','language':'МОВА',
        'volume':'ГУЧНІСТЬ','start':'СТАРТ','score':'РАХУНОК:','level':'РІВЕНЬ:',
        'next_lvl':'НАСТ. Рів:','best':'РЕКОРД:','next_pieces':'НАСТ. ФІГУРИ:',
        'hold':'ЗБЕРЕЖЕННЯ:','pause':'ПАУЗА','game_over':'ГРУ ЗАВЕРШЕНО',
        'highscore':'Рекорд збережено!',
        'menu_help':'Миша: Клік | Стрілки & ENTER: Старт | ESC: Вихід'
    },
    'pl': {
        'title':'Tetris Deluxe Edition','menu':'MENU GŁÓWNE','difficulty':'POZIOM TRUDNOŚCI',
        'easy':'Łatwy','medium':'Średni','hard':'Trudny','language':'JĘZYK',
        'volume':'GŁOŚNOŚĆ','start':'START','score':'WYNIK:','level':'POZIOM:',
        'next_lvl':'NAST. Poz:','best':'REKORD:','next_pieces':'NAST. KLOCKI:',
        'hold':'REZERWA:','pause':'PAUZA','game_over':'KONIEC GRY',
        'highscore':'Rekord zapisany!',
        'menu_help':'Mysz: Kliknij | Strzałki & ENTER: Start | ESC: Wyjdź'
    },
    'nl': {
        'title':'Tetris Deluxe Edition','menu':'HOOFDMENU','difficulty':'MOEILIJKHEIDSGRAAD',
        'easy':'Makkelijk','medium':'Gemiddeld','hard':'Moeilijk','language':'TAAL',
        'volume':'VOLUME','start':'START','score':'SCORE:','level':'NIVEAU:',
        'next_lvl':'VOLG. Niv:','best':'BESTE:','next_pieces':'VOLG. STUKKEN:',
        'hold':'VASTHOUDEN:','pause':'PAUZE','game_over':'GAME OVER',
        'highscore':'Highscore opgeslagen!',
        'menu_help':'Muis: Klik | Pijltjes & ENTER: Start | ESC: Afsluiten'
    },
    'tr': {
        'title':'Tetris Deluxe Edition','menu':'ANA MENÜ','difficulty':'ZORLUK',
        'easy':'Kolay','medium':'Orta','hard':'Zor','language':'DİL',
        'volume':'SES SEVİYESİ','start':'BAŞLA','score':'SKOR:','level':'SEVİYE:',
        'next_lvl':'SONR. Sev:','best':'EN İYİ:','next_pieces':'SONRAKİ PARÇALAR:',
        'hold':'TUT:','pause':'DURAKLAT','game_over':'OYUN BİTTİ',
        'highscore':'Highscore kaydedildi!',
        'menu_help':'Fare: Tıkla | Oklar & ENTER: Başlat | ESC: Çıkış'
    },
    'sv': {
        'title':'Tetris Deluxe Edition','menu':'HUVUDMENY','difficulty':'SVÅRIGHETSGRAD',
        'easy':'Lätt','medium':'Mellan','hard':'Svår','language':'SPRÅK',
        'volume':'VOLYM','start':'STARTA','score':'POÄNG:','level':'NIVÅ:',
        'next_lvl':'NÄSTA Niv:','best':'BÄSTA:','next_pieces':'NÄSTA BITAR:',
        'hold':'HÅLL:','pause':'PAUS','game_over':'GAME OVER',
        'highscore':'Highscore sparat!',
        'menu_help':'Mus: Klicka | Pilar & ENTER: Starta | ESC: Avsluta'
    },
    'cs': {
        'title':'Tetris Deluxe Edition','menu':'HLAVNÍ MENU','difficulty':'OBTÍŽNOST',
        'easy':'Lehká','medium':'Střední','hard':'Těžká','language':'JAZYK',
        'volume':'HLASITOST','start':'START','score':'SKÓRE:','level':'ÚROVEŇ:',
        'next_lvl':'DALŠÍ Úr:','best':'NEJLEPŠÍ:','next_pieces':'DALŠÍ KOSTKY:',
        'hold':'DRŽET:','pause':'PAUZA','game_over':'KONEC HRY',
        'highscore':'Highscore uloženo!',
        'menu_help':'Myš: Kliknout | Šipky & ENTER: Start | ESC: Ukončit'
    },
}

# ─────────────────────────── Einstellungen ───────────────────────────────────

def get_settings_path():
    s = platform.system()
    if s == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif s == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    folder = base / "TetrisDeluxe"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "settings.json"

def load_settings():
    path = get_settings_path()
    defaults = {'difficulty':'mittel','language':'Deutsch','master_volume':0.06,'highscore':0}
    if path.exists():
        try:
            with open(path,"r",encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault('highscore', 0)
            return data
        except Exception:
            return defaults
    return defaults

def save_settings(settings):
    with open(get_settings_path(),"w",encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

# ─────────────────────────── Spiellogik ──────────────────────────────────────

class Piece:
    def __init__(self, col, row, shape):
        self.col, self.row, self.shape_key = col, row, shape
        self.color = COLORS[SHAPE_KEYS.index(shape)]
        self.rotation = 0
        self.matrix = SHAPES[shape][self.rotation]

def create_grid(locked):
    grid = [[None]*COLUMNS for _ in range(ROWS)]
    for (r,c), color in locked.items():
        if 0 <= r < ROWS and 0 <= c < COLUMNS:
            grid[r][c] = color
    return grid

def convert_shape_format(piece):
    return [(piece.row+i, piece.col+j)
            for i,row in enumerate(piece.matrix)
            for j,val in enumerate(row) if val]

def valid_space(piece, grid):
    for r,c in convert_shape_format(piece):
        if c<0 or c>=COLUMNS or r>=ROWS:
            return False
        if r>=0 and grid[r][c]:
            return False
    return True

def get_ghost_piece(piece, grid):
    ghost = Piece(piece.col, piece.row, piece.shape_key)
    ghost.rotation, ghost.matrix = piece.rotation, piece.matrix
    while valid_space(ghost, grid):
        ghost.row += 1
    ghost.row -= 1
    return ghost

def get_shape_from_bag(bag):
    if not bag:
        bag.extend(SHAPE_KEYS)
        random.shuffle(bag)
    return bag.pop()

# ─────────────────────────── Partikel ────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color, size=4, decay=15):
        self.x, self.y = float(x), float(y)
        self.color = color
        self.vx = random.uniform(-5,5)
        self.vy = random.uniform(-5,5)
        self.lifetime = 255
        self.size = size
        self.decay = decay

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= self.decay

    def draw(self, painter: QPainter):
        if self.lifetime <= 0:
            return
        alpha = max(0, min(255, int(self.lifetime)))
        c = QColor(self.color)
        c.setAlpha(alpha)
        painter.fillRect(int(self.x), int(self.y), self.size, self.size, c)

# ─────────────────────────── Sprach-Dialog ───────────────────────────────────

class LanguageDialog(QDialog):
    def __init__(self, parent, lang_keys, selected_index):
        super().__init__(parent)
        self.setWindowTitle("Select Language")
        self.setModal(True)
        self.setFixedSize(500, 420)
        self.selected = selected_index
        self.lang_keys = lang_keys
        self._setup_ui(lang_keys, selected_index)

    def _setup_ui(self, lang_keys, selected_index):
        self.setStyleSheet(
            "QDialog { background-color: #1c1c1c; }"
            "QWidget { background-color: #1c1c1c; }"
            "QScrollArea { background-color: #1c1c1c; border: none; }"
            "QLabel { color: #ffffff; background-color: transparent; }"
            "QPushButton {"
            "  background-color: #3c3c3c; color: #ffffff;"
            "  border: 2px solid #666666; border-radius: 5px;"
            "  padding: 7px 10px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: #525252; border-color: #909090; }"
            "QPushButton[active=\"true\"] {"
            "  background-color: #006600; color: #ffffff; border-color: #00aa00; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("🌐 Select Language")
        title.setStyleSheet("color:#ffffff; font-size:16px; font-weight:bold; background:transparent;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1c1c1c; }")
        container = QWidget()
        container.setStyleSheet("background-color: #1c1c1c;")
        grid = QGridLayout(container)
        grid.setSpacing(6)

        self.buttons = []
        for i, lang in enumerate(lang_keys):
            btn = QPushButton(lang)
            btn.setCheckable(False)
            btn.setProperty("active", i == selected_index)
            btn.setStyle(btn.style())
            btn.clicked.connect(lambda _, idx=i: self._pick(idx))
            self.buttons.append(btn)
            grid.addWidget(btn, i//2, i%2)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        cancel = QPushButton("✕ Abbrechen")
        cancel.setStyleSheet(
            "background-color:#444444; color:#ffffff;"
            "border:2px solid #666666; border-radius:5px; padding:7px; font-weight:bold;"
        )
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)

    def _pick(self, idx):
        self.selected = idx
        self.accept()

# ─────────────────────────── Menü-Widget ─────────────────────────────────────

class MenuWidget(QWidget):
    start_game = pyqtSignal(str, float)   # difficulty, volume
    

    def __init__(self, settings, sounds):
        super().__init__()
        self.settings = settings
        self.sounds = sounds

        self.diff_keys  = list(DIFFICULTY.keys())
        self.lang_keys  = list(LANGUAGES.keys())
        self.sel_diff   = self.diff_keys.index(settings.get('difficulty','mittel'))
        self.sel_lang   = self.lang_keys.index(settings.get('language','Deutsch'))
        self.volume     = int(settings.get('master_volume', 0.06) * 100)
        self._build_ui()

    def _strings(self):
        return STRINGS[LANGUAGES[self.lang_keys[self.sel_lang]]]

    def _build_ui(self):
        self.setStyleSheet(
            "QWidget { background-color: #111111; color: #e0e0e0; font-family: Arial; }"
            "QPushButton {"
            "  border-radius: 6px; font-size: 15px; font-weight: bold;"
            "  padding: 8px 16px; border: 2px solid #505050; }"
            "QPushButton#diff_btn {"
            "  background-color: #666666; color: white;"
            "  min-height: 44px; min-width: 120px; }"
            "QPushButton#diff_btn[active=\"true\"] {"
            "  background-color: #006600; color: #ffffff; border-color: #00aa00; }"
            "QPushButton#diff_btn:hover { background-color: #777777; }"
            "QPushButton#lang_btn { background-color: #555555; color: white; min-height: 44px; }"
            "QPushButton#lang_btn:hover { background-color: #666666; }"
            "QPushButton#start_btn {"
            "  background-color: #004a99; color: #ffffff;"
            "  min-height: 50px; font-size: 20px; border-color: #0066cc; }"
            "QPushButton#start_btn:hover { background-color: #005cb3; }"
            "QSlider::groove:horizontal { height: 8px; background-color: #666666; border-radius: 4px; }"
            "QSlider::handle:horizontal {"
            "  background-color: #aaaa00; width: 16px; height: 16px;"
            "  margin: -4px 0; border-radius: 8px; }"
            "QSlider::sub-page:horizontal { background-color: #006600; border-radius: 4px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(50, 30, 50, 20)
        root.setSpacing(16)

        # Titel + Highscore
        self.lbl_title = QLabel("TETRIS DELUXE")
        self.lbl_title.setStyleSheet("font-size:38px; font-weight:bold; color:white; background-color: #666666; padding: 5px;")
        root.addWidget(self.lbl_title)

        self.lbl_hs = QLabel()
        self.lbl_hs.setStyleSheet("font-size:16px; font-weight:bold; color:black; background:transparent;")
        root.addWidget(self.lbl_hs)
        root.addSpacing(10)

        # Schwierigkeit
        self.lbl_diff = QLabel()
        self.lbl_diff.setStyleSheet("font-size:15px; color:black; font-weight:bold; background: transparent;")
        root.addWidget(self.lbl_diff)

        diff_row = QHBoxLayout()
        diff_row.setSpacing(12)
        self.diff_btns = []
        for i, key in enumerate(self.diff_keys):
            btn = QPushButton(key.capitalize())
            btn.setObjectName("diff_btn")
            btn.setProperty("active", i == self.sel_diff)
            btn.clicked.connect(lambda _, idx=i: self._set_diff(idx))
            self.diff_btns.append(btn)
            diff_row.addWidget(btn)
        diff_row.addStretch()
        root.addLayout(diff_row)

        # Sprache
        self.lbl_lang_header = QLabel()
        self.lbl_lang_header.setStyleSheet("font-size:15px; color:black; font-weight:bold; background: transparent;")
        root.addWidget(self.lbl_lang_header)

        self.btn_lang = QPushButton()
        self.btn_lang.setObjectName("lang_btn")
        self.btn_lang.clicked.connect(self._open_lang_modal)
        root.addWidget(self.btn_lang)

        # Lautstärke
        vol_row = QHBoxLayout()
        self.lbl_vol = QLabel()
        self.lbl_vol.setStyleSheet("font-size:15px; color:black; font-weight:bold; background: transparent;")
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(self.volume)
        self.slider_vol.valueChanged.connect(self._vol_changed)
        self.lbl_vol_pct = QLabel(f"{self.volume}%")
        self.lbl_vol_pct.setStyleSheet("color: black; background: transparent; min-width: 50px; font-weight: bold; font-size: 16px;")
        vol_row.addWidget(self.lbl_vol)
        vol_row.addWidget(self.slider_vol, 1)
        vol_row.addWidget(self.lbl_vol_pct)
        root.addLayout(vol_row)

        root.addSpacing(10)

        # Start
        self.btn_start = QPushButton()
        self.btn_start.setObjectName("start_btn")
        self.btn_start.clicked.connect(self._do_start)
        root.addWidget(self.btn_start)

        root.addStretch()

        # Help-Zeile
        self.lbl_help = QLabel()
        self.lbl_help.setStyleSheet("font-size:12px; color:#505050; background:transparent;")
        root.addWidget(self.lbl_help)

        self._refresh_labels()

    def _refresh_labels(self):
        st = self._strings()
        self.lbl_hs.setText(f"HIGH SCORE: {self.settings.get('highscore',0)}")
        self.lbl_diff.setText(st['difficulty'])
        self.lbl_lang_header.setText(st['language'])
        self.btn_lang.setText(f"{st['language']}: {self.lang_keys[self.sel_lang]}")
        self.lbl_vol.setText(st['volume'])
        self.btn_start.setText(st['start'])
        self.lbl_help.setText(st.get('menu_help',''))
        # Diff-Labels aktualisieren
        labels = [st['easy'], st['medium'], st['hard']]
        for i, btn in enumerate(self.diff_btns):
            btn.setText(labels[i])

    def _set_diff(self, idx):
        self.sel_diff = idx
        for i, btn in enumerate(self.diff_btns):
            btn.setProperty("active", i == idx)
            btn.setStyle(btn.style())

    def _vol_changed(self, val):
        self.volume = val
        self.lbl_vol_pct.setText(f"{val}%")

    def _open_lang_modal(self):
        dlg = LanguageDialog(self, self.lang_keys, self.sel_lang)
        if dlg.exec_() == QDialog.Accepted:
            self.sel_lang = dlg.selected
            self._refresh_labels()

    def _do_start(self):
        self.settings.update({
            'difficulty': self.diff_keys[self.sel_diff],
            'language':   self.lang_keys[self.sel_lang],
            'master_volume': self.volume / 100
        })
        save_settings(self.settings)
        self.start_game.emit(self.diff_keys[self.sel_diff], self.volume / 100)

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == Qt.Key_Return or k == Qt.Key_Enter:
            self._do_start()
        elif k == Qt.Key_Escape:
            QApplication.quit()
        elif k == Qt.Key_Left:
            self._set_diff(max(0, self.sel_diff - 1))
        elif k == Qt.Key_Right:
            self._set_diff(min(len(self.diff_keys)-1, self.sel_diff + 1))

# ─────────────────────────── Spiel-Canvas ────────────────────────────────────

class GameCanvas(QWidget):
    """Das eigentliche Tetris-Spielfeld mit Seitenpanel, komplett via QPainter."""

    game_over_signal = pyqtSignal(int)   # final score

    def __init__(self, settings, difficulty, sounds, volume):
        super().__init__()
        self.settings   = settings
        self.difficulty = difficulty
        self.sounds     = sounds
        self.volume     = volume

        total_w = CELL_SIZE * COLUMNS + SIDE_PANEL
        total_h = CELL_SIZE * ROWS
        self.setFixedSize(total_w, total_h)
        self.setFocusPolicy(Qt.StrongFocus)

        self._init_game()

        self.elapsed = QElapsedTimer()
        self.elapsed.start()
        self.last_ms  = 0

        self.timer = QTimer(self)
        self.timer.setInterval(1000 // FPS)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ── Initialisierung ──
    def _init_game(self):
        lang_code = LANGUAGES[self.settings['language']]
        self.strings = STRINGS[lang_code]

        self.locked     = {}
        self.grid       = create_grid(self.locked)
        self.score      = 0
        self.level      = 1
        self.fall_time  = 0
        self.fall_interval = DIFFICULTY[self.difficulty]
        self.paused     = False
        self.shake_intensity = 0
        self.shake_offset    = QPoint(0,0)
        self.particles  = []
        self.game_active = True

        # Level-Up-Overlay
        self.levelup_text    = ""
        self.levelup_timer   = 0
        self.levelup_scale   = 1.0

        self.shape_bag  = []
        self.next_pieces = [
            Piece(COLUMNS//2-2, 0, get_shape_from_bag(self.shape_bag))
            for _ in range(5)
        ]
        self.current_piece = Piece(COLUMNS//2-2, 0, get_shape_from_bag(self.shape_bag))
        self.hold_shape = None
        self.can_hold   = True

    # ── Haupt-Tick ──
    def _tick(self):
        now_ms = self.elapsed.elapsed()
        delta  = now_ms - self.last_ms
        self.last_ms = now_ms

        if not self.paused and self.game_active:
            self.fall_time += delta

            # Partikel
            for p in self.particles[:]:
                p.update()
                if p.lifetime <= 0:
                    self.particles.remove(p)

            # Shake
            if self.shake_intensity > 0:
                self.shake_offset = QPoint(
                    random.randint(-self.shake_intensity, self.shake_intensity),
                    random.randint(-self.shake_intensity, self.shake_intensity)
                )
                self.shake_intensity = max(0, self.shake_intensity - 2)
            else:
                self.shake_offset = QPoint(0,0)

            # Level-Up-Overlay-Timer
            if self.levelup_timer > 0:
                self.levelup_timer -= delta

            # Automatisch fallen
            if self.fall_time >= self.fall_interval:
                self.fall_time = 0
                self.current_piece.row += 1
                if not valid_space(self.current_piece, self.grid):
                    self.current_piece.row -= 1
                    self._lock_piece()

        self.update()

    def _lock_piece(self):
        for r,c in convert_shape_format(self.current_piece):
            if r >= 0:
                self.locked[(r,c)] = self.current_piece.color
        self.grid = create_grid(self.locked)

        cleared = self._clear_lines()
        if cleared > 0:
            points = {1:100, 2:300, 3:500, 4:800}.get(cleared, 0)
            self.score += points
            if self.score > self.settings.get('highscore',0):
                self.settings['highscore'] = self.score
                save_settings(self.settings)

            if self.score >= LEVEL_BASE_SCORE * self.level:
                self.level += 1
                self.fall_interval = max(
                    MIN_FALL_INTERVAL,
                    self.fall_interval * (
                        SPEEDUP_FACTOR_BEFORE_8 if self.level < 8
                        else SPEEDUP_FACTOR_AFTER_7
                    )
                )
                self.levelup_text  = f"LEVEL {self.level}"
                self.levelup_timer = 700
                play_sound(self.sounds.get('levelup'), self.volume * LEVELUP_VOLUME_FACTOR)

        self.grid = create_grid(self.locked)
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(Piece(COLUMNS//2-2, 0, get_shape_from_bag(self.shape_bag)))
        self.can_hold = True

        if not valid_space(self.current_piece, self.grid):
            if self.score > self.settings.get('highscore',0):
                self.settings['highscore'] = self.score
                save_settings(self.settings)
            self.game_active = False
            self.timer.stop()
            self.game_over_signal.emit(self.score)

    def _clear_lines(self):
        lines = [r for r in range(ROWS) if None not in self.grid[r]]
        if not lines:
            return 0
        # Flash (vereinfacht – direkt löschen & Partikel)
        for r in lines:
            for col in range(COLUMNS):
                color = self.grid[r][col] or C_WHITE
                for _ in range(6):
                    self.particles.append(Particle(
                        col*CELL_SIZE+15, r*CELL_SIZE+15, color
                    ))
        # Locked bereinigen
        for r in sorted(lines):
            for col in range(COLUMNS):
                self.locked.pop((r, col), None)
            for key in sorted(list(self.locked.keys()), reverse=True):
                rr, cc = key
                if rr < r:
                    self.locked[(rr+1, cc)] = self.locked.pop(key)
        play_sound(self.sounds.get('clear'), self.volume)
        return len(lines)

    # ── Eingabe ──
    def keyPressEvent(self, ev):
        if not self.game_active:
            return
        k = ev.key()

        if k == Qt.Key_Escape:
            if self.score > self.settings.get('highscore',0):
                self.settings['highscore'] = self.score
                save_settings(self.settings)
            self.timer.stop()
            self.game_over_signal.emit(self.score)
            return

        if k == Qt.Key_P:
            self.paused = not self.paused
            return

        if self.paused:
            return

        if k == Qt.Key_C:
            self._do_hold()
        elif k == Qt.Key_Left:
            self.current_piece.col -= 1
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.col += 1
        elif k == Qt.Key_Right:
            self.current_piece.col += 1
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.col -= 1
        elif k == Qt.Key_Down:
            self.current_piece.row += 1
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.row -= 1
        elif k == Qt.Key_Space:
            self._hard_drop()
        elif k == Qt.Key_Up:
            old = self.current_piece.rotation
            self.current_piece.rotation = (old+1) % len(SHAPES[self.current_piece.shape_key])
            self.current_piece.matrix = SHAPES[self.current_piece.shape_key][self.current_piece.rotation]
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.rotation = old
                self.current_piece.matrix = SHAPES[self.current_piece.shape_key][old]
        elif k == Qt.Key_Z:
            # Undo-ähnlich: Rückgängig (Ctrl+Z)
            pass

    def _do_hold(self):
        if not self.can_hold:
            return
        if self.hold_shape is None:
            self.hold_shape = self.current_piece.shape_key
            self.current_piece = self.next_pieces.pop(0)
            self.next_pieces.append(Piece(COLUMNS//2-2, 0, get_shape_from_bag(self.shape_bag)))
        else:
            temp = self.hold_shape
            self.hold_shape = self.current_piece.shape_key
            self.current_piece = Piece(COLUMNS//2-2, 0, temp)
        self.can_hold = False

    def _hard_drop(self):
        while valid_space(self.current_piece, self.grid):
            self.current_piece.row += 1
        self.current_piece.row -= 1
        # Staubpartikel
        for r,c in convert_shape_format(self.current_piece):
            if r >= 0:
                for _ in range(12):
                    dc = random.choice([
                        QColor(150,150,150), QColor(190,190,190), QColor(120,120,120)
                    ])
                    p = Particle(
                        c*CELL_SIZE + random.randint(0, CELL_SIZE),
                        (r+1)*CELL_SIZE, dc,
                        size=random.randint(6,10), decay=random.randint(5,8)
                    )
                    p.vx = random.uniform(-4,4)
                    p.vy = random.uniform(-3,-0.5)
                    self.particles.append(p)
        self.shake_intensity = 8
        self._lock_piece()

    # ── Zeichnen ──
    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        ox, oy = self.shake_offset.x(), self.shake_offset.y()
        painter.translate(ox, oy)

        self._draw_board(painter)
        self._draw_ghost(painter)
        self._draw_current(painter)
        self._draw_particles(painter)
        self._draw_side_panel(painter)

        if self.paused:
            self._draw_pause(painter)

        if self.levelup_timer > 0:
            self._draw_levelup(painter)

        painter.end()

    def _draw_board(self, p: QPainter):
        board_w = CELL_SIZE * COLUMNS
        board_h = CELL_SIZE * ROWS
        p.fillRect(0, 0, board_w, board_h, C_GAME_BG)

        for r in range(ROWS):
            for c in range(COLUMNS):
                cell = self.grid[r][c]
                rx, ry = c*CELL_SIZE, r*CELL_SIZE
                if cell:
                    p.fillRect(rx, ry, CELL_SIZE, CELL_SIZE, cell)
                    p.setPen(QPen(QColor(255,255,255,60), 1))
                    p.drawRect(rx, ry, CELL_SIZE-1, CELL_SIZE-1)
                else:
                    p.setPen(QPen(QColor(100,100,100), 1))
                    p.drawRect(rx, ry, CELL_SIZE-1, CELL_SIZE-1)

    def _draw_ghost(self, p: QPainter):
        ghost = get_ghost_piece(self.current_piece, self.grid)
        ghost_color = QColor(70,70,70)
        for r,c in convert_shape_format(ghost):
            if r >= 0:
                p.fillRect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE, ghost_color)

    def _draw_current(self, p: QPainter):
        for r,c in convert_shape_format(self.current_piece):
            if r >= 0:
                col = self.current_piece.color
                p.fillRect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE, col)
                p.setPen(QPen(QColor(255,255,255,80), 1))
                p.drawRect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE-1, CELL_SIZE-1)

    def _draw_particles(self, p: QPainter):
        for particle in self.particles:
            particle.draw(p)

    def _draw_side_panel(self, p: QPainter):
        sx = CELL_SIZE * COLUMNS
        sw = SIDE_PANEL
        sh = CELL_SIZE * ROWS
        p.fillRect(sx, 0, sw, sh, QColor(30,30,30))
        p.setPen(QPen(QColor(80,80,80), 1))
        p.drawLine(sx, 0, sx, sh)

        st = self.strings
        right_edge = sx + sw - 10

        self._draw_text(p, st['score'], 18, sx+10, 18, C_YELLOW)
        self._draw_text_right(p, str(self.score), 28, right_edge, 18, C_WHITE)

        self._draw_text(p, st['level'], 15, sx+10, 62, C_WHITE)
        self._draw_text_right(p, str(self.level), 20, right_edge, 62, C_WHITE)

        self._draw_text(p, st['next_lvl'], 13, sx+10, 98, C_WHITE)
        self._draw_text_right(p, str(LEVEL_BASE_SCORE * self.level), 15, right_edge, 98, C_WHITE)

        best = max(self.score, self.settings.get('highscore',0))
        self._draw_text(p, f"{st['best']} {best}", 18, sx+10, 138, C_GOLD)

        # Next-Pieces
        self._draw_text(p, st['next_pieces'], 15, sx+10, 185, C_WHITE)
        for idx, piece in enumerate(self.next_pieces):
            y_off = 215 + idx * 80
            self._draw_mini_piece(p, piece, sx+50, y_off)

        # Hold
        hold_y = 630
        self._draw_text(p, st['hold'], 15, sx+10, hold_y, C_WHITE)
        if self.hold_shape:
            hold_p = Piece(0,0, self.hold_shape)
            self._draw_mini_piece(p, hold_p, sx+50, hold_y+25)

    def _draw_mini_piece(self, p: QPainter, piece, ox, oy):
        cs = CELL_SIZE - 2
        for i, row in enumerate(piece.matrix):
            for j, val in enumerate(row):
                if val:
                    p.fillRect(ox + j*cs, oy + i*cs, cs-1, cs-1, piece.color)

    def _draw_pause(self, p: QPainter):
        overlay = QColor(0,0,0,120)
        p.fillRect(0, 0, self.width(), self.height(), overlay)
        f = QFont("Arial", 52, QFont.Bold)
        p.setFont(f)
        p.setPen(C_YELLOW)
        p.drawText(self.rect(), Qt.AlignCenter, self.strings['pause'])

    def _draw_levelup(self, p: QPainter):
        progress = 1 - (self.levelup_timer / 700)
        scale = 1 + 0.3 * abs(progress - 0.5) * 2
        fsize = int(72 * scale)
        f = QFont("Arial", fsize, QFont.Bold)
        p.setFont(f)
        overlay = QColor(0,0,0,140)
        p.fillRect(0, 0, self.width(), self.height(), overlay)
        p.setPen(C_YELLOW)
        p.drawText(self.rect(), Qt.AlignCenter, self.levelup_text)

    def _draw_text(self, p: QPainter, text, size, x, y, color):
        f = QFont("Arial", size, QFont.Bold)
        p.setFont(f)
        p.setPen(color)
        p.drawText(x, y + size, text)

    def _draw_text_right(self, p: QPainter, text, size, right_x, y, color):
        # Schriftgröße reduzieren wenn zu breit
        while size > 10:
            f = QFont("Arial", size, QFont.Bold)
            fm = QFontMetrics(f)
            if fm.horizontalAdvance(text) <= SIDE_PANEL - 20:
                break
            size -= 2
        f = QFont("Arial", size, QFont.Bold)
        fm = QFontMetrics(f)
        w = fm.horizontalAdvance(text)
        p.setFont(f)
        p.setPen(color)
        p.drawText(right_x - w, y + size, text)

# ─────────────────────────── Game-Over-Widget ────────────────────────────────

class GameOverWidget(QWidget):
    restart_signal = pyqtSignal()

    def __init__(self, score, settings):
        super().__init__()
        self.setStyleSheet("background: black;")
        lang_code = LANGUAGES[settings['language']]
        st = STRINGS[lang_code]

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        lbl_go = QLabel(st['game_over'])
        lbl_go.setStyleSheet("color: #c80000; font-size: 60px; font-weight: bold;")
        lbl_go.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_go)

        lbl_sc = QLabel(f"{st['score']} {score}")
        lbl_sc.setStyleSheet("color: white; font-size: 28px;")
        lbl_sc.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_sc)

        best = settings.get('highscore', 0)
        lbl_hs = QLabel(f"{st['best']} {best}")
        lbl_hs.setStyleSheet("color: #ffd700; font-size: 22px;")
        lbl_hs.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_hs)

        btn = QPushButton("🔄 Zurück zum Menü")
        btn.setStyleSheet(
            "background:#1e90ff; color:white; font-size:18px; font-weight:bold;"
            "border-radius:8px; padding:12px 30px; border:none;"
        )
        btn.clicked.connect(self.restart_signal)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        # Auto-Rückkehr nach 5 Sekunden
        QTimer.singleShot(5000, self.restart_signal)

# ─────────────────────────── Haupt-Fenster ───────────────────────────────────

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tetris Deluxe Edition")

        self.settings = load_settings()
        self.sounds   = {
            'clear':   load_sound("clear.wav"),
            'levelup': load_sound("levelup.wav"),
        }

        total_w = CELL_SIZE * COLUMNS + SIDE_PANEL
        total_h = CELL_SIZE * ROWS
        self.setFixedSize(total_w, total_h)

        self._show_menu()

    def _show_menu(self):
        self._clear_layout()
        menu = MenuWidget(self.settings, self.sounds)
        menu.start_game.connect(self._start_game)
        self._set_central(menu)
        menu.setFocus()

    def _start_game(self, difficulty, volume):
        self._clear_layout()
        self.settings['difficulty']    = difficulty
        self.settings['master_volume'] = volume
        game = GameCanvas(self.settings, difficulty, self.sounds, volume)
        game.game_over_signal.connect(self._game_over)
        self._set_central(game)
        game.setFocus()

    def _game_over(self, score):
        self._clear_layout()
        go = GameOverWidget(score, self.settings)
        go.restart_signal.connect(self._show_menu)
        self._set_central(go)

    def _set_central(self, widget):
        if self.layout() is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0,0,0,0)
            layout.setSpacing(0)
        self.layout().addWidget(widget)
        self._current = widget

    def _clear_layout(self):
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def keyPressEvent(self, ev):
        # Weiterleiten an aktives Child
        if hasattr(self, '_current') and self._current:
            QApplication.sendEvent(self._current, ev)


# ─────────────────────────── Entry-Point ─────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
