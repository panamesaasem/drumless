"""Remove drums from one audio file while retaining the original mix elsewhere."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

import julius
import numpy as np
import soundfile as sf
import torch
from demucs.api import Separator
from demucs.audio import AudioFile, convert_audio_channels


def pick_file() -> Path | None:
    """Show a file chooser for the Windows double-click workflow."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        name = filedialog.askopenfilename(
            title="Choose a song",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus"),
                ("All files", "*.*"),
            ],
        )
    finally:
        root.destroy()
    return Path(name) if name else None


def remove_drums(source: Path, destination: Path, model: str, device: str) -> None:
    """Subtract estimated drums from FFmpeg's native-rate decoded input."""
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and ffprobe must be installed and available on PATH.")

    audio = AudioFile(source)
    if len(audio) == 0:
        raise ValueError("The file contains no audio stream.")
    channels = audio.channels(0)
    if channels not in (1, 2):
        raise ValueError(f"Only mono and stereo files are supported (got {channels} channels).")
    sample_rate = audio.samplerate(0)

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {model} on {device}. The model is downloaded on first use.", flush=True)
    separator = Separator(model=model, device=device, progress=True)

    # FFmpeg honors MP3/AAC encoder delay metadata. Keep its native-rate decode
    # as the output baseline so non-drum sounds never undergo sample-rate conversion.
    original = audio.read(streams=0, channels=channels)
    if original.shape[-1] == 0:
        raise ValueError("The decoded audio is empty.")
    model_input = convert_audio_channels(original, separator.audio_channels)
    if sample_rate != separator.samplerate:
        model_input = julius.resample_frac(
            model_input, sample_rate, separator.samplerate, full=True
        )
    else:
        # Keep the native-rate baseline independent of Demucs' working tensor.
        model_input = model_input.clone()

    print("Separating drums...", flush=True)
    _, stems = separator.separate_tensor(model_input, sr=separator.samplerate)
    drums = stems["drums"]
    if sample_rate != separator.samplerate:
        drums = julius.resample_frac(
            drums,
            separator.samplerate,
            sample_rate,
            output_length=original.shape[-1],
        )

    if channels == 1:
        drums = drums.mean(dim=0, keepdim=True)
    samples = (original - drums).T.detach().cpu().numpy()
    if not np.isfinite(samples).all():
        raise RuntimeError("The model produced invalid audio samples.")

    peak = float(np.max(np.abs(samples)))
    if peak >= 1.0:
        gain = 0.99 / peak
        samples *= gain
        print(f"Reduced overall gain by {20 * np.log10(gain):.1f} dB to avoid clipping.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=".drumless-", suffix=".wav", dir=destination.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        sf.write(temporary_path, samples, sample_rate, subtype="PCM_24")
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    print(f"Saved: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove drums from a song and save a 24-bit WAV next to it."
    )
    parser.add_argument("source", nargs="?", type=Path, help="Input audio file")
    parser.add_argument("--pick", action="store_true", help="Choose the input with a file dialog")
    parser.add_argument("-o", "--output", type=Path, help="Output WAV path")
    parser.add_argument(
        "--model",
        choices=("htdemucs_ft", "htdemucs"),
        default="htdemucs_ft",
        help="Fine-tuned quality model (default) or faster base model",
    )
    parser.add_argument(
        "--device", choices=("auto", "cpu", "cuda"), default="auto"
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output")
    args = parser.parse_args()

    if args.source and args.pick:
        parser.error("Provide a path or --pick, not both.")
    source = pick_file() if args.pick else args.source
    if source is None:
        if args.pick:
            print("No file selected.")
            return 0
        parser.error("Provide an input file or use --pick.")
    source = source.expanduser().resolve()
    if not source.is_file():
        parser.error(f"Input file does not exist: {source}")

    destination = args.output or source.with_name(f"{source.stem} (no drums).wav")
    destination = destination.expanduser().resolve()
    if destination.suffix.lower() != ".wav":
        parser.error("The output file must have a .wav extension.")
    if destination == source:
        parser.error("The output path must differ from the input path.")
    if destination.exists() and not args.overwrite:
        parser.error(f"Output already exists: {destination} (use --overwrite)")

    try:
        remove_drums(source, destination, args.model, args.device)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
