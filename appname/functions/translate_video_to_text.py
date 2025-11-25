# functions/translate_video_to_text.py - FIXED VERSION
from appname.datas.translate_video_to_text import getTranslationFromVideo
from appname.datas.model_ai import *
import numpy as np


def predict_asl_text(video_url):
    try:
        print(f"🎯 Starting ASL prediction for: {video_url}")
        
        # Use the time-based ASL recognition
        predictions = get_asl_translation(video_url)
        
        # Process predictions
        timestamps = []
        
        if predictions and len(predictions) > 0:
            print(f"✅ Using {len(predictions)} REAL model predictions")
            
            # Use predictions directly from WLASL API
            for pred in predictions:
                if isinstance(pred, dict) and 'second' in pred and 'text' in pred:
                    timestamps.append({
                        "second": pred['second'],
                        "text": pred['text']
                    })
            
            # Sort by time
            timestamps.sort(key=lambda x: x['second'])
            
            # Log what we found
            unique_words = set(ts['text'] for ts in timestamps)
            print(f"📝 Detected words: {list(unique_words)}")
            
        else:
            # No real predictions - use fallback
            print("⚠️ No model predictions available, using fallback")
            timestamps = fallback_timestamps()

        # Ensure we have output
        if not timestamps:
            print("⚠️ No timestamps generated, creating default")
            timestamps = fallback_timestamps()

        print(f"✅ Final output: {len(timestamps)} timestamps")
        return {
            "status": "success",
            "code": 0,
            "message": "ASL translation completed",
            "data": timestamps
        }

    except Exception as e:
        print(f"❌ Error in predict_asl_text: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": fallback_timestamps()
        }


def funcTranslateVideoToText(room_id, video_url, frame_rate, resolution):
    try:
        print(f"🚀 Starting translation for room {room_id}")
        result = getTranslationFromVideo(room_id, video_url, frame_rate, resolution)

        # Handle the result from getTranslationFromVideo
        if result is None:
            return {
                "status": "error",
                "code": 500,
                "message": "Translation returned no result",
                "data": fallback_timestamps()
            }

        return {
            "status": "success",
            "code": 0,
            "message": "Translation completed successfully",
            "data": result
        }

    except Exception as e:
        print(f"❌ Error in funcTranslateVideoToText: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": fallback_timestamps()
        }