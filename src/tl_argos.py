#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, sys
from pathlib import Path
from tqdm import tqdm
import srt
from datetime import timedelta

# Run example:
# uv run .\tl_argos.py "path/to/video.mp4" --language fr --to en --vad-ms 250 --vad-threshold 0.4

# Faster-Whisper (CUDA)
from faster_whisper import WhisperModel

# Argos Translate
import argostranslate.translate as argos
import argostranslate.package as argos_pkg

def run_ffmpeg_extract_wav(in_video: Path, out_wav: Path, sr=16000):
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_video),
        "-ac", "1", "-ar", str(sr),
        "-f", "wav", str(out_wav),
    ]
    subprocess.run(cmd, check=True)

def write_srt(segments, out_path: Path):
    subs = []
    for i, seg in enumerate(segments, start=1):
        subs.append(srt.Subtitle(
            index=i,
            start=timedelta(seconds=seg[0]),
            end=timedelta(seconds=seg[1]),
            content=seg[2].strip()
        ))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

def translate_srt(in_srt: Path, out_srt: Path, translator):
    with open(in_srt, "r", encoding="utf-8") as f:
        subs = list(srt.parse(f.read()))
    for sub in tqdm(subs, desc="Translating", unit="line"):
        sub.content = translator.translate(sub.content)
    with open(out_srt, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

def load_translator(src_lang: str, tgt_lang: str):
    installed = argos.get_installed_languages()
    langs = {lang.code: lang for lang in installed}
    if src_lang in langs and tgt_lang in langs:
        translator = langs[src_lang].get_translation(langs[tgt_lang])
        if translator:
            return translator
    return None

def ensure_argos_pair(src_lang: str, tgt_lang: str):
    """Return an Argos translator. If missing, auto-download the pair."""
    tr = load_translator(src_lang, tgt_lang)
    if tr:
        return tr

    # Try to find and install the pair
    print(f"Argos pair {src_lang}->{tgt_lang} not installed; downloading...")
    try:
        available = {
            f"{pkg.from_code}-{pkg.to_code}": pkg
            for pkg in argos_pkg.get_available_packages()
        }
        key = f"{src_lang}-{tgt_lang}"
        pkg = available.get(key)
        if not pkg:
            raise RuntimeError(
                f"No Argos package found for {key}. "
                f"Check available pairs or use a different target code."
            )
        model_path = pkg.download()  # downloads .argosmodel
        argos_pkg.install_from_path(model_path)
        print(f"Installed Argos package {key}")
    except Exception as e:
        raise RuntimeError(f"Failed to auto-install Argos {src_lang}->{tgt_lang}: {e}")

    tr = load_translator(src_lang, tgt_lang)
    if not tr:
        raise RuntimeError(f"Argos translator still unavailable for {src_lang}->{tgt_lang} after install.")
    return tr

def transcribe_to_segments(wav_path: Path, model_name: str, language: str, vad: bool, vad_ms: int, vad_threshold: float, beam_size: int, device: str, compute_type: str):
    model = WhisperModel(
        model_name,
        device=device,              # "cuda"
        compute_type=compute_type,  # e.g., "float16", "int8_float16"
    )
    segments, info = model.transcribe(
        str(wav_path),
        language=None if language.lower() == "auto" else language,
        vad_filter=vad,
        vad_parameters={
            "min_silence_duration_ms": vad_ms,
            "speech_pad_ms": 100,
            "threshold": vad_threshold,
        },
        beam_size=beam_size,
        temperature=0.0,
    )
    out = []
    for seg in segments:
        out.append((seg.start, seg.end, seg.text))
    return out, info

def main():
    p = argparse.ArgumentParser(description="GPU-accelerated local subtitles: transcribe (Faster-Whisper) + translate (Argos).")
    p.add_argument("video", type=Path, help="Input video file")
    p.add_argument("--model", default="large-v3", help="Whisper model (e.g., large-v3, distil-large-v3, medium, small)")
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    p.add_argument("--compute-type", default="float16", help="faster-whisper compute_type (e.g., float16, int8_float16)")
    p.add_argument("--language", default="auto", help="Source language code or 'auto' (e.g., en, ja, es)")
    p.add_argument("--to", required=True, help="Target language code for Argos (e.g., id, en, ja, es)")
    p.add_argument("--beam-size", type=int, default=5)
    p.add_argument("--vad-ms", type=int, default=500, help="VAD min_silence_duration_ms")
    p.add_argument("--vad-threshold", type=float, default=0.5, help="VAD speech probability threshold")
    p.add_argument("--no-vad", action="store_true", help="Disable VAD filter")
    args = p.parse_args()

    video = args.video
    if not video.exists():
        sys.exit(f"Input not found: {video}")

    base = video.with_suffix("")
    out_orig = Path(f"{base}.orig.srt")
    out_trans = Path(f"{base}.{args.to}.srt")

    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        print("Extracting audio with ffmpeg...")
        run_ffmpeg_extract_wav(video, wav)

        print(f"Transcribing with faster-whisper [{args.model}] on {args.device} ({args.compute_type})...")
        segments, info = transcribe_to_segments(
            wav, args.model, args.language, vad=(not args.no_vad),
            vad_ms=args.vad_ms, vad_threshold=args.vad_threshold,
            beam_size=args.beam_size, device=args.device,
            compute_type=args.compute_type
        )
        detected_lang = getattr(info, "language", None)
        duration = getattr(info, "duration", None)
        print(f"Detected language: {detected_lang or 'unknown'} | Duration: {duration or 'n/a'}s")

    print(f"Writing original subtitles → {out_orig}")
    write_srt(segments, out_orig)

    # Decide source language code for Argos
    src_code = (detected_lang if args.language.lower() == "auto" else args.language).split("-")[0]

    print(f"Preparing Argos translator {src_code}→{args.to} ...")
    translator = ensure_argos_pair(src_code, args.to)

    print(f"Translating → {out_trans}")
    translate_srt(out_orig, out_trans, translator)

    print("Done.")
    print(f"- Original:   {out_orig}")
    print(f"- Translated: {out_trans}")

if __name__ == "__main__":
    main()
