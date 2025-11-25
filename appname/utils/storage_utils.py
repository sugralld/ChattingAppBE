import requests


def download_from_supabase(public_url: str):
    res = requests.get(public_url)
    if res.status_code != 200:
        raise Exception("Failed to download file from Supabase Storage")
    return res.content
