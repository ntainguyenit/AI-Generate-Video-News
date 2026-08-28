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
        print("Error: Please provide GEMINI_API_KEY in the .env file")
        return
        
    cache_file = "session_cache.json"
    use_cache = False
    if os.path.exists(cache_file):
        ans = input("Interrupted process found. Restore previous configuration? (y/n) [Enter = y]: ").strip().lower()
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
        print(f"Session restored: {article_url[:50]}...")
    else:
        article_url = input("Enter news article URL: ")
        if not article_url:
            print("Error: Invalid URL.")
            return
            
        from datetime import datetime, timezone, timedelta
    
        print("\nSelect AI voice:")
        print("1. Female (vi-VN-HoaiMyNeural) - Expressive, professional (Default)")
        print("2. Male (vi-VN-NamMinhNeural) - Deep, news anchor")
        print("3. Female (vi-VN-BichNgocNeural) - Youthful, energetic, bright")
        voice_choice = input("Enter choice (1/2/3) [Enter for 1]: ").strip()
        
        if voice_choice == '2':
            voice = "vi-VN-NamMinhNeural"
        elif voice_choice == '3':
            voice = "vi-VN-BichNgocNeural"
        else:
            voice = "vi-VN-HoaiMyNeural"
        
        source_name = input("\nEnter Article Source (e.g., VnExpress, Reuters, etc.): ").strip()
        publish_date = input("Enter Publish Date (e.g., 20/10/2023) [Enter for today]: ").strip()
        if not publish_date:
            tz_vn = timezone(timedelta(hours=7))
            publish_date = datetime.now(tz_vn).strftime("%d/%m/%Y")
            print(f"Automatically set date: {publish_date}")
        
        print("\n[Optional] Enter links to additional images/videos (Press Enter to skip):")
        custom_media_urls = []
        while True:
            url = input("Image/Video URL (or Enter to finish): ").strip()
            if not url:
                break
            custom_media_urls.append(url)
            
        print("\n[Optional] Select Background Music:")
        bgm_dir = "bgm"
        if not os.path.exists(bgm_dir) and os.path.exists("bmg"):
            bgm_dir = "bmg"
            
        selected_bgm = None
        if os.path.exists(bgm_dir):
            bgm_files = [f for f in os.listdir(bgm_dir) if f.lower().endswith(".mp3")]
            if bgm_files:
                print("0. No background music (Skip)")
                for idx, f in enumerate(bgm_files, 1):
                    print(f"{idx}. {f}")
                bgm_choice = input(f"Select track (0-{len(bgm_files)}) [Enter for 0]: ").strip()
                if bgm_choice.isdigit() and 1 <= int(bgm_choice) <= len(bgm_files):
                    selected_bgm = os.path.join(bgm_dir, bgm_files[int(bgm_choice)-1])
                    print(f"Selected background music: {bgm_files[int(bgm_choice)-1]}")
                else:
                    print("Background music skipped.")
            else:
                print("No .mp3 files found in the background music directory.")
                
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
        
    # Create temporary directory
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
        
    # 2. Summarize & generate script
    script_data_tuple = generate_video_script(article_data['text'])
    if not script_data_tuple[2]:
        print("Error: Could not generate script.")
        return
    
    category, key_points, scenes, reels_caption = script_data_tuple
        
    # Download main article image
    main_image_path = os.path.join(tmp_dir, "main_image.jpg")
    if article_data['top_image']:
        download_image(article_data['top_image'], main_image_path)
    
    print("\nPreparing media assets...")
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
                # Remove invalid characters to avoid virtual paths
                ext = "".join([c for c in ext if c.isalnum()])
                if len(ext) > 5 or not ext:
                    ext = ""
                    
                if not is_video and not is_image:
                    is_video = ext in ['mp4', 'webm', 'mov', 'avi']
                    is_image = ext in ['jpg', 'jpeg', 'png', 'webp']
                
                if not is_video and not is_image:
                    # If unknown, treat as image to let PIL catch errors
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
                        media_paths.append(p) # Prioritize
                        print(f"Additional video downloaded successfully: {url[:30]}...")
                    except Exception:
                        os.remove(p)
                        print(f"Link does not contain valid video: {url[:30]}...")
                else:
                    try:
                        with Image.open(p) as img_check:
                            img_check.verify()
                        media_paths.append(p) # Prioritize
                        print(f"Additional image downloaded successfully: {url[:30]}...")
                    except Exception:
                        os.remove(p)
                        print(f"Link does not contain valid image (might be HTML): {url[:30]}...")
        except Exception as e:
            print(f"Error downloading link {url[:30]}: {e}")

    # Append main article image at the end as fallback
    if os.path.exists(main_image_path):
        media_paths.append(main_image_path)
            
    if not media_paths:
        dummy_img = os.path.join(tmp_dir, "dummy_black.jpg")
        Image.new('RGB', (1080, 1920), color = 'black').save(dummy_img)
        media_paths.append(dummy_img)
        print("No media found, using black fallback image.")
    
    # 3. Process each scene
    scene_clips = []
    
    for i, scene in enumerate(scenes):
        print(f"\nProcessing Scene {i+1}/{len(scenes)}...")
        text = scene['text']
        
        # Audio
        audio_file = os.path.join(tmp_dir, f"audio_{i}.mp3")
        boundaries = generate_audio(text, audio_file, voice=voice)
        
        if boundaries is None:
            print(f"Skipping Scene {i} due to audio generation error.")
            continue
        if len(boundaries) == 0:
            print(f"Warning: No word boundary data for Scene {i}.")
        
        # Cycle through media for each scene
        current_media_path = media_paths[i % len(media_paths)]
                
        # Build scene video
        video_file = os.path.join(tmp_dir, f"scene_{i}.mp4")
        
        # Pass key_points sequentially for each scene
        is_last = (i == len(scenes) - 1)
        build_video(
            audio_file, current_media_path, boundaries, video_file, 
            article_title=article_data['title'], category=category, 
            key_points=key_points, scene_index=i,
            source_name=source_name, publish_date=publish_date, is_last_scene=is_last
        )
        scene_clips.append(video_file)
        
    # 4. Concatenate video clips
    print("Concatenating video clips...")
    
    if not scene_clips:
        print("Error: No scene videos were generated successfully. Cannot concatenate.")
        return
        
    clips = [VideoFileClip(c) for c in scene_clips]
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # 5. Process Background Music
    if selected_bgm and os.path.exists(selected_bgm):
        print(f"Mixing background music: {os.path.basename(selected_bgm)}")
        try:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            from moviepy.audio.fx.all import audio_loop, volumex
            
            bgm_clip = AudioFileClip(selected_bgm)
            # Loop bgm to match final clip duration
            bgm_clip = audio_loop(bgm_clip, duration=final_clip.duration)
            # Reduce background music volume to 30% (0.3)
            bgm_clip = volumex(bgm_clip, 0.3)
            
            # Mix audio: voiceover + background music
            final_audio = CompositeAudioClip([final_clip.audio, bgm_clip])
            final_clip = final_clip.set_audio(final_audio)
        except Exception as e:
            print(f"Error processing background music: {e}")
    
    final_output = "output_video.mp4"
    final_clip.write_videofile(
        final_output,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    
    # Close clips to release file handles
    for c in clips:
        c.close()
    final_clip.close()
    
    print(f"\nSUCCESS! Video saved at: {final_output}")
    
    # 6. Print Caption Suggestion (Reels/TikTok)
    if reels_caption:
        print("\n" + "="*60)
        print("SUGGESTED CAPTION FOR REELS / TIKTOK / SHORTS:")
        print("="*60)
        print(reels_caption)
        print("="*60 + "\n")
        
    # 7. Send to Telegram Bot
    send_to_telegram(final_output, reels_caption)
    
    # Clear cache on successful run
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
        print("\n" + "="*40)
        print("CRITICAL SYSTEM ERROR (CRASH):")
        print(f"Cause: {str(e)}")
        print("Stack Trace (For Debugging):")
        traceback.print_exc()
        print("="*40 + "\n")
    finally:
        # Cleanup temporary files
        tmp_dir = "tmp_assets"
        if os.path.exists(tmp_dir):
            print("\nCleaning up temporary files...")
            try:
                shutil.rmtree(tmp_dir)
                print("Cleanup completed successfully.")
            except Exception as cleanup_e:
                print(f"Error cleaning up temporary directory: {cleanup_e}")

if __name__ == "__main__":
    main()
