# DANK Engine — TTS

Local text-to-speech pipeline for manhwa / manga / anime / movie recap videos and Shorts.

Two engines, chosen automatically by language:

- **English** → **Chatterbox** (MIT-licensed, expressive, zero-shot voice cloning)
- **All other languages** → **Edge-TTS** → **RVC** voice conversion

Every final file is mastered to mono 48 kHz, 16-bit PCM WAV with noise cleanup and -14 LUFS loudness.

## Requirements

- Python 3.10 - 3.13
- FFmpeg and FFprobe on PATH
- Internet on the first run (Chatterbox downloads its model weights from Hugging Face)

### Install FFmpeg

Windows:

```powershell
winget install Gyan.FFmpeg
```

macOS:

```bash
brew install ffmpeg
```

Ubuntu / Debian:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Setup

Chatterbox and RVC have conflicting dependency pins and cannot live in the same
virtual environment. Use two environments:

### Environment 1 — English (Chatterbox + Edge-TTS)

Windows:

```powershell
py -3.11 -m venv tts_env
tts_env\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv tts_env
source tts_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For an NVIDIA GPU, install the CUDA Torch build in place of the defaults:

```bash
python -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r requirements.txt
```

### Environment 2 — Non-English fallback (RVC)

```bash
python -m venv rvc_env
# activate as shown above
python -m pip install "pip<24.1"
python -m pip install -r requirements-rvc.txt
```

On GPU machines, install the CUDA Torch build first (see the command above).
On Linux, if `pyworld` / `fairseq` fail to build, install the system headers first:

```bash
sudo apt-get update && sudo apt-get install -y python3-dev build-essential
```

## Voice files

Place these under `models/`:

| File | Purpose |
| --- | --- |
| `english_reference.wav` | Chatterbox English voice clone, clean 3-15 seconds (5-10 recommended), no music/effects |
| `*.pth` | RVC model for non-English fallback |
| `*.index` | Optional RVC index file |

Use audio you have permission to use as a voice reference.

## Configuration

`config_tts.json` is created automatically on the first run. Common settings:

```json
{
  "PRIMARY_ENGINE": {
    "enabled": true,
    "languages": ["english", "en"],
    "reference_audio": "models/english_reference.wav",
    "narration": { "exaggeration": 0.65, "cfg_weight": 0.35 },
    "intro": { "exaggeration": 0.75, "cfg_weight": 0.3 }
  },
  "MASTERING": {
    "highpass_hz": 75,
    "denoise": true,
    "loudness_lufs": -14,
    "true_peak_dbtp": -1.5,
    "sample_rate": 48000
  }
}
```

- `exaggeration` — higher is more dramatic; `cfg_weight` — lower is slower and more deliberate.
- Set `PRIMARY_ENGINE.enabled` to `false` to route English through Edge-TTS + RVC as well.

## Story format

`story.json`:

```json
{
  "story": [
    {
      "render": true,
      "page": 2,
      "panel": 1,
      "shorts": true,
      "narration_english": "He finally came down the mountain.",
      "narration_spanish": "Por fin bajó de la montaña.",
      "intro_english": "This manhwa will keep you up all night!",
      "animation": "zoom_in",
      "sfx": "sword_unsheath",
      "bgm": "dark_tension",
      "transition": "fade"
    }
  ]
}
```

- `narration_<language>` and `intro_<language>` define the spoken text.
- `intro_*` is optional and only appears on some scenes.
- `"render": false` skips a scene.

## Run

```bash
python tts_engine.py
```

Output:

```text
audio/english/2_1.wav
audio/english/intro/2_1.wav
audio/spanish/2_1.wav
```

Audio filenames use `page_panel` so the video engine can match them to `page2_panel1` images.

### Running mixed-language stories

Because of the dependency split, generate the languages in two passes:

1. English with `tts_env`, `PRIMARY_ENGINE.enabled` = `true`.
2. Other languages with `rvc_env`, `PRIMARY_ENGINE.enabled` = `false`.

Already-generated files are cached and skipped on later runs, so the two passes
merge into one `audio/` tree.

## Available languages

75 configured languages.

Chatterbox: English.

Edge-TTS + RVC: Spanish, Hindi, Japanese, Korean, French, German, Chinese,
Portuguese, Russian, Arabic, Indonesian, Italian, Turkish, Vietnamese, Thai,
Polish, Dutch, Filipino, Bengali, Urdu, Tamil, Telugu, Marathi, Gujarati,
Malayalam, Kannada, Punjabi, Ukrainian, Greek, Czech, Romanian, Swedish,
Hungarian, Danish, Finnish, Norwegian, Bulgarian, Croatian, Slovak, Lithuanian,
Slovenian, Latvian, Estonian, Serbian, Afrikaans, Albanian, Amharic,
Azerbaijani, Bosnian, Burmese, Catalan, Galician, Georgian, Hebrew, Icelandic,
Irish, Javanese, Kazakh, Khmer, Lao, Macedonian, Malay, Maltese, Mongolian,
Nepali, Pashto, Persian, Sinhala, Somali, Sundanese, Swahili, Uzbek, Welsh, Zulu.

## Troubleshooting

- `403` from Edge-TTS — upgrade it (`python -m pip install "edge-tts>=7.3.1"`).
- Chatterbox import/load errors — recreate the environment with `requirements.txt` pinned versions.
- `Missing english reference` — add `models/english_reference.wav`.
- `Missing ffmpeg` — install FFmpeg and FFprobe, then reopen the terminal.
- First run is slow — model weights download once and are cached.
- Cached files skip generation — delete the file inside `audio/` to regenerate it.