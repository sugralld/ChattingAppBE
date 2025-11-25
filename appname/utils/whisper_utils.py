import whisper
import tempfile
import os
import shutil

try:
    import imageio_ffmpeg
except Exception:
    imageio_ffmpeg = None


def ensure_ffmpeg():
    # If ffmpeg is already on PATH, nothing to do
    if shutil.which("ffmpeg"):
        return

    # Try to use imageio-ffmpeg’s bundled binary
    if imageio_ffmpeg is not None:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            # Ensure a "ffmpeg.exe" exists on PATH (Windows needs the exact name)
            tmp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg-bin")
            os.makedirs(tmp_dir, exist_ok=True)
            target = os.path.join(tmp_dir, "ffmpeg.exe")
            if not os.path.exists(target):
                try:
                    shutil.copyfile(ffmpeg_exe, target)
                except Exception as copy_err:
                    raise FileNotFoundError(f"Could not prepare ffmpeg: {copy_err}")
            os.environ["PATH"] = f"{tmp_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            if shutil.which("ffmpeg"):
                print(f"Using bundled ffmpeg at: {target}")
                return

    raise FileNotFoundError(
        "FFmpeg not found. Install it (winget install Gyan.FFmpeg or choco install ffmpeg) "
        "or add it to PATH, or pip install imageio-ffmpeg for bundling."
    )


def call_whisper(audio_bytes: bytes) -> str:
    """
    Save audio bytes to a temp file and transcribe locally with Whisper.
    """
    tmp_path = None
    try:
        print("🔊 Transcribing locally with Whisper...")
        ensure_ffmpeg()

        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = whisper.load_model("small")
        result = model.transcribe(tmp_path, language="id")
        return result.get("text", "")
    except Exception as e:
        print(f"❌ Error while transcribing: {e}")
        return ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_error:
                print(f"⚠️ Could not delete temp file: {cleanup_error}")
