# Goober

A simple python script for transcribing and translating videos locally, combining Faster-Whisper transcription capability with Argos Translate/Opus-MT translation engine.  

No internet required* - everything is processed locally!  
<small><span style="color:gray" >
**after the dependencies and models are downloaded*
</span></small>


## Prerequisites

- **Python** 3.10.18 (specifically this version due to dependency constraints)
- **FFmpeg**: For audio extraction from videos
- **NVIDIA GPU**: For CUDA acceleration (optional, CPU is supported but slower)

## Quick Start

```bash
# 1. Navigate to project
cd goober

# 2. Initiate and activate virtual environment
uv venv --python 3.10.18
./venv/Scripts/activate

# 3. Sync dependencies
uv sync

# 4. Run interactive mode
uv run python main.py
```

> [!NOTE]  
> First run may take longer due to model downloads. All models are cached locally for future use.

## Installation

### 1. Install Python Dependencies
This project uses `uv` for fast Python package management:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh  # bash
# or
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"  # PowerShell

# Clone this repository
git clone https://github.com/narendnp/goober

# Navigate to project directory
cd goober

# Create a virtual environment
uv venv --python 3.10.18

# Activate the virtual environment
./venv/Scripts/activate  # bash
# or
./venv/Scripts/activate.ps1  # PowerShell

# Install dependencies
uv sync
```

> [!NOTE]  
> Make sure you have correct CUDA version for your GPU defined on the `pyproject.toml` file before running `uv sync`. For more information, go [here](https://pytorch.org/get-started/locally/).

### 2. Additional Setup for Opus-MT
If you plan to use Opus-MT translation engine, you need to install NLTK data:

```bash
# Enter Python environment
uv run python

# In Python interpreter:
>>> import nltk
>>> nltk.download('punkt_tab')
>>> exit()
```
For more information, go [here](/doc/nltk.md).

### 3. CUDA Setup
For GPU acceleration, ensure you have:
- NVIDIA GPU with CUDA support
- [CUDA toolkit](https://developer.nvidia.com/cuda-toolkit) installed
- PyTorch with CUDA support (already included in dependencies)
> [!NOTE]  
> Make sure you have correct CUDA version for your GPU defined on the `pyproject.toml` file. For more information, go [here](https://pytorch.org/get-started/locally/).


## Usage

### Interactive Mode
Inside the virtual environment, run the main script:

```bash
uv run python main.py
```

The script will prompt you for:
- **Video path**: Path to your input video file
- **Source language**: Language code (e.g., `en`, `fr`, `ja`) or `auto` for detection
- **Target language**: Desired translation language (e.g., `id`, `en`, `es`)
- **Silence duration**: Minimum silence duration for VAD (default: 500ms)
- **Threshold**: VAD sensitivity (0.1-1.0, default: 0.5)
- **Translation engine**: `argos` (faster) or `opus` (more accurate)

### Direct Script Usage
You can also run the script directly from the command line:

#### Argos Translate (Faster)
```bash
uv run src/tl_argos.py "path/to/video.mp4" \
  --language auto \
  --to en \
  --vad-ms 500 \
  --vad-threshold 0.5
```

#### Opus-MT (Higher Quality)
```bash
uv run src/tl_opus.py "path/to/video.mp4" \
  --language auto \
  --to en \
  --vad-ms 500 \
  --vad-threshold 0.5
```

> [!NOTE]  
> First run may take longer due to model downloads. All models are cached locally for future use.

## Configuration Options

### Common Parameters
- `--model`: Whisper model size (`large-v3`, `distil-large-v3`, `medium`, `small`)
  - Larger models are more accurate but slower
  - Default: `large-v3`
- `--device`: Processing device (`cuda` for GPU, `cpu` for CPU)
- `--compute-type`: Precision level (`float16`, `int8_float16`)
- `--language`: Source language code or `auto` for detection
- `--to`: Target language code (required)
- `--beam-size`: Beam search size for transcription (default: 5)

### Voice Activity Detection (VAD)
- `--vad-ms`: Minimum silence duration in milliseconds (default: 500)
- `--vad-threshold`: Speech detection sensitivity (0.1-1.0, default: 0.5)
- `--no-vad`: Disable VAD filtering

### Opus-MT Specific
- `--batch-size`: Translation batch size (default: 32)

## Supported Languages

Faster-Whisper, Argos Translate, and Opus-MT generally support a wide array of languages.  

These are some of the popular language codes:
- English: `en`
- Indonesian: `id`
- Spanish: `es`
- French: `fr`
- German: `de`
- Japanese: `ja`
- Chinese: `zh`
- Korean: `ko`
- Arabic: `ar`

Please refer to the respective library's documentation for more details.

## Output Files

The tool generates two subtitle files on the directory of the video file:
1. **Original transcription**: `{video_name}.orig.srt`
2. **Translated subtitles**: `{video_name}.{target_lang}.srt`

## Troubleshooting

**1. Failed to build/install fasttext libary (Windows)**  
  - Try installing it using the pre-built wheel (credit to [FKz11](https://github.com/FKz11/fasttext-0.9.3-windows-wheels))  

    Inside this repo's directory, run:

      ```bash
      uv pip install https://github.com/FKz11/fasttext-0.9.3-windows-wheels/releases/download/0.9.3/fasttext-0.9.3-cp310-cp310-win_amd64.whl
      ```
  - Re-run `uv sync`

## FAQ

**Q: Why is it named goober?**  
A: Because I can see how gooners would use this to generate subtitles to watch JAV. (*I know this doesn't explain it but I just think it's funny*).

**Q:**  
![Why](https://i.imgur.com/9O367V6.png)  
A: No.

## License

MIT License. See `LICENSE` file for details.

## Acknowledgments

- **[Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)**: Speech-to-text transcription
- **[Argos Translate](https://github.com/argosopentech/argos-translate)**: Fast translation library
- **[Opus-MT](https://github.com/Helsinki-NLP/Opus-MT)**: High-quality translation models
- **[FFmpeg](https://ffmpeg.org/)**: Audio/video processing
- **[UV](https://github.com/astral-sh/uv)**: Ultra-fast Python dependency management

