import subprocess
import sys
import os

def main():
    """Interactively gathers arguments and runs the translation script."""
    # 1. Get video path
    video_path = input("Video path: ").strip()
    if not video_path:
        print("\nError: Video path cannot be empty.")
        sys.exit(1)

    # 2. Get language
    language = input("Language (e.g., en, id, fr, es, ja): ").strip()
    if not language:
        print("\nError: Language cannot be empty.")
        sys.exit(1)

    # 3. Get translate to
    translate_to = input("Translate to (e.g., en, id, fr, es, ja): ").strip()
    if not translate_to:
        print("\nError: 'Translate to' language cannot be empty.")
        sys.exit(1)

    # 4. Get min silence duration
    while True:
        min_silence_duration_str = input("Minimum silence duration (in ms, default 500): ").strip()
        if not min_silence_duration_str:
            min_silence_duration = 500
            break
        try:
            min_silence_duration = int(min_silence_duration_str)
            if min_silence_duration > 0:
                break
            print("Error: Please enter a positive number for duration.")
        except ValueError:
            print("Error: Invalid input. Please enter a whole number.")

    # 5. Get threshold
    while True:
        threshold_str = input("Threshold (0.1-1.0, default 0.5): ").strip()
        if not threshold_str:
            threshold = 0.5
            break
        try:
            threshold = float(threshold_str)
            if 0.1 <= threshold <= 1.0:
                break
            print("Error: Please enter a number between 0.1 and 1.0.")
        except ValueError:
            print("Error: Invalid input. Please enter a number.")

    # 6. Get library
    library = ""
    prompt = "Library [argos (faster, less accurate) | opus (heavier, more accurate)]: "
    while library not in ["argos", "opus"]:
        library = input(prompt).lower().strip()
        if library not in ["argos", "opus"] and library != "":
            print("Error: Invalid library. Please choose 'argos' or 'opus'.")

    # Construct the command
    script_name = f"tl_{library}.py"
    # Assuming `src` directory is relative to where `uv run` is executed.
    script_path = os.path.join("src", script_name)

    command = [
        "uv", "run", script_path, video_path,
        "--language", language, "--to", translate_to,
        "--vad-ms", str(min_silence_duration), "--vad-threshold", str(threshold)
    ]

    # Display the command to be executed
    display_command_parts = ["uv", "run", script_path, f'"{video_path}"'] + command[4:]
    print("\n" + "="*40)
    print(" Executing command:")
    print(f"  {' '.join(display_command_parts)}")
    print("="*40 + "\n")

    # Execute the command and stream output in real-time
    try:
        # Create a copy of the current environment and set PYTHONUTF8=1.
        # This forces the subprocess to use UTF-8 for its standard streams,
        # preventing UnicodeEncodeError on Windows when printing special
        # characters to the console.
        sub_env = os.environ.copy()
        sub_env["PYTHONUTF8"] = "1"

        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=sub_env,
            bufsize=1) as process:
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    print(line, end='')
            process.wait()
        if process.returncode == 0:
            return
        else:
            print(f"\nRun failed with exit code {process.returncode}.")
            sys.exit(process.returncode)
    except FileNotFoundError:
        print("\nError: 'uv' command not found. Make sure 'uv' is installed and in your PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
