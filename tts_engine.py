"""Local multilingual TTS pipeline.

Routes each narration/intro clip to the best available engine:
  * Kokoro (local, MIT, GPU/CPU) for English, Spanish, French, Hindi,
    Italian, Portuguese, Japanese and Chinese.
  * Edge-TTS (online Microsoft neural voices) for every other language and
    as an automatic fallback whenever the local engine is unavailable.

Output is mastered to mono 48 kHz 16-bit PCM WAV at a consistent loudness.
"""

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRS = {
    "config": os.path.join(BASE_DIR, "config_tts.json"),
    "story": os.path.join(BASE_DIR, "story.json"),
    "cache": os.path.join(BASE_DIR, "temp", "cache_tts"),
    "final": os.path.join(BASE_DIR, "audio"),
}
CACHE_VERSION = "3"

# Kokoro voices confirmed present in hexgrad/Kokoro-82M.
LOCAL_LANGUAGES = {
    "english":    {"lang_code": "a", "voice": "af_heart"},
    "spanish":    {"lang_code": "e", "voice": "ef_dora"},
    "french":     {"lang_code": "f", "voice": "ff_siwis"},
    "hindi":      {"lang_code": "h", "voice": "hf_alpha"},
    "italian":    {"lang_code": "i", "voice": "if_sara"},
    "portuguese": {"lang_code": "p", "voice": "pf_dora"},
    "japanese":   {"lang_code": "j", "voice": "jf_alpha"},
    "chinese":    {"lang_code": "z", "voice": "zf_xiaobei"},
}

# Edge-TTS voices for every other language (fallback route).
EDGE_VOICES = {
    "english": "en-US-ChristopherNeural",
    "spanish": "es-MX-JorgeNeural",
    "hindi": "hi-IN-MadhurNeural",
    "japanese": "ja-JP-KeitaNeural",
    "korean": "ko-KR-InJoonNeural",
    "french": "fr-FR-HenriNeural",
    "german": "de-DE-ConradNeural",
    "chinese": "zh-CN-YunxiNeural",
    "portuguese": "pt-BR-AntonioNeural",
    "russian": "ru-RU-DmitryNeural",
    "arabic": "ar-SA-HamedNeural",
    "indonesian": "id-ID-ArdiNeural",
    "italian": "it-IT-DiegoNeural",
    "turkish": "tr-TR-AhmetNeural",
    "vietnamese": "vi-VN-NamMinhNeural",
    "thai": "th-TH-NiwatNeural",
    "polish": "pl-PL-MarekNeural",
    "dutch": "nl-NL-MaartenNeural",
    "filipino": "fil-PH-AngeloNeural",
    "bengali": "bn-IN-BashkarNeural",
    "urdu": "ur-PK-AsadNeural",
    "tamil": "ta-IN-ValluvarNeural",
    "telugu": "te-IN-MohanNeural",
    "marathi": "mr-IN-ManoharNeural",
    "gujarati": "gu-IN-NiranjanNeural",
    "malayalam": "ml-IN-MidhunNeural",
    "kannada": "kn-IN-GaganNeural",
    "punjabi": "pa-IN-SalmaNeural",
    "ukrainian": "uk-UA-OstapNeural",
    "greek": "el-GR-NestorasNeural",
    "czech": "cs-CZ-AntoninNeural",
    "romanian": "ro-RO-EmilNeural",
    "swedish": "sv-SE-MattiasNeural",
    "hungarian": "hu-HU-TamasNeural",
    "danish": "da-DK-JeppeNeural",
    "finnish": "fi-FI-HarriNeural",
    "norwegian": "nb-NO-FinnNeural",
    "bulgarian": "bg-BG-BorislavNeural",
    "croatian": "hr-HR-SreckoNeural",
    "slovak": "sk-SK-LukasNeural",
    "lithuanian": "lt-LT-LeonasNeural",
    "slovenian": "sl-SI-RokNeural",
    "latvian": "lv-LV-NilsNeural",
    "estonian": "et-EE-KertNeural",
    "serbian": "sr-RS-NicholasNeural",
    "afrikaans": "af-ZA-WillemNeural",
    "albanian": "sq-AL-IlirNeural",
    "amharic": "am-ET-AmehaNeural",
    "azerbaijani": "az-AZ-BabekNeural",
    "bosnian": "bs-BA-GoranNeural",
    "burmese": "my-MM-ThihaNeural",
    "catalan": "ca-ES-EnricNeural",
    "galician": "gl-ES-RoiNeural",
    "georgian": "ka-GE-GiorgiNeural",
    "hebrew": "he-IL-AvriNeural",
    "icelandic": "is-IS-GunnarNeural",
    "irish": "ga-IE-ColmNeural",
    "javanese": "jv-ID-DimasNeural",
    "kazakh": "kk-KZ-DauletNeural",
    "khmer": "km-KH-PisethNeural",
    "lao": "lo-LA-ChanthavongNeural",
    "macedonian": "mk-MK-AleksandarNeural",
    "malay": "ms-MY-OsmanNeural",
    "maltese": "mt-MT-JosephNeural",
    "mongolian": "mn-MN-BataaNeural",
    "nepali": "ne-NP-SagarNeural",
    "pashto": "ps-AF-GulNawazNeural",
    "persian": "fa-IR-FaridNeural",
    "sinhala": "si-LK-SameeraNeural",
    "somali": "so-SO-MuuseNeural",
    "sundanese": "su-ID-JajangNeural",
    "swahili": "sw-KE-RafikiNeural",
    "uzbek": "uz-UZ-SardorNeural",
    "welsh": "cy-GB-AledNeural",
    "zulu": "zu-ZA-ThembaNeural",
}


def defaults():
    return {
        "AUDIO_RATE": "+0%",
        "AUDIO_PITCH": "+0Hz",
        "LOCAL": {"enabled": True, "speed": 1.0, "languages": LOCAL_LANGUAGES},
        "MASTERING": {
            "highpass_hz": 75,
            "loudness_lufs": -14,
            "true_peak_dbtp": -1.5,
            "sample_rate": 48000,
        },
        "EDGE_SETTINGS": {
            "retries": 3,
            "retry_delay_seconds": 2,
            "concurrency": 6,
            "timeout_seconds": 60,
        },
        "LANGUAGES": dict(EDGE_VOICES),
    }


def merge_defaults(config, fallback):
    for key, value in fallback.items():
        if key not in config:
            config[key] = value
        elif isinstance(value, dict) and isinstance(config[key], dict):
            merge_defaults(config[key], value)
    return config


def load_config():
    if not os.path.isfile(DIRS["config"]):
        config = defaults()
        with open(DIRS["config"], "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"Created default {DIRS['config']}")
        return config
    with open(DIRS["config"], encoding="utf-8") as f:
        config = json.load(f)
    return merge_defaults(config, defaults())


def load_story():
    if not os.path.isfile(DIRS["story"]):
        template = {
            "story": [{
                "render": True,
                "page": 1,
                "panel": 1,
                "narration_english": "This is a test. Paste your script here!",
                "narration_spanish": "Esta es una prueba. ¡Pega tu guion aquí!",
            }]
        }
        with open(DIRS["story"], "w", encoding="utf-8") as f:
            json.dump(template, f, indent=4, ensure_ascii=False)
        print(f"Created blank template {DIRS['story']}")
        return template
    with open(DIRS["story"], encoding="utf-8") as f:
        return json.load(f)


def require_ffmpeg():
    missing = [tool for tool in ("ffmpeg", "ffprobe") if not shutil.which(tool)]
    if missing:
        raise SystemExit(
            "FFmpeg/FFprobe are required but not found on PATH. "
            "Install FFmpeg (https://ffmpeg.org) and re-run."
        )


def detect_device():
    try:
        import torch
    except ImportError:
        return "cpu", False
    if torch.cuda.is_available():
        return "cuda", True
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps", True
    return "cpu", False


# --------------------------------------------------------------------------- #
# Story -> jobs
# --------------------------------------------------------------------------- #
def normalize_language(lang):
    return str(lang).strip().lower().replace("_", "-")


def normalize_story(story):
    scenes = []
    for item in story.get("story", []):
        if item.get("render") is False:
            continue
        scene = {
            "page": str(item.get("page", 1)),
            "panel": str(item.get("panel", 1)),
            "narration": {},
            "intro": {},
        }
        for key, value in item.items():
            text = str(value).strip() if isinstance(value, str) else ""
            if not text:
                continue
            if key.startswith("narration_"):
                scene["narration"][key[len("narration_"):]] = text
            elif key.startswith("intro_"):
                scene["intro"][key[len("intro_"):]] = text
        scenes.append(scene)
    return scenes


def build_jobs(scenes, config):
    jobs = []
    local_langs = {normalize_language(k): v for k, v in config["LOCAL"]["languages"].items()}
    edge_voices = config["LANGUAGES"]

    for scene in scenes:
        panel_id = f"{scene['page']}_{scene['panel']}"
        if not re.fullmatch(r"\d+_\d+", panel_id):
            raise ValueError(f"Invalid page/panel for scene, skipping render of: {panel_id}")

        for field, kind in (("narration", "narration"), ("intro", "intro")):
            for lang, text in scene[field].items():
                norm = normalize_language(lang)
                edge_voice = edge_voices.get(lang) or edge_voices.get(norm)
                use_local = config["LOCAL"].get("enabled", True) and norm in local_langs
                voice = local_langs[norm]["voice"] if use_local else edge_voice
                jobs.append({
                    "panel_id": panel_id,
                    "lang": lang,
                    "norm": norm,
                    "kind": kind,
                    "text": text,
                    "engine": "local" if use_local else "edge",
                    "voice": voice,
                    "lang_code": local_langs[norm]["lang_code"] if use_local else None,
                })
    return jobs


def ensure_unique(jobs):
    seen = {}
    result = []
    for job in jobs:
        key = (job["lang"], job["kind"], job["panel_id"])
        if key in seen:
            raise ValueError(f"Duplicate narration for {key[0]}/{key[1]} {key[2]}")
        seen[key] = True
        result.append(job)
    return result


# --------------------------------------------------------------------------- #
# Paths + caching
# --------------------------------------------------------------------------- #
def job_paths(job):
    parts = [job["lang"]]
    if job["kind"] == "intro":
        parts.append("intro")
    final_dir = os.path.join(DIRS["final"], *parts)
    return {
        "final": os.path.join(final_dir, f"{job['panel_id']}.wav"),
        "master_tmp": os.path.join(final_dir, f"{job['panel_id']}.tmp.wav"),
        "edge_cache": os.path.join(DIRS["cache"], *parts, f"{job['panel_id']}.mp3"),
        "local_src": os.path.join(DIRS["cache"], "_src", f"{job['lang']}_{job['panel_id']}.wav"),
    }


def job_hash(job, config, edge_voice):
    token = json.dumps({
        "v": CACHE_VERSION,
        "lang": job["lang"],
        "kind": job["kind"],
        "panel": job["panel_id"],
        "text": job["text"],
        "engine": job["engine"],
        "voice": job["voice"],
        "lang_code": job["lang_code"],
        "rate": config["AUDIO_RATE"],
        "pitch": config["AUDIO_PITCH"],
        "local_speed": config["LOCAL"].get("speed", 1.0),
        "mastering": config["MASTERING"],
        "edge_voice": edge_voice,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def load_manifest():
    path = os.path.join(DIRS["cache"], "manifest.json")
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("entries", {})
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_manifest(entries):
    os.makedirs(DIRS["cache"], exist_ok=True)
    tmp = os.path.join(DIRS["cache"], "manifest.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": CACHE_VERSION, "entries": entries}, f)
    os.replace(tmp, os.path.join(DIRS["cache"], "manifest.json"))


# --------------------------------------------------------------------------- #
# Audio helpers
# --------------------------------------------------------------------------- #
def run_ffmpeg(args, timeout=120):
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-y", *args],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:] or "ffmpeg failed")
    return result


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_name,sample_rate,channels:format=duration",
         "-of", "json", path],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe could not decode audio")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise RuntimeError("No audio stream found")
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    return streams[0], duration


def validate_wav(path, sample_rate):
    import numpy as np
    import soundfile as sf
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise RuntimeError("Audio file missing or empty")
    info = sf.info(path)
    if info.samplerate != sample_rate or info.channels != 1:
        raise RuntimeError("Final audio must be mono at the configured sample rate")
    data, _ = sf.read(path, dtype="float32", always_2d=False)
    if data.size == 0 or info.duration < 0.1:
        raise RuntimeError("Audio too short")
    peak = float(np.max(np.abs(data)))
    if peak < 1e-3:
        raise RuntimeError("Audio is silent")
    if peak > 1.0:
        raise RuntimeError("Audio is clipped")
    return info.duration


def master_audio(source_path, final_path, config):
    settings = config["MASTERING"]
    sample_rate = int(settings["sample_rate"])
    highpass = int(settings["highpass_hz"])
    loudness = settings["loudness_lufs"]
    peak = settings["true_peak_dbtp"]

    base = f"loudnorm=I={loudness}:TP={peak}:LRA=11"
    filters = f"highpass=f={highpass}" if highpass > 0 else "anull"

    # Pass 1: measure loudness.
    result = run_ffmpeg(
        ["-i", source_path, "-af", f"{filters},{base}:print_format=json", "-f", "null", "-"]
    )
    blocks = re.findall(r"\{[^{}]+\}", result.stderr)
    measurement = None
    for block in reversed(blocks):
        try:
            candidate = json.loads(block)
        except json.JSONDecodeError:
            continue
        if "input_i" in candidate:
            measurement = candidate
            break
    if measurement is None:
        raise RuntimeError("FFmpeg returned no loudness measurement")

    linear = (f"{base}:measured_I={measurement['input_i']}"
              f":measured_LRA={measurement['input_lra']}"
              f":measured_TP={measurement['input_tp']}"
              f":measured_thresh={measurement['input_thresh']}"
              f":offset={measurement['target_offset']}:linear=true")

    stem = os.path.splitext(final_path)[0]
    tmp = f"{stem}.tmp.wav"
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
        run_ffmpeg([
            "-i", source_path, "-af", f"{filters},{linear}",
            "-ar", str(sample_rate), "-ac", "1", "-c:a", "pcm_s16le", tmp,
        ])
        validate_wav(tmp, sample_rate)
        os.replace(tmp, final_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# --------------------------------------------------------------------------- #
# Local engine (Kokoro)
# --------------------------------------------------------------------------- #
class LocalEngine:
    def __init__(self, device, config):
        try:
            from kokoro import KPipeline, KModel
        except Exception as exc:
            raise RuntimeError(f"Kokoro not installed: {exc}") from exc
        self.kokoro_device = "cuda" if device == "cuda" else "cpu"
        self.speed = float(config["LOCAL"].get("speed", 1.0))
        self.KPipeline = KPipeline
        self.pipelines = {}
        self._failed = set()
        try:
            # One shared model keeps GPU/CPU memory flat across languages.
            self.model = KModel(repo_id="hexgrad/Kokoro-82M").to(self.kokoro_device).eval()
        except BaseException as exc:
            if isinstance(exc, KeyboardInterrupt):
                raise
            raise RuntimeError(f"Kokoro model load failed: {exc}") from exc

    def _pipeline(self, lang_code):
        if lang_code in self._failed:
            raise RuntimeError(f"Kokoro language '{lang_code}' unavailable")
        if lang_code not in self.pipelines:
            try:
                self.pipelines[lang_code] = self.KPipeline(lang_code=lang_code, model=self.model)
            except BaseException as exc:
                if isinstance(exc, KeyboardInterrupt):
                    raise
                self._failed.add(lang_code)
                raise RuntimeError(f"Kokoro language '{lang_code}' unavailable: {exc}") from exc
        return self.pipelines[lang_code]

    def generate(self, job, config):
        import numpy as np
        import soundfile as sf
        import torch
        try:
            pipe = self._pipeline(job["lang_code"])
            chunks = []
            for result in pipe(job["text"], voice=job["voice"], speed=self.speed):
                audio = result.audio
                if audio is None:
                    continue
                chunks.append(audio.detach().cpu())
            if not chunks:
                raise RuntimeError("Local engine produced no audio")
            wave = torch.cat(chunks).float().numpy()
            wave = np.clip(wave, -1.0, 1.0)
            src = job["paths"]["local_src"]
            os.makedirs(os.path.dirname(src), exist_ok=True)
            sf.write(src, wave, 24000)
            master_audio(src, job["paths"]["final"], config)
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            if os.path.exists(job["paths"]["local_src"]):
                os.remove(job["paths"]["local_src"])


def kokoro_available():
    try:
        import kokoro  # noqa: F401
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Edge-TTS
# --------------------------------------------------------------------------- #
async def edge_generate(job, config):
    import edge_tts
    paths = job["paths"]
    cache = paths["edge_cache"]
    if os.path.isfile(cache) and os.path.getsize(cache) > 0:
        return cache

    settings = config["EDGE_SETTINGS"]
    retries = max(1, int(settings["retries"]))
    delay = max(0.0, float(settings["retry_delay_seconds"]))
    os.makedirs(os.path.dirname(cache), exist_ok=True)

    last_error = None
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(
                job["text"], job["voice"], rate=config["AUDIO_RATE"], pitch=config["AUDIO_PITCH"]
            )
            await communicate.save(cache)
            probe(cache)
            return cache
        except Exception as exc:
            last_error = exc
            if os.path.exists(cache):
                os.remove(cache)
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))
    raise RuntimeError(f"Edge-TTS failed: {last_error}")


async def generate_edge_job(job, config):
    if not job["voice"]:
        raise RuntimeError(f"No voice configured for language '{job['lang']}'")
    source = await edge_generate(job, config)
    await asyncio.to_thread(master_audio, source, job["paths"]["final"], config)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
async def main():
    print("=" * 60)
    print("TTS PIPELINE")
    print("=" * 60)

    require_ffmpeg()
    device, accelerated = detect_device()

    config = load_config()
    scenes = normalize_story(load_story())
    jobs = ensure_unique(build_jobs(scenes, config))
    print(f"Loaded {len(scenes)} scenes -> {len(jobs)} audio clips")

    manifest = load_manifest()

    pending = []
    cached = 0
    sample_rate = int(config["MASTERING"]["sample_rate"])
    for job in jobs:
        edge_voice = (config["LANGUAGES"].get(job["lang"])
                      or config["LANGUAGES"].get(job["norm"]))
        job["paths"] = job_paths(job)
        job["hash"] = job_hash(job, config, edge_voice)
        job["edge_voice"] = edge_voice
        if job["engine"] == "edge":
            job["voice"] = edge_voice
        rel = os.path.relpath(job["paths"]["final"], BASE_DIR)
        if (manifest.get(rel) == job["hash"] and os.path.isfile(job["paths"]["final"])):
            try:
                validate_wav(job["paths"]["final"], sample_rate)
                cached += 1
                continue
            except Exception:
                pass
        pending.append(job)

    print(f"Cached: {cached} | To generate: {len(pending)}")

    local_ok = kokoro_available() if pending else False
    if accelerated:
        print(f"Hardware: {device.upper()} (accelerated)")
    else:
        print(f"Hardware: {device.upper()} (CPU)")

    # Split by engine.
    local_jobs = [j for j in pending if j["engine"] == "local"]
    edge_jobs = [j for j in pending if j["engine"] == "edge"]

    local_engine = None
    if local_jobs:
        if local_ok and config["LOCAL"].get("enabled", True):
            try:
                local_engine = LocalEngine(device, config)
            except Exception as exc:
                print(f"[!] Local engine unavailable, using Edge voices: {exc}")
                local_engine = None
        else:
            local_ok = False

    failures = []
    generated = 0
    saves = 0

    def record():
        nonlocal saves
        saves += 1
        if saves % 25 == 0:
            save_manifest(manifest)

    # Generate local jobs; fall back to Edge on failure.
    to_edge = []
    for job in local_jobs:
        if local_engine is None:
            if job["edge_voice"]:
                job["engine"] = "edge"
                job["voice"] = job["edge_voice"]
                to_edge.append(job)
            else:
                failures.append(f"{job['lang']}/{job['kind']} {job['panel_id']}: no local or Edge voice")
            continue
        try:
            await asyncio.to_thread(local_engine.generate, job, config)
            generated += 1
            print(f"  ok  local  {job['lang']}/{job['kind']} {job['panel_id']}")
            rel = os.path.relpath(job["paths"]["final"], BASE_DIR)
            manifest[rel] = job["hash"]
            record()
        except Exception as exc:
            print(f"  retry-edge {job['lang']}/{job['kind']} {job['panel_id']}: {exc}")
            if job["edge_voice"]:
                job["engine"] = "edge"
                job["voice"] = job["edge_voice"]
                to_edge.append(job)
            else:
                failures.append(f"{job['lang']}/{job['kind']} {job['panel_id']}: {exc}")

    edge_jobs.extend(to_edge)

    # Edge jobs run concurrently with a bounded pool.
    if edge_jobs:
        sem = asyncio.Semaphore(max(1, int(config["EDGE_SETTINGS"]["concurrency"])))
        async def edge_worker(job):
            nonlocal generated
            async with sem:
                try:
                    await generate_edge_job(job, config)
                    generated += 1
                    print(f"  ok  edge   {job['lang']}/{job['kind']} {job['panel_id']}")
                    rel = os.path.relpath(job["paths"]["final"], BASE_DIR)
                    manifest[rel] = job["hash"]
                    record()
                except Exception as exc:
                    failures.append(f"{job['lang']}/{job['kind']} {job['panel_id']}: {exc}")
                    print(f"  FAIL edge   {job['lang']}/{job['kind']} {job['panel_id']}: {exc}")
        await asyncio.gather(*(edge_worker(j) for j in edge_jobs))

    save_manifest(manifest)

    print("=" * 60)
    print(f"Generated: {generated} | Cached: {cached} | Failed: {len(failures)}")
    if failures:
        for message in failures[:40]:
            print(f"  - {message}")
        if len(failures) > 40:
            print(f"  ... and {len(failures) - 40} more")
        raise SystemExit(1)
    print("Complete.")


if __name__ == "__main__":
    asyncio.run(main())