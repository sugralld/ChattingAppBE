# datas/translate_video_to_text.py - FIXED VERSION
import tempfile
import cv2
import numpy as np
from datetime import datetime
import os
import requests

from appname.datas.model_ai import get_asl_translation, fallback_timestamps
from appname.config import *


def download_video(video_url):
    """Download video from URL"""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.close()
    try:
        response = requests.get(video_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(tmp.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return tmp.name
    except Exception as e:
        raise Exception(f"Failed to download video: {str(e)}")


def get_video_duration(video_url):
    """Get video duration without processing all frames"""
    video_path = download_video(video_url)
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if frame_count > 0 and fps > 0 else 4.0
        cap.release()
        return duration
    finally:
        # Clean up temporary file
        try:
            os.unlink(video_path)
        except:
            pass


def getTranslationFromVideo(room_id, video_url, frame_rate, resolution):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print(f"Starting ASL translation for room {room_id}")
        
        # Get video duration efficiently
        total_duration = get_video_duration(video_url)
        print(f"📹 Video duration: {total_duration:.2f}s")

        # Use ASL recognition service - get REAL predictions
        predictions = get_asl_translation(video_url)
        
        # Process the predictions from WLASL API - RETURN WHATEVER WLASL GIVES
        timestamps = []
        translated_script = "NO_SIGNS_DETECTED"
        
        if predictions and len(predictions) > 0:
            # We have REAL predictions from the model
            print(f"✅ Using REAL model predictions: {len(predictions)} timestamps")
            
            for pred in predictions:
                if isinstance(pred, dict) and 'second' in pred and 'text' in pred:
                    # Use the timestamp and text directly from WLASL API
                    timestamps.append({
                        "second": pred['second'],
                        "text": pred['text']
                    })
            
            # Sort by time
            timestamps.sort(key=lambda x: x['second'])
            
            # Use the most frequent word for database storage
            if timestamps:
                word_counts = {}
                for ts in timestamps:
                    word = ts['text']
                    word_counts[word] = word_counts.get(word, 0) + 1
                most_common_word = max(word_counts.items(), key=lambda x: x[1])[0]
                translated_script = most_common_word
                
        else:
            # No real predictions - RETURN EMPTY LIST instead of fallback
            print("⚠️ No model predictions from WLASL API - returning empty list")
            # Don't use fallback timestamps - return empty to show real WLASL output
            timestamps = []
            translated_script = "NO_SIGNS_DETECTED"

        # Insert into database
        cur.execute("""
            INSERT INTO translate_video
            (room_id, video_url, frame_rate, resolution, translated_script, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            room_id,
            video_url,
            frame_rate,
            resolution,
            translated_script,
            datetime.now()
        ))

        conn.commit()

        print(f"✅ ASL Translation completed: {len(timestamps)} timestamps")
        if timestamps:
            print(f"📝 Final output: {[ts['text'] for ts in timestamps[:5]]}...")
        else:
            print("📝 Final output: [] (no signs detected)")
        return timestamps  # This will be empty if WLASL returned empty

    except Exception as e:
        print(f"❌ Error in getTranslationFromVideo: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list on error to be consistent
        return []

    finally:
        cur.close()
        conn.close()