from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_voice_to_supabase(file_name, file_bytes):
    bucket = "voice-notes"

    res = supabase.storage.from_(bucket).upload(
        file_name, file_bytes, {"content-type": "audio/m4a"}
    )

    if res is None:
        raise Exception("Upload failed")

    public_url = supabase.storage.from_(bucket).get_public_url(file_name)
    return public_url
