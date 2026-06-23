# Tetris Deluxe Edition

An enhanced Tetris implementation in Python built with **PyQt5** (rendered via `QPainter`, no pygame). Featuring multi-language support, a ghost piece, hold function, particle effects, and cross-platform settings/highscore persistence.

## Features

- 🎮 **Classic Tetris gameplay** with a 7-bag randomizer for fair piece distribution

- 👻 **Ghost piece** – shows where the current piece will land

- 🔄 **Hold function** – set a piece aside for later use

- 🔲 **5x next-piece preview**

- ✨ **Particle system** on hard drops and line clears

- 📳 **Screen shake** and level-up effects

- 🌍 **14 languages**: Deutsch, English, Français, Español, Українська, Polski, Svenska, Italiano, Português, Русский, Ελληνικά, Nederlands, Türkçe, Čeština

- 🔊 Optional **sound effects** (requires `PyQt5.QtMultimedia`)

- 💾 **Highscore and settings persistence**, cross-platform (Windows/macOS/Linux)

- 🎚️ Three difficulty levels: Easy, Medium, Hard

## Download

Pre-built binaries are available on the [Releases page](https://github.com/%3Cyour-username%3E/%3Cyour-repo%3E/releases):

| Platform | File |
| - | - |
| 🪟 Windows | `Tetris.exe` |
| 🍎 macOS | `Tetris.dmg` |
| 🐧 Linux | `Tetris` (binary) |


## Controls

| Key | Action |
| - | - |
| `←` / `→` | Move piece left / right |
| `↓` | Soft drop (move down one row) |
| `↑` | Rotate piece |
| `Space` | Hard drop (instantly drop piece) |
| `C` | Hold (set piece aside / swap) |
| `P` | Pause |
| `Esc` | End game and return to menu |


In the menu: use the mouse to click, or arrow keys + `Enter` to navigate/start.

## Settings & save location

Settings (language, difficulty, volume, highscore) are saved automatically depending on platform:

- **Windows:** `%APPDATA%\\TetrisDeluxe\\settings.json`

- **macOS:** `~/Library/Application Support/TetrisDeluxe/settings.json`

- **Linux:** `~/.config/TetrisDeluxe/settings.json`

## Project structure

```
.  
├── Tetris.py            \# Main file – complete game (source)  
├── clear.wav            \# (optional) sound on line clear  
└── levelup.wav          \# (optional) sound on level-up├── clear.wav              
└── Tetris.icns             
└── Tetris.ico
```

## Known limitations

- The `Z` key (undo) exists as a placeholder but has no function yet.

## License

This project is released under the [Unlicense](https://unlicense.org/) — public domain. You're free to use, copy, modify, and distribute it for any purpose, commercial or private, with no conditions and no warranty.

## Contributing

Pull requests and issues are welcome! For larger changes, please open an issue first to discuss what you'd like to change.

