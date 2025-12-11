# datas/translate_video_to_text.py - FIXED VERSION
import tempfile
import cv2
import numpy as np
from datetime import datetime
import os
import requests
import json

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
        print(f"\n{'='*60}")
        print(f"🎬 STARTING ASL TRANSLATION FOR ROOM {room_id}")
        print(f"{'='*60}")
        print(f"Video URL: {video_url}")
        print(f"Frame rate: {frame_rate}, Resolution: {resolution}")
        
        # Get video duration
        print("⏱️ Calculating video duration...")
        duration = get_video_duration(video_url)
        print(f"✅ Duration: {duration:.2f} seconds")
        
        # Use ASL recognition service - get predictions from SIBI model
        predictions = get_asl_translation(video_url)
        
        # Process the predictions
        timestamps = []
        translated_script = "NO_SIGNS_DETECTED"
        
        if predictions and len(predictions) > 0:
            print(f"✅ Using REAL SIBI model predictions: {len(predictions)} timestamps")
            
            for pred in predictions:
                if isinstance(pred, dict) and 'second' in pred and 'text' in pred:
                    # Use the timestamp and text directly from SIBI API
                    timestamps.append({
                        "second": float(pred['second']),
                        "text": str(pred['text'])
                    })
            
            # Sort by time
            timestamps.sort(key=lambda x: x['second'])
            
            # Create full transcript
            if timestamps:
                words = [ts['text'] for ts in timestamps]
                translated_script = " ".join(words)
                print(f"📝 Full transcript: {translated_script}")
                
        else:
            print("⚠️ No predictions from SIBI model - returning empty")
            timestamps = []
            translated_script = "NO_SIGNS_DETECTED"

        # Insert into database
        cur.execute("""
            INSERT INTO translate_video
            (room_id, video_url, frame_rate, resolution, duration, translated_script, timestamps_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            room_id,
            video_url,
            frame_rate,
            resolution,
            duration,
            translated_script,
            json.dumps(timestamps, ensure_ascii=False), 
            datetime.now()
        ))

        # Update translate_yn to 'Y' for all video notes in this room with this video_url
        cur.execute("""
            UPDATE video_notes
               SET translate_yn = 'Y'
             WHERE message_id IN (
                SELECT m.message_id 
                FROM messages m
                JOIN media_messages mm ON m.message_id = mm.message_id
                WHERE m.room_id = %s AND m.message_type = 'video' AND mm.media_url = %s
            );
        """, (room_id, video_url))

        conn.commit()

        print(f"\n✅ ASL Translation COMPLETED")
        print(f"   Total timestamps: {len(timestamps)}")
        if timestamps:
            print(f"   First 5 predictions:")
            for ts in timestamps[:5]:
                print(f"     {ts['second']:.1f}s: {ts['text']}")
        print(f"{'='*60}\n")
        
        return timestamps

    except Exception as e:
        print(f"❌ Error in getTranslationFromVideo: {e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        cur.close()
        conn.close()
        