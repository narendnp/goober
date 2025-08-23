#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, sys
from pathlib import Path
from tqdm import tqdm
import srt
from datetime import timedelta

# Run example:
# uv run .\tl_opus.py "path/to/video.mp4" --language fr --to en --vad-ms 250 --vad-threshold 0.4

# Faster-Whisper (CUDA)
from faster_whisper import WhisperModel

# Opus-MT
from easynmt import EasyNMT
import nltk

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

def translate_srt_opus(in_srt: Path, out_srt: Path, translator: EasyNMT, src_lang: str, tgt_lang: str, batch_size: int):
    with open(in_srt, "r", encoding="utf-8") as f:
        subs = list(srt.parse(f.read()))
    
    sentences = [sub.content for sub in subs]
    
    translated_sentences = translator.translate(
        sentences,
        source_lang=src_lang,
        target_lang=tgt_lang,
        batch_size=batch_size,
        show_progress_bar=True
    )
    
    for i, sub in enumerate(subs):
        sub.content = translated_sentences[i]
        
    with open(out_srt, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

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
    p = argparse.ArgumentParser(description="GPU-accelerated local subtitles: transcribe (Faster-Whisper) + translate (Opus-MT).")
    p.add_argument("video", type=Path, help="Input video file")
    p.add_argument("--model", default="large-v3", help="Whisper model (e.g., large-v3, distil-large-v3, medium, small)")
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    p.add_argument("--compute-type", default="float16", help="faster-whisper compute_type (e.g., float16, int8_float16)")
    p.add_argument("--language", default="auto", help="Source language code or 'auto' (e.g., en, ja, es)")
    p.add_argument("--to", required=True, help="Target language code for Opus-MT (e.g., id, en, ja, es)")
    p.add_argument("--batch-size", type=int, default=32, help="Batch size for translation")
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

    # Decide source language code for Opus-MT
    src_code = (detected_lang if args.language.lower() == "auto" else args.language).split("-")[0]

    # Ensure NLTK data is available
    try:
        nltk.data.find('tokenizers/punkt')
    except nltk.downloader.DownloadError:
        print("NLTK 'punkt' resource not found. Downloading...")
        nltk.download('punkt', quiet=True)

    print(f"Preparing Opus-MT translator {src_code}→{args.to} ...")
    translator = EasyNMT("Opus-MT", device=args.device)

    print(f"Translating → {out_trans}")
    translate_srt_opus(out_orig, out_trans, translator, src_code, args.to, args.batch_size)

    print("Done.")
    print(f"- Original:   {out_orig}")
    print(f"- Translated: {out_trans}")

if __name__ == "__main__":
    main()
