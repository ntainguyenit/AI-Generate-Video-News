import os
import shutil
import requests
from dotenv import load_dotenv
from PIL import Image

from scraper import scrape_article
from llm_processor import generate_video_script
from audio_generator import generate_audio
from image_generator import download_image
from video_builder import build_video
from telegram_notifier import send_to_telegram
from moviepy.editor import concatenate_videoclips, VideoFileClip

def run_pipeline():
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"):
        print("[-] Vui lòng cung cấp GEMINI_API_KEY trong file .env")
        return
        
    cache_file = "session_cache.json"
    use_cache = False
    if os.path.exists(cache_file):
        ans = input("🔄 Tìm thấy tiến trình bị gián đoạn trước đó. Khôi phục lại toàn bộ cấu hình? (y/n) [Enter = y]: ").strip().lower()
        if ans in ['', 'y', 'yes']:
            use_cache = True
            
    if use_cache:
        import json
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        article_url = cache.get("article_url", "")
        voice = cache.get("voice", "vi-VN-HoaiMyNeural")
        source_name = cache.get("source_name", "")
        publish_date = cache.get("publish_date", "")
        custom_media_urls = cache.get("custom_media_urls", [])
        selected_bgm = cache.get("selected_bgm", None)
        print(f"[+] Đã khôi phục phiên làm việc: {article_url[:50]}...")
    else:
        article_url = input("Nhập link bài báo tin tức: ")
        if not article_url:
            print("[-] URL không hợp lệ.")
            return
            
        from datetime import datetime, timezone, timedelta
    
        print("\nChọn giọng đọc AI:")
        print("1. Nữ (vi-VN-HoaiMyNeural) - Giọng truyền cảm, chuyên nghiệp (Mặc định)")
        print("2. Nam (vi-VN-NamMinhNeural) - Giọng trầm ấm, đọc thời sự")
        print("3. Nữ (vi-VN-BichNgocNeural) - Giọng trẻ trung, năng động, tươi sáng")
        voice_choice = input("Nhập lựa chọn (1/2/3) [Enter để chọn 1]: ").strip()
        
        if voice_choice == '2':
            voice = "vi-VN-NamMinhNeural"
        elif voice_choice == '3':
            voice = "vi-VN-BichNgocNeural"
        else:
            voice = "vi-VN-HoaiMyNeural"
        
        source_name = input("\nNhập tên Nguồn bài viết (VD: VnExpress, Dân Trí, ...): ").strip()
        publish_date = input("Nhập Ngày đăng (VD: 20/10/2023) [Nhấn Enter để dùng ngày hôm nay]: ").strip()
        if not publish_date:
            tz_vn = timezone(timedelta(hours=7))
            publish_date = datetime.now(tz_vn).strftime("%d/%m/%Y")
            print(f"  -> Tự động thiết lập ngày: {publish_date}")
        
        print("\n[Tùy chọn] Nhập link hình ảnh/video bổ sung để video sinh động hơn (Nhấn Enter để bỏ qua):")
        custom_media_urls = []
        while True:
            url = input("Link ảnh/video (hoặc Enter để kết thúc): ").strip()
            if not url:
                break
            custom_media_urls.append(url)
            
        print("\n[Tùy chọn] Chọn Nhạc Nền (Background Music):")
        bgm_dir = "bgm"
        if not os.path.exists(bgm_dir) and os.path.exists("bmg"):
            bgm_dir = "bmg"
            
        selected_bgm = None
        if os.path.exists(bgm_dir):
            bgm_files = [f for f in os.listdir(bgm_dir) if f.lower().endswith(".mp3")]
            if bgm_files:
                print("0. Không dùng nhạc nền (Bỏ qua)")
                for idx, f in enumerate(bgm_files, 1):
                    print(f"{idx}. {f}")
                bgm_choice = input(f"Chọn bài nhạc (0-{len(bgm_files)}) [Enter để chọn 0]: ").strip()
                if bgm_choice.isdigit() and 1 <= int(bgm_choice) <= len(bgm_files):
                    selected_bgm = os.path.join(bgm_dir, bgm_files[int(bgm_choice)-1])
                    print(f"[+] Đã chọn nhạc nền: {bgm_files[int(bgm_choice)-1]}")
                else:
                    print("  -> Đã bỏ qua nhạc nền.")
            else:
                print("  -> Không tìm thấy file .mp3 nào trong thư mục nhạc nền.")
                
        # Save cache
        import json
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "article_url": article_url,
                "voice": voice,
                "source_name": source_name,
                "publish_date": publish_date,
                "custom_media_urls": custom_media_urls,
                "selected_bgm": selected_bgm
            }, f, ensure_ascii=False, indent=4)
        
    # Tạo thư mục tạm
    tmp_dir = "tmp_assets"
    if os.path.exists(tmp_dir):
        import shutil
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass
    os.makedirs(tmp_dir, exist_ok=True)
    
    # 1. Scrape
    article_data = scrape_article(article_url)
    if not article_data:
        return
        
    # 2. Tóm tắt & tạo kịch bản
    script_data_tuple = generate_video_script(article_data['text'])
    if not script_data_tuple[2]:
        print("[-] Không thể tạo kịch bản.")
        return
    
    category, key_points, scenes, reels_caption = script_data_tuple
        
    # Tải ảnh chính của bài báo
    main_image_path = os.path.join(tmp_dir, "main_image.jpg")
    if article_data['top_image']:
        download_image(article_data['top_image'], main_image_path)
    
    print("\n[+] Đang chuẩn bị hình ảnh/video...")
    media_paths = []
        
    for idx, url in enumerate(custom_media_urls):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = requests.get(url, headers=headers, stream=True, timeout=15)
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '').lower()
                is_video = 'video' in content_type
                is_image = 'image' in content_type
                
                ext = url.split('.')[-1].split('?')[0].lower()
                # Loại bỏ các ký tự không hợp lệ như dấu slash để tránh tạo thư mục ảo
                ext = "".join([c for c in ext if c.isalnum()])
                if len(ext) > 5 or not ext:
                    ext = ""
                    
                if not is_video and not is_image:
                    is_video = ext in ['mp4', 'webm', 'mov', 'avi']
                    is_image = ext in ['jpg', 'jpeg', 'png', 'webp']
                
                if not is_video and not is_image:
                    # Nếu không rõ, coi như ảnh để cho PIL bắt lỗi
                    ext = 'jpg'
                elif is_video and ext not in ['mp4', 'webm', 'mov', 'avi']:
                    ext = 'mp4'
                elif is_image and ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
                    
                p = os.path.join(tmp_dir, f"custom_media_{idx}.{ext}")
                with open(p, "wb") as f:
                    for chunk in resp.iter_content(4096):
                        f.write(chunk)
                
                if is_video:
                    try:
                        with VideoFileClip(p) as v:
                            dur = v.duration
                        media_paths.append(p) # Ưu tiên đưa vào trước
                        print(f"  -> Tải thành công video bổ sung: {url[:30]}...")
                    except Exception:
                        os.remove(p)
                        print(f"  [-] Link không chứa video hợp lệ: {url[:30]}...")
                else:
                    try:
                        with Image.open(p) as img_check:
                            img_check.verify()
                        media_paths.append(p) # Ưu tiên đưa vào trước
                        print(f"  -> Tải thành công ảnh bổ sung: {url[:30]}...")
                    except Exception:
                        os.remove(p)
                        print(f"  [-] Link không chứa hình ảnh hợp lệ (có thể là HTML): {url[:30]}...")
        except Exception as e:
            print(f"  [-] Lỗi tải link {url[:30]}: {e}")

    # Đưa ảnh chính của bài báo vào cuối danh sách (làm nền phụ)
    if os.path.exists(main_image_path):
        media_paths.append(main_image_path)
            
    if not media_paths:
        dummy_img = os.path.join(tmp_dir, "dummy_black.jpg")
        Image.new('RGB', (1080, 1920), color = 'black').save(dummy_img)
        media_paths.append(dummy_img)
        print("  [!] Không có media nào, dùng ảnh nền đen thay thế.")
    
    # 3. Xử lý từng scene
    scene_clips = []
    
    for i, scene in enumerate(scenes):
        print(f"\n--- Đang xử lý Scene {i+1}/{len(scenes)} ---")
        text = scene['text']
        
        # Audio
        audio_file = os.path.join(tmp_dir, f"audio_{i}.mp3")
        boundaries = generate_audio(text, audio_file, voice=voice)
        
        if boundaries is None:
            print(f"[-] Bỏ qua Scene {i} do lỗi tạo audio.")
            continue
        if len(boundaries) == 0:
            print(f"[!] Cảnh báo: Không có dữ liệu phụ đề (word boundaries) cho Scene {i}.")
        
        # Gán media xoay vòng cho từng phân cảnh để thay đổi liên tục
        current_media_path = media_paths[i % len(media_paths)]
                
        # Build scene video
        video_file = os.path.join(tmp_dir, f"scene_{i}.mp4")
        
        # Để các Key Points xuất hiện tuần tự ở mỗi scene, ta truyền key_points vào
        is_last = (i == len(scenes) - 1)
        build_video(
            audio_file, current_media_path, boundaries, video_file, 
            article_title=article_data['title'], category=category, 
            key_points=key_points, scene_index=i,
            source_name=source_name, publish_date=publish_date, is_last_scene=is_last
        )
        scene_clips.append(video_file)
        
    # 4. Nối các đoạn video lại
    print("[*] Đang ghép các đoạn video...")
    
    if not scene_clips:
        print("[-] Lỗi: Không có video phân cảnh nào được tạo thành công. Không thể ghép video.")
        print("\n[*] Đang ghép các đoạn video...")
    clips = [VideoFileClip(c) for c in scene_clips]
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # 4. Xử lý Background Music
    if selected_bgm and os.path.exists(selected_bgm):
        print(f"[*] Đang lồng nhạc nền: {os.path.basename(selected_bgm)}")
        try:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            from moviepy.audio.fx.all import audio_loop, volumex
            
            bgm_clip = AudioFileClip(selected_bgm)
            # Loop bgm to match final clip duration
            bgm_clip = audio_loop(bgm_clip, duration=final_clip.duration)
            # Giảm âm lượng nhạc nền xuống 30% (0.3) để nghe rõ hơn
            bgm_clip = volumex(bgm_clip, 0.3)
            
            # Mix audio: giọng đọc (của video final) + nhạc nền
            final_audio = CompositeAudioClip([final_clip.audio, bgm_clip])
            final_clip = final_clip.set_audio(final_audio)
        except Exception as e:
            print(f"[-] Lỗi khi xử lý nhạc nền: {e}")
    
    final_output = "output_video.mp4"
    final_clip.write_videofile(
        final_output,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    
    # Đóng clips để giải phóng file handles
    for c in clips:
        c.close()
    final_clip.close()
    
    print(f"\n[+] HOÀN THÀNH! Video đã được lưu tại: {final_output}")
    
    # 5. In gợi ý Caption (Reels/TikTok)
    if reels_caption:
        print("\n" + "="*60)
        print("📝 GỢI Ý CAPTION ĐĂNG REELS / TIKTOK / SHORTS:")
        print("="*60)
        print(reels_caption)
        print("="*60 + "\n")
        
    # 6. Tự động gửi lên Telegram Bot
    send_to_telegram(final_output, reels_caption)
    
    # Xóa cache nếu chạy thành công toàn bộ
    if os.path.exists("session_cache.json"):
        try:
            os.remove("session_cache.json")
        except:
            pass

def main():
    try:
        run_pipeline()
    except Exception as e:
        import traceback
        print("\n" + "🔥"*20)
        print("LỖI HỆ THỐNG NGHIÊM TRỌNG (CRASH):")
        print(f"Nguyên nhân: {str(e)}")
        print("Chi tiết Stack Trace (Dành cho Coder debug):")
        traceback.print_exc()
        print("🔥"*20 + "\n")
    finally:
        # Dọn dẹp bộ nhớ luông được thực thi dù lỗi hay không
        tmp_dir = "tmp_assets"
        if os.path.exists(tmp_dir):
            print("\n[*] Đang dọn dẹp các file rác tạm thời (Dọn dẹp dung lượng máy tính)...")
            try:
                shutil.rmtree(tmp_dir)
                print("[+] Dọn dẹp hoàn tất. Các file rác đã bị xóa vĩnh viễn!")
            except Exception as cleanup_e:
                print(f"[-] Lỗi khi dọn dẹp thư mục tạm: {cleanup_e}")

if __name__ == "__main__":
    main()
