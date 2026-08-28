import edge_tts
import asyncio
import os
import ssl

# Bypass SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

async def _generate_audio_async(text, output_file, voice="vi-VN-HoaiMyNeural"):
    """
    Async function to call edge-tts.
    """
    communicate = edge_tts.Communicate(text, voice)
    word_boundaries = []
    
    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # edge-tts returns offset and duration in 100-nanoseconds
                # Convert to seconds
                offset_sec = chunk["offset"] / 10000000.0
                duration_sec = chunk["duration"] / 10000000.0
                word_boundaries.append({
                    "word": chunk["text"],
                    "start": offset_sec,
                    "end": offset_sec + duration_sec
                })
                
    # Fallback for voices without WordBoundary support
    if len(word_boundaries) == 0 and os.path.exists(output_file):
        try:
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(output_file)
            dur = clip.duration
            clip.close()
            words = text.split()
            if words and dur > 0:
                time_per_word = dur / len(words)
                for i, w in enumerate(words):
                    word_boundaries.append({
                        "word": w,
                        "start": i * time_per_word,
                        "end": (i + 1) * time_per_word
                    })
        except Exception as e:
            print(f"Error creating fallback word boundaries: {e}")
                
    return word_boundaries

def generate_audio(text, output_file, voice="vi-VN-HoaiMyNeural"):
    """
    Generate audio file and word timestamps.
    Returns a list of word boundaries: [{"word": "...", "start": 0.0, "end": 0.5}, ...]
    """
    import time
    print(f"Generating audio for text: '{text[:30]}...'")
    
    for attempt in range(1, 4):
        try:
            boundaries = asyncio.run(_generate_audio_async(text, output_file, voice))
            # Check if file has data
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"Audio generated successfully: {output_file}")
                return boundaries
            else:
                print(f"Invalid audio received (Attempt {attempt}/3)...")
                time.sleep(1)
        except Exception as e:
            print(f"Error generating audio (Attempt {attempt}/3): {e}")
            time.sleep(1)
            
    print("Failed to generate audio after 3 attempts.")
    return None

if __name__ == "__main__":
    test_text = "Xin chào, đây là công cụ tạo video tin tức tự động."
    out_file = "test_audio.mp3"
    bounds = generate_audio(test_text, out_file)
    if bounds:
        print(f"Total words: {len(bounds)}")
        print(bounds[:3])
