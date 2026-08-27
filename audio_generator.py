import edge_tts
import asyncio
import os
import ssl

# Bỏ qua kiểm tra chứng chỉ SSL (Fix lỗi SSLCertVerificationError)
ssl._create_default_https_context = ssl._create_unverified_context

async def _generate_audio_async(text, output_file, voice="vi-VN-HoaiMyNeural"):
    """
    Hàm bất đồng bộ gọi edge-tts.
    """
    communicate = edge_tts.Communicate(text, voice)
    word_boundaries = []
    
    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # edge-tts trả về offset và duration tính bằng 100-nanoseconds
                # Đổi sang giây (seconds)
                offset_sec = chunk["offset"] / 10000000.0
                duration_sec = chunk["duration"] / 10000000.0
                word_boundaries.append({
                    "word": chunk["text"],
                    "start": offset_sec,
                    "end": offset_sec + duration_sec
                })
                
    # Fallback nếu giọng đọc không hỗ trợ WordBoundary (ví dụ một số giọng Nam)
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
            print(f"Lỗi tạo fallback word boundaries: {e}")
                
    return word_boundaries

def generate_audio(text, output_file, voice="vi-VN-HoaiMyNeural"):
    """
    Tạo file audio từ văn bản và lấy mốc thời gian của từng từ.
    Trả về danh sách word boundaries: [{"word": "...", "start": 0.0, "end": 0.5}, ...]
    """
    import time
    print(f"[*] Đang tạo audio cho text: '{text[:30]}...'")
    
    for attempt in range(1, 4):
        try:
            boundaries = asyncio.run(_generate_audio_async(text, output_file, voice))
            # Kiểm tra xem file có thực sự được ghi dữ liệu không
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"[+] Tạo audio thành công: {output_file}")
                return boundaries
            else:
                print(f"[-] Không nhận được audio hợp lệ (Thử lại {attempt}/3)...")
                time.sleep(1)
        except Exception as e:
            print(f"[-] Lỗi khi tạo audio (Thử lại {attempt}/3): {e}")
            time.sleep(1)
            
    print("[-] Thất bại tạo audio sau 3 lần thử.")
    return None

if __name__ == "__main__":
    test_text = "Xin chào, đây là công cụ tạo video tin tức tự động."
    out_file = "test_audio.mp3"
    bounds = generate_audio(test_text, out_file)
    if bounds:
        print(f"Total words: {len(bounds)}")
        print(bounds[:3])
