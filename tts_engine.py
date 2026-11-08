import os
import json
import asyncio
import glob
import shutil
import subprocess
import re
import math

# ================= 1. INSTANT FOLDER & FILE CREATION =================
DIRS = {
    "config": "config_tts.json",
    "story": "story.json",
    "models": "models",
    "cache_audio": "temp/cache_tts",
    "work_audio": "temp/master_tts",
    "final_audio": "audio"
}

print("Checking directories and files...")
for key, path in DIRS.items():
    if "." not in path and not os.path.exists(path): 
        os.makedirs(path)
        print(f"[+] Created missing folder: {path}")

# Auto-create Config with 75 Pre-Mapped Languages
if not os.path.exists(DIRS["config"]):
    default_conf = {
        "AUDIO_RATE": "+20%",
        "AUDIO_PITCH": "+0Hz",
        "RVC_SETTINGS": {"pitch_shift": 0, "index_rate": 0.75, "method": "rmvpe"},
        "PRIMARY_ENGINE": {
            "type": "chatterbox",
            "enabled": True,
            "languages": ["english", "en"],
            "reference_audio": "models/english_reference.wav",
            "max_chars": 350,
            "crossfade_ms": 80,
            "narration": {"exaggeration": 0.65, "cfg_weight": 0.35, "temperature": 0.8, "repetition_penalty": 1.2},
            "intro": {"exaggeration": 0.75, "cfg_weight": 0.3, "temperature": 0.8, "repetition_penalty": 1.2}
        },
        "MASTERING": {
            "highpass_hz": 75,
            "denoise": True,
            "denoise_db": 6,
            "loudness_lufs": -14,
            "true_peak_dbtp": -1.5,
            "sample_rate": 48000
        },
        "EDGE_SETTINGS": {"retries": 3, "retry_delay_seconds": 2, "circuit_breaker_failures": 5},
        "LANGUAGES": {
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
            "zulu": "zu-ZA-ThembaNeural"
        }
    }
    with open(DIRS["config"], "w", encoding="utf-8") as f:
        json.dump(default_conf, f, indent=4, ensure_ascii=False)
    print(f"[+] Created default {DIRS['config']}")

if not os.path.exists(DIRS["story"]):
    default_story = {
        "story": [
            {
                "render": True,
                "page": 1,
                "panel": 1,
                "shorts": 1,
                "narration_english": "This is a test. Paste your script here!"
            }
        ]
    }
    with open(DIRS["story"], "w", encoding="utf-8") as f:
        json.dump(default_story, f, indent=4, ensure_ascii=False)
    print(f"[+] Created blank template for {DIRS['story']}")

# ================= 2. SELF-HEALING IMPORTS =================
try:
    import torch
    if not hasattr(torch.utils._pytree, "register_pytree_node"):
        def patched_register_pytree_node(cls, flatten_fn, unflatten_fn, serialized_type_name=None):
            return torch.utils._pytree._register_pytree_node(cls, flatten_fn, unflatten_fn)
        torch.utils._pytree.register_pytree_node = patched_register_pytree_node
    
    # PyTorch 2.6+ Security Block Fix
    original_torch_load = torch.load
    def safe_torch_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    torch.load = safe_torch_load
except ImportError as e:
    raise SystemExit("PyTorch is required. Install the CPU or CUDA build appropriate for this machine.") from e

try:
    import edge_tts
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
except ImportError as e:
    raise SystemExit(f"Missing dependency: {e}. Install edge-tts>=7.3.1 and pydub.") from e

# ================= 3. STORY NORMALIZER =================
def normalize_story(story_data):
    normalized = {"story": []}
    for item in story_data.get("story", []):
        if item.get("render") is False:
            continue
            
        scene = {"page": item.get("page", 1), "panel": item.get("panel", 1), "text": {}, "intro": {}}
        
        for key in item:
            if key.startswith("narration_"):
                lang_name = key.replace("narration_", "")
                if item[key] and str(item[key]).strip():
                    scene["text"][lang_name] = item[key]
            elif key.startswith("intro_"):
                lang_name = key.replace("intro_", "")
                if item[key] and str(item[key]).strip():
                    scene["intro"][lang_name] = item[key]
        
        normalized["story"].append(scene)
    return normalized

# ================= 4. TTS + RVC GENERATION =================
def runtime_defaults():
    return {
        "PRIMARY_ENGINE": {
            "type": "chatterbox",
            "enabled": True,
            "languages": ["english", "en"],
            "reference_audio": "models/english_reference.wav",
            "max_chars": 350,
            "crossfade_ms": 80,
            "narration": {"exaggeration": 0.65, "cfg_weight": 0.35, "temperature": 0.8, "repetition_penalty": 1.2},
            "intro": {"exaggeration": 0.75, "cfg_weight": 0.3, "temperature": 0.8, "repetition_penalty": 1.2}
        },
        "MASTERING": {
            "highpass_hz": 75,
            "denoise": True,
            "denoise_db": 6,
            "loudness_lufs": -14,
            "true_peak_dbtp": -1.5,
            "sample_rate": 48000
        },
        "EDGE_SETTINGS": {"retries": 3, "retry_delay_seconds": 2, "circuit_breaker_failures": 5}
    }


def merge_defaults(config, defaults):
    for key, value in defaults.items():
        if isinstance(value, dict):
            target = config.setdefault(key, {})
            if isinstance(target, dict):
                merge_defaults(target, value)
        else:
            config.setdefault(key, value)
    return config


def require_audio_tools():
    missing = [tool for tool in ("ffmpeg", "ffprobe") if not shutil.which(tool)]
    if missing:
        raise RuntimeError(f"Missing required audio tools: {', '.join(missing)}")


def probe_audio(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels:format=duration", "-of", "json", path],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "ffprobe could not decode audio")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError("No audio stream found")
    return streams[0], float(data.get("format", {}).get("duration", 0))


def validate_audio(path, mastered_sample_rate=None):
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise ValueError("Audio file is missing or empty")
    stream, duration = probe_audio(path)
    if not math.isfinite(duration) or duration < 0.1:
        raise ValueError("Audio is empty or shorter than 100ms")
    if mastered_sample_rate is not None:
        if stream.get("codec_name") != "pcm_s16le":
            raise ValueError("Final audio must be 16-bit PCM WAV")
        if int(stream.get("sample_rate", 0)) != mastered_sample_rate or int(stream.get("channels", 0)) != 1:
            raise ValueError("Final audio must be mono at the configured sample rate")
    audio = AudioSegment.from_file(path)
    if len(audio) < 100 or not math.isfinite(audio.dBFS) or audio.dBFS < -60:
        raise ValueError("Audio is silent or too short")
    if mastered_sample_rate is not None and audio.max_dBFS > -0.1:
        raise ValueError("Final audio contains clipped peaks")
    return duration


def normalize_language(lang):
    return str(lang).strip().lower().replace("_", "-")


def uses_primary_engine(lang, cfg):
    if cfg["PRIMARY_ENGINE"].get("enabled", True) is False:
        return False
    normalized = normalize_language(lang)
    aliases = {normalize_language(item) for item in cfg["PRIMARY_ENGINE"].get("languages", [])}
    return normalized in aliases or ("-" in normalized and normalized.split("-", 1)[0] in aliases)


def job_paths(job):
    parts = [job["lang"]]
    if job["kind"] == "intro":
        parts.append("intro")
    final_dir = os.path.join(DIRS["final_audio"], *parts)
    source_dir = os.path.join(DIRS["work_audio"], job["engine"], *parts)
    cache_dir = os.path.join(DIRS["cache_audio"], *parts)
    return {
        "final": os.path.join(final_dir, f"{job['panel_id']}.wav"),
        "source": os.path.join(source_dir, f"{job['panel_id']}.source.wav"),
        "master_tmp": os.path.join(final_dir, f"{job['panel_id']}.tmp.wav"),
        "edge_cache": os.path.join(cache_dir, f"{job['panel_id']}.mp3"),
        "edge_smooth": os.path.join(source_dir, f"{job['panel_id']}.edge.wav")
    }


def build_jobs(story, cfg):
    jobs = []
    voice_map = cfg.get("LANGUAGES", {})
    for scene_index, scene in enumerate(story["story"], 1):
        page, panel = str(scene["page"]), str(scene["panel"])
        panel_id = f"{page}_{panel}"
        if not re.fullmatch(r"\d+_\d+", panel_id):
            print(f"[!] Scene {scene_index}: invalid page/panel '{panel_id}', skipped")
            continue
        for field, kind in (("text", "narration"), ("intro", "intro")):
            for lang in sorted(scene.get(field, {})):
                text = str(scene[field][lang]).strip()
                if not text:
                    continue
                if not re.fullmatch(r"[A-Za-z0-9-]+", lang):
                    print(f"[!] Scene {scene_index}: invalid language '{lang}', skipped")
                    continue
                primary = uses_primary_engine(lang, cfg)
                jobs.append({
                    "scene": scene_index,
                    "panel_id": panel_id,
                    "lang": lang,
                    "kind": kind,
                    "text": text,
                    "voice": voice_map.get(lang) or voice_map.get(normalize_language(lang)),
                    "engine": "chatterbox" if primary else "edge_rvc"
                })
    return jobs


def chunk_text(text, max_chars):
    text = " ".join(text.split())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces = []
    for sentence in sentences:
        while len(sentence) > max_chars:
            cut = sentence.rfind(" ", 0, max_chars + 1)
            if cut < 1:
                cut = max_chars
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            pieces.append(sentence)
    chunks = []
    current = ""
    for piece in pieces:
        candidate = f"{current} {piece}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = piece
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def join_waveforms(chunks, sample_rate, crossfade_ms):
    result = chunks[0].detach().cpu().flatten()
    fade_samples = int(sample_rate * crossfade_ms / 1000)
    for chunk in chunks[1:]:
        chunk = chunk.detach().cpu().flatten()
        count = min(fade_samples, len(result), len(chunk))
        if count < 2:
            result = torch.cat((result, chunk))
            continue
        positions = torch.linspace(0, math.pi / 2, count, dtype=result.dtype)
        overlap = result[-count:] * torch.cos(positions).square() + chunk[:count] * torch.sin(positions).square()
        result = torch.cat((result[:-count], overlap, chunk[count:]))
    return torch.clamp(result, -1.0, 1.0)


def loudnorm_filter(settings, measurements=None):
    loudness = settings["loudness_lufs"]
    peak = settings["true_peak_dbtp"]
    base = f"loudnorm=I={loudness}:TP={peak}:LRA=11"
    if measurements is None:
        return base + ":print_format=json"
    values = {
        "measured_I": measurements["input_i"],
        "measured_LRA": measurements["input_lra"],
        "measured_TP": measurements["input_tp"],
        "measured_thresh": measurements["input_thresh"],
        "offset": measurements["target_offset"]
    }
    return base + ":" + ":".join(f"{key}={value}" for key, value in values.items()) + ":linear=true"


def mastering_filters(settings):
    filters = [f"highpass=f={settings['highpass_hz']}"]
    if settings.get("denoise", True):
        filters.append(f"afftdn=nr={settings['denoise_db']}:nf=-50")
    filters.extend([
        "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB:start_silence=0.08",
        "areverse",
        "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB:start_silence=0.12",
        "areverse"
    ])
    return ",".join(filters)


def master_audio(source_path, final_path, tmp_path, cfg):
    settings = cfg["MASTERING"]
    sample_rate = int(settings["sample_rate"])
    filters = mastering_filters(settings)
    validate_audio(source_path)
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    try:
        measured = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", source_path, "-af", filters + "," + loudnorm_filter(settings), "-f", "null", "-"],
            capture_output=True,
            text=True
        )
        if measured.returncode != 0:
            raise RuntimeError(measured.stderr[-1500:])
        blocks = re.findall(r"\{[^{}]+\}", measured.stderr)
        measurements = None
        for block in reversed(blocks):
            candidate = json.loads(block)
            if "input_i" in candidate:
                measurements = candidate
                break
        if measurements is None:
            raise RuntimeError("FFmpeg did not return loudness measurements")
        second_filter = filters + "," + loudnorm_filter(settings, measurements)
        rendered = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-i", source_path, "-af", second_filter, "-ar", str(sample_rate), "-ac", "1", "-c:a", "pcm_s16le", tmp_path],
            capture_output=True,
            text=True
        )
        if rendered.returncode != 0:
            raise RuntimeError(rendered.stderr[-1500:])
        validate_audio(tmp_path, sample_rate)
        os.replace(tmp_path, final_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


class ChatterboxEngine:
    def __init__(self, device, cfg):
        self.settings = cfg["PRIMARY_ENGINE"]
        reference = self.settings["reference_audio"]
        if not os.path.isfile(reference):
            raise FileNotFoundError(f"English reference audio not found: {reference}")
        reference_duration = validate_audio(reference)
        if not 3 <= reference_duration <= 15:
            raise ValueError("English reference audio must be between 3 and 15 seconds")
        from chatterbox.tts import ChatterboxTTS
        import torchaudio
        self.torchaudio = torchaudio
        selected_device = "cuda" if device.startswith("cuda") else "cpu"
        self.model = ChatterboxTTS.from_pretrained(device=selected_device)
        self.model.prepare_conditionals(reference, exaggeration=self.settings["narration"]["exaggeration"])

    def generate(self, job, cfg):
        paths = job["paths"]
        os.makedirs(os.path.dirname(paths["source"]), exist_ok=True)
        settings = self.settings[job["kind"]]
        try:
            chunks = chunk_text(job["text"], int(self.settings["max_chars"]))
            generated = [
                self.model.generate(
                    chunk,
                    exaggeration=settings["exaggeration"],
                    cfg_weight=settings["cfg_weight"],
                    temperature=settings["temperature"],
                    repetition_penalty=settings["repetition_penalty"]
                )
                for chunk in chunks
            ]
            waveform = join_waveforms(generated, self.model.sr, int(self.settings["crossfade_ms"]))
            self.torchaudio.save(paths["source"], waveform.unsqueeze(0), self.model.sr)
            master_audio(paths["source"], paths["final"], paths["master_tmp"], cfg)
        finally:
            if os.path.exists(paths["source"]):
                os.remove(paths["source"])

    def release(self):
        self.model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class EdgeCircuit:
    def __init__(self, limit):
        self.limit = limit
        self.failures = 0

    @property
    def blocked(self):
        return self.failures >= self.limit

    def success(self):
        self.failures = 0

    def failure(self):
        self.failures += 1


async def generate_edge_base(job, cfg):
    paths = job["paths"]
    cache_path = paths["edge_cache"]
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 0:
        try:
            validate_audio(cache_path)
            return
        except Exception:
            os.remove(cache_path)
    settings = cfg["EDGE_SETTINGS"]
    attempts = int(settings["retries"])
    delay = float(settings["retry_delay_seconds"])
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            communicate = edge_tts.Communicate(job["text"], job["voice"], rate=cfg["AUDIO_RATE"], pitch=cfg["AUDIO_PITCH"])
            await communicate.save(cache_path)
            validate_audio(cache_path)
            return
        except Exception as e:
            last_error = e
            if os.path.exists(cache_path):
                os.remove(cache_path)
            if attempt < attempts:
                await asyncio.sleep(delay * (2 ** (attempt - 1)))
    raise RuntimeError(f"Edge-TTS failed after {attempts} attempts: {last_error}")


def smooth_edge_audio(job):
    paths = job["paths"]
    os.makedirs(os.path.dirname(paths["edge_smooth"]), exist_ok=True)
    audio = AudioSegment.from_mp3(paths["edge_cache"])
    chunks = split_on_silence(audio, min_silence_len=200, silence_thresh=audio.dBFS - 16, keep_silence=150)
    if chunks:
        audio = sum(chunks)
    audio = AudioSegment.silent(duration=150) + audio + AudioSegment.silent(duration=150)
    audio.export(paths["edge_smooth"], format="wav", parameters=["-c:a", "pcm_s16le"])
    validate_audio(paths["edge_smooth"])


async def generate_fallback(job, rvc, index_path, cfg, circuit):
    if not job["voice"]:
        raise RuntimeError(f"No Edge-TTS voice configured for language '{job['lang']}'")
    if circuit.blocked:
        raise RuntimeError("Edge-TTS circuit breaker is open after repeated failures")
    try:
        await generate_edge_base(job, cfg)
    except Exception:
        circuit.failure()
        raise
    circuit.success()
    paths = job["paths"]
    settings = cfg.get("RVC_SETTINGS", {})
    try:
        smooth_edge_audio(job)
        if index_path:
            rvc.index_file = index_path
        rvc.set_params(
            f0method=settings.get("method", "rmvpe"),
            pitch=settings.get("pitch_shift", 0),
            index_rate=settings.get("index_rate", 0.75)
        )
        await asyncio.to_thread(rvc.infer_file, paths["edge_smooth"], paths["source"])
        master_audio(paths["source"], paths["final"], paths["master_tmp"], cfg)
    finally:
        for key in ("source", "edge_smooth"):
            if os.path.exists(paths[key]):
                os.remove(paths[key])


def load_rvc(device):
    from rvc_python.infer import RVCInference
    model_files = sorted(glob.glob(os.path.join(DIRS["models"], "*.pth")))
    if not model_files:
        raise FileNotFoundError("Fallback jobs require an RVC .pth model inside models/")
    rvc = RVCInference(device=device)
    rvc.load_model(model_files[0])
    index_files = sorted(glob.glob(os.path.join(DIRS["models"], "*.index")))
    return rvc, index_files[0] if index_files else None


# ================= 5. MAIN PIPELINE =================
async def main():
    print("=" * 60)
    print("DANK ENGINE - TTS COMPLETE")
    print("=" * 60)
    require_audio_tools()
    with open(DIRS["config"], "r", encoding="utf-8") as f:
        config = json.load(f)
    merge_defaults(config, runtime_defaults())
    with open(DIRS["config"], "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    with open(DIRS["story"], "r", encoding="utf-8") as f:
        raw_story = json.load(f)
    story = normalize_story(raw_story)
    print(f"\n[✓] Loaded {len(story['story'])} renderable scenes from story.json")
    jobs = build_jobs(story, config)
    pending = []
    cached = 0
    sample_rate = int(config["MASTERING"]["sample_rate"])
    for job in jobs:
        job["paths"] = job_paths(job)
        final_path = job["paths"]["final"]
        try:
            validate_audio(final_path, sample_rate)
            print(f"    [{job['lang']}/{job['kind']}] ✓ {job['panel_id']} (cached)")
            cached += 1
        except Exception:
            if os.path.exists(final_path):
                os.remove(final_path)
            pending.append(job)
    primary_jobs = [job for job in pending if job["engine"] == "chatterbox"]
    fallback_jobs = [job for job in pending if job["engine"] == "edge_rvc"]
    print(f"[✓] Chatterbox English: {len(primary_jobs)} pending | Edge-TTS + RVC: {len(fallback_jobs)} pending")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"[✓] Using hardware: {device.upper()}")
    generated = 0
    failures = []

    def fail(job, error):
        message = f"{job['lang']}/{job['kind']} {job['panel_id']}: {error}"
        failures.append(message)
        print(f"    [{job['lang']}/{job['kind']}] ✗ {job['panel_id']}: {error}")

    if primary_jobs:
        engine = None
        try:
            engine = ChatterboxEngine(device, config)
            for job in primary_jobs:
                print(f"    [{job['lang']}/{job['kind']}] Chatterbox: {job['panel_id']}")
                try:
                    await asyncio.to_thread(engine.generate, job, config)
                    generated += 1
                except Exception as e:
                    fail(job, e)
        except Exception as e:
            for job in primary_jobs:
                if not os.path.exists(job["paths"]["final"]):
                    fail(job, f"Chatterbox initialization failed: {e}")
        finally:
            if engine is not None:
                engine.release()

    if fallback_jobs:
        try:
            rvc, index_path = load_rvc(device)
            circuit = EdgeCircuit(int(config["EDGE_SETTINGS"]["circuit_breaker_failures"]))
            for job in fallback_jobs:
                print(f"    [{job['lang']}/{job['kind']}] Edge-TTS + RVC: {job['panel_id']}")
                try:
                    await generate_fallback(job, rvc, index_path, config, circuit)
                    generated += 1
                except Exception as e:
                    fail(job, e)
        except Exception as e:
            for job in fallback_jobs:
                if not os.path.exists(job["paths"]["final"]):
                    fail(job, f"RVC initialization failed: {e}")

    print("\n" + "=" * 60)
    print(f"Generated: {generated} | Cached: {cached} | Failed: {len(failures)}")
    if failures:
        print("Failed audio:")
        for message in failures[:30]:
            print(f"  - {message}")
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more")
        raise SystemExit(1)
    print("✓ TTS GENERATION COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())