import os
import sys
import subprocess
import json
import asyncio
import glob
import shutil

# ================= 1. INSTANT FOLDER & FILE CREATION =================
DIRS = {
    "config": "config_tts.json",
    "story": "story.json",
    "models": "models",
    "cache_audio": "temp/cache_tts",
    "final_audio": "output/audio"
}

print("Checking directories and files...")
for key, path in DIRS.items():
    if "." not in path and not os.path.exists(path): 
        os.makedirs(path)
        print(f"[+] Created missing folder: {path}")

# Auto-create Config with 74 Pre-Mapped Languages
if not os.path.exists(DIRS["config"]):
    default_conf = {
        "AUDIO_RATE": "+20%",
        "AUDIO_PITCH": "+0Hz",
        "RVC_SETTINGS": {"pitch_shift": 0, "index_rate": 0.75, "method": "rmvpe"},
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
except ImportError:
    print("[!] Torch not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch"])
    import torch

try:
    import edge_tts
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    from rvc_python.infer import RVCInference
except AttributeError as e:
    if "coverage" in str(e):
        print("\n[!] Numba/Coverage bug detected.")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "coverage", "numba"])
        print("\n[+] FIX APPLIED SUCCESSFULLY! Please run the script one more time.")
        sys.exit(0)
    else:
        raise
except ImportError as e:
    print(f"\n[!] Missing Library: {e}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts", "pydub", "rvc-python"])
    print("\n[+] Installed missing libraries! Please run the script again.")
    sys.exit(0)

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
                scene["text"][lang_name] = item[key]
            elif key.startswith("intro_"):
                lang_name = key.replace("intro_", "")
                if item[key] and str(item[key]).strip():
                    scene["intro"][lang_name] = item[key]
        
        normalized["story"].append(scene)
    return normalized

# ================= 4. TTS + RVC GENERATION =================
def finalize_audio(tmp_path, final_path, label):
    try:
        audio = AudioSegment.from_file(tmp_path)
        if os.path.getsize(tmp_path) == 0 or len(audio) < 100:
            raise ValueError("audio empty or too short")
        os.replace(tmp_path, final_path)
        return True
    except Exception as e:
        print(f"    [{label}] ✗ Validation failed: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False

async def generate_audio(rvc, text, lang, voice, panel_id, cfg, index_path, subdir=""):
    temp_dir = os.path.join(DIRS["cache_audio"], lang, subdir) if subdir else os.path.join(DIRS["cache_audio"], lang)
    final_dir = os.path.join(DIRS["final_audio"], lang, subdir) if subdir else os.path.join(DIRS["final_audio"], lang)
    
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)
    
    tts_path = os.path.join(temp_dir, f"{panel_id}.mp3")
    rvc_path = os.path.join(final_dir, f"{panel_id}.wav")
    tmp_rvc_path = os.path.join(final_dir, f"{panel_id}.tmp.wav")

    label = f"{lang}/{subdir}" if subdir else lang

    if os.path.exists(rvc_path):
        if os.path.getsize(rvc_path) > 0:
            print(f"    [{label}] ✓ {panel_id} (cached)")
            return
        os.remove(rvc_path)

    try:
        # Generate base TTS
        comm = edge_tts.Communicate(text, voice, rate=cfg["AUDIO_RATE"], pitch=cfg["AUDIO_PITCH"])
        await comm.save(tts_path)
        
        # Open in PyDub for silence stripping
        audio = AudioSegment.from_mp3(tts_path)
        
        # Keep 150ms of natural silence so word tails don't clip
        chunks = split_on_silence(audio, min_silence_len=200, silence_thresh=audio.dBFS-16, keep_silence=150)
        
        if chunks:
            audio = sum(chunks)
            
        # Add a snappy 0.15-second (150ms) buffer to beginning and end
        padding = AudioSegment.silent(duration=150)
        audio = padding + audio + padding
        
        # Save smoothed audio
        audio.export(tts_path, format="mp3")
        print(f"    [{label}] TTS Generated & Smoothed: {panel_id}")
    except Exception as e:
        print(f"    [{label}] ✗ TTS Error: {e}")
        return

    try:
        if index_path:
            rvc.index_file = index_path
            
        pitch = cfg.get("RVC_SETTINGS", {}).get("pitch_shift", 0)
        method = cfg.get("RVC_SETTINGS", {}).get("method", "rmvpe")
        index_rate = cfg.get("RVC_SETTINGS", {}).get("index_rate", 0.75)
        
        rvc.set_params(f0method=method, pitch=pitch, index_rate=index_rate)
        rvc.infer_file(tts_path, tmp_rvc_path)
        if finalize_audio(tmp_rvc_path, rvc_path, label):
            print(f"    [{label}] ✓ RVC Complete: {panel_id}")
        else:
            raise RuntimeError("RVC output invalid")
    except Exception as e:
        print(f"    [{label}] ✗ RVC Error: {e}, using raw TTS fallback")
        try:
            shutil.copy(tts_path, tmp_rvc_path)
            finalize_audio(tmp_rvc_path, rvc_path, label)
        except Exception as copy_err:
            print(f"    [{label}] ✗ Fallback failed: {copy_err}")

# ================= 5. MAIN PIPELINE =================
async def main():
    print("=" * 60)
    print("DANK ENGINE - TTS COMPLETE")
    print("=" * 60)
    
    pth_files = glob.glob(os.path.join(DIRS["models"], "*.pth"))
    if not pth_files:
        print("\n[!] Missing RVC Model. Please put your .pth file inside the 'models' folder!")
        return

    with open(DIRS["config"], "r", encoding="utf-8") as f:
        config = json.load(f)
    with open(DIRS["story"], "r", encoding="utf-8") as f:
        raw_story = json.load(f)
    
    story = normalize_story(raw_story)
    print(f"\n[✓] Loaded {len(story['story'])} renderable scenes from story.json")
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"[✓] Using hardware: {device.upper()}")
    
    try:
        rvc = RVCInference(device=device)
        rvc.load_model(pth_files[0])
    except Exception as e:
        print(f"[✗] RVC Load Error: {e}")
        return
    
    index_files = glob.glob(os.path.join(DIRS["models"], "*.index"))
    index_path = index_files[0] if index_files else None
    
    detected_languages = set()
    for item in story["story"]:
        detected_languages.update(item["text"].keys())
        detected_languages.update(item.get("intro", {}).keys())
    
    voice_map = config.get("LANGUAGES", {})
    # Fallback dictionary internally just in case a language gets called that isn't in config
    fallback_voice = "en-US-ChristopherNeural"
    
    print("\n" + "=" * 60)
    total_scenes = len(story["story"])
    
    for idx, scene in enumerate(story["story"], 1):
        # EXACT FIX: changed "pageX_panelY" to "X_Y" so engine.py can find it!
        panel_id = f"{scene['page']}_{scene['panel']}"
        print(f"[Scene {idx}/{total_scenes}] Panel ID: {panel_id}")
        
        for lang in detected_languages:
            text = scene["text"].get(lang)
            if text and text.strip():
                # Uses mapped voice, or defaults to English if missing
                voice = voice_map.get(lang, fallback_voice)
                await generate_audio(rvc, text, lang, voice, panel_id, config, index_path)
        
        for lang, intro_text in scene.get("intro", {}).items():
            if intro_text and str(intro_text).strip():
                voice = voice_map.get(lang, fallback_voice)
                await generate_audio(rvc, intro_text, lang, voice, panel_id, config, index_path, subdir="intro")
    print("\n✓ TTS GENERATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())