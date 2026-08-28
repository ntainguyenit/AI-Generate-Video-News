import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Patch for MoviePy compatibility with Pillow >= 10.0.0
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, AudioClip, CompositeAudioClip

def resize_and_crop(img, target_size=(1080, 1920)):
    """
    Crop and resize the image to fit the target frame, 
    filling excess space with a blurred background.
    """
    target_w, target_h = target_size
    img_w, img_h = img.size
    
    # Create blurred background
    bg = img.copy()
    # Calculate scale factor to cover the entire frame
    scale = max(target_w / img_w, target_h / img_h)
    new_bg_w = int(img_w * scale)
    new_bg_h = int(img_h * scale)
    bg = bg.resize((new_bg_w, new_bg_h), Image.LANCZOS)
    
    # Center-crop the background
    left = (new_bg_w - target_w) / 2
    top = (new_bg_h - target_h) / 2
    bg = bg.crop((left, top, left + target_w, top + target_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
    bg = bg.point(lambda p: p * 0.5) # Darken background slightly
    
    # Calculate main image dimensions (fit inside frame)
    scale = min(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    main_img = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Paste main image onto center of background
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    bg.paste(main_img, (paste_x, paste_y))
    
    return bg

def make_ken_burns_clip(image_path, duration, target_size=(1080, 1920)):
    """
    Create a video clip with random zoom/pan (Ken Burns) effects from an image.
    """
    img = Image.open(image_path).convert("RGB")
    base_img = resize_and_crop(img, target_size)
    
    # Randomly select one of four motion effects
    effect = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
    
    def make_frame(t):
        w, h = base_img.size
        progress = t / duration
        
        if effect == "zoom_in":
            zoom_factor = 1.0 + 0.1 * progress
            x_offset, y_offset = 0, 0
        elif effect == "zoom_out":
            zoom_factor = 1.1 - 0.1 * progress
            x_offset, y_offset = 0, 0
        elif effect == "pan_left":
            zoom_factor = 1.1
            max_pan = w * 0.1
            x_offset = -(max_pan / 2) + max_pan * progress
            y_offset = 0
        elif effect == "pan_right":
            zoom_factor = 1.1
            max_pan = w * 0.1
            x_offset = (max_pan / 2) - max_pan * progress
            y_offset = 0
        
        new_w = int(w * zoom_factor)
        new_h = int(h * zoom_factor)
        zoomed = base_img.resize((new_w, new_h), Image.LANCZOS)
        
        # Crop central region with offset applied
        left = (new_w - w) / 2 + x_offset
        top = (new_h - h) / 2 + y_offset
        
        # Clamp crop boundaries to remain within image limits
        left = max(0, min(new_w - w, left))
        top = max(0, min(new_h - h, top))
        
        cropped = zoomed.crop((left, top, left + w, top + h))
        return np.array(cropped)
        
    return make_frame

def make_video_background_clip(video_path, duration, target_size=(1080, 1920)):
    from moviepy.editor import VideoFileClip
    vid_clip = VideoFileClip(video_path)
    
    # Loop video if duration is shorter than required
    if vid_clip.duration < duration:
        from moviepy.video.fx.all import loop
        vid_clip = loop(vid_clip, duration=duration)
    else:
        vid_clip = vid_clip.subclip(0, duration)
        
    w, h = vid_clip.size
    target_w, target_h = target_size
    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Resize
    vid_clip = vid_clip.resize(height=new_h, width=new_w)
    
    # Center crop
    x_center = new_w / 2
    y_center = new_h / 2
    vid_clip = vid_clip.crop(x_center=x_center, y_center=y_center, width=target_w, height=target_h)
    
    def make_frame(t):
        return vid_clip.get_frame(t)
        
    return make_frame, vid_clip

def split_into_chunks(words, chunk_size=6):
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        chunks.append({
            "words": chunk,
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"]
        })
    return chunks

def make_ping_sound(duration=0.3, freq=1200, volume=0.8):
    """
    Generate a ping sound effect (decaying sine wave) using NumPy.
    """
    def make_frame(t):
        # Time variable t can be a NumPy array or float
        # Apply exponential decay for audio smoothing
        decay = np.exp(-8 * t)
        wave = volume * np.sin(2 * np.pi * freq * t) * decay
        
        # Ensure a 2D array output for stereo audio
        if isinstance(t, np.ndarray):
            return np.column_stack((wave, wave))
        else:
            return np.array([wave, wave])
            
    return AudioClip(make_frame, duration=duration, fps=44100)

def ease_out_cubic(t, start, end, duration):
    """Cubic ease-out function for smooth deceleration."""
    if t <= 0: return start
    if t >= duration: return end
    t /= duration
    t -= 1
    return (end - start) * (t * t * t + 1) + start

def draw_overlays_and_subtitles(frame, t, duration, chunks, font_path, article_title="Tin Tức", category="Tin Công Nghệ", key_points=[], scene_index=0, source_name="", publish_date="", is_last_scene=False, font_size=70):
    """
    Render UI cards with slide-in animations and stylized subtitles.
    """
    img = Image.fromarray(frame)
    
    # Force 9:16 vertical aspect ratio (1080x1920) to prevent video distortion
    if img.size != (1080, 1920):
        img = img.resize((1080, 1920), Image.LANCZOS)
        
    # Use draw_main to render directly onto img (supports RGBA)
    draw_main = ImageDraw.Draw(img, "RGBA")
    
    try:
        font_sub = ImageFont.truetype(font_path, font_size)
        font_title = ImageFont.truetype(font_path, 55) # Increase title font size
        font_tag = ImageFont.truetype(font_path, 35)
        font_bullet = ImageFont.truetype(font_path, 45)
    except:
        font_sub = font_title = font_tag = font_bullet = ImageFont.load_default()

    dark_blue = (0, 51, 102, 255)
    
    # 1. Header (Category Tag) - Slide in only on the first scene
    category_full = "Breaking News Công Nghệ"
    part1 = "Breaking News"
    part2 = " Công Nghệ"
    
    tag_padding_x, tag_padding_y = 30, 15
    tag_w = font_tag.getbbox(category_full)[2] + tag_padding_x * 2
    tag_h = 35 + tag_padding_y * 2
    target_tag_x = 60
    tag_y = 150 # Lower position slightly
    
    # Calculate current X position
    if scene_index == 0:
        tag_x = ease_out_cubic(t, start=-tag_w - 50, end=target_tag_x, duration=0.8)
    else:
        tag_x = target_tag_x # Fixed position
    
    draw_main.rounded_rectangle([tag_x, tag_y, tag_x + tag_w, tag_y + tag_h], radius=20, fill=dark_blue)
    
    # Render two-tone text
    draw_main.text((tag_x + tag_padding_x, tag_y + tag_padding_y - 5), part1, font=font_tag, fill=(220, 20, 60, 255)) # Dark red (Crimson)
    w_part1 = font_tag.getbbox(part1)[2]
    draw_main.text((tag_x + tag_padding_x + w_part1, tag_y + tag_padding_y - 5), part2, font=font_tag, fill=(255, 255, 255, 255)) # White
    
    # 1.5 Date Badge (Next to Category Tag)
    if publish_date:
        date_w = font_tag.getbbox(publish_date)[2] + 40
        date_h = tag_h
        target_date_x = target_tag_x + tag_w + 15
        
        if scene_index == 0:
            date_x = ease_out_cubic(t, start=-date_w - 50, end=target_date_x, duration=0.8)
        else:
            date_x = target_date_x
            
        draw_main.rounded_rectangle([date_x, tag_y, date_x + date_w, tag_y + date_h], radius=20, fill=(0, 0, 0, 160))
        draw_main.text((date_x + 20, tag_y + tag_padding_y - 5), publish_date, font=font_tag, fill=(200, 200, 200, 255))
    
    # 2. Footer (Lower Third) - Slide up only on the first scene
    banner_height = 450 # Increase banner height
    target_banner_y = img.height - banner_height
    
    if scene_index == 0:
        banner_y = ease_out_cubic(t, start=img.height, end=target_banner_y, duration=0.8)
    else:
        banner_y = target_banner_y
        
    draw_main.rectangle([0, banner_y, img.width, img.height], fill=dark_blue)
    
    margin = 50
    article_title_upper = article_title.upper()
    max_title_width = img.width - 2 * margin
    title_words = article_title_upper.split()
    t_lines = []
    t_curr_line = ""
    for w in title_words:
        test_line = t_curr_line + w + " "
        if font_title.getbbox(test_line)[2] <= max_title_width:
            t_curr_line = test_line
        else:
            t_lines.append(t_curr_line)
            t_curr_line = w + " "
    t_lines.append(t_curr_line)
    
    ty = banner_y + 50
    for line in t_lines:
        draw_main.text((margin, ty), line.strip(), font=font_title, fill=(255, 255, 255, 255))
        ty += 75 # Increase line spacing for larger font
        
    # 2.5 Source Tag (Article source - Bottom-left corner)
    if source_name:
        src_text = f"Nguồn: {source_name}"
        src_w = font_tag.getbbox(src_text)[2] + 40
        src_h = 70 # Increase top/bottom padding
        target_src_x = 30
        target_src_y = img.height - src_h - 50 # Adjust position slightly upward
        
        if scene_index == 0:
            src_y = ease_out_cubic(t, start=img.height + 50, end=target_src_y, duration=0.8)
        else:
            src_y = target_src_y
            
        draw_main.rounded_rectangle([target_src_x, src_y, target_src_x + src_w, src_y + src_h], radius=15, fill=(0, 0, 0, 150))
        draw_main.text((target_src_x + 20, src_y + 15), src_text, font=font_tag, fill=(255, 255, 255, 200))
    
    # 2. Render Bullet Points (Key points)
    if key_points and scene_index < len(key_points):
        bullet_text = key_points[scene_index]
        
        # Apply word wrapping for bullet text
        # Increase max width to provide padding on dark box (prevent text clipping)
        b_max_w = img.width - 250
        b_words = bullet_text.split()
        b_lines = []
        b_curr = ""
        for w in b_words:
            if font_bullet.getbbox(b_curr + w + " ")[2] <= b_max_w:
                b_curr += w + " "
            else:
                b_lines.append(b_curr)
                b_curr = w + " "
        b_lines.append(b_curr)
        
        card_h = len(b_lines) * 60 + 60
        card_w = img.width - 120
        target_card_x = 60
        target_card_y = 150 # Position below header
        
        # Fast Fade-In + Short Slide-Up animation (Smooth Easing / Ease Out)
        anim_start_t = 0.3
        anim_duration = 0.3
        
        # Calculate progress 0.0 to 1.0
        p = (t - anim_start_t) / anim_duration
        if p < 0:
            p = 0
        elif p > 1:
            p = 1
            
        # Cubic ease-out formula for rapid entrance with smooth deceleration
        p_eased = 1 - (1 - p) ** 3
        
        # Calculate properties based on progress
        opacity_factor = p_eased
        # Short slide up from 60px below target position
        card_y_anim = target_card_y + 60 * (1 - p_eased)
        card_x = target_card_x
        
        if opacity_factor > 0:
            bg_alpha = int(180 * opacity_factor)
            text_alpha = int(255 * opacity_factor)
            
            # Render translucent card background (Glassmorphism effect)
            draw_main.rounded_rectangle([card_x, card_y_anim, card_x + card_w, card_y_anim + card_h], radius=25, fill=(0, 0, 0, bg_alpha))
            
            # Yellow vertical bar (Accent Bar)
            bar_x = card_x + 35
            bar_y = card_y_anim + 35
            bar_w = 8
            bar_h = len(b_lines) * 60 - 10
            draw_main.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=4, fill=(255, 215, 0, text_alpha))
            
            by = card_y_anim + 30
            for line in b_lines:
                # Increase spacing from yellow bar to text (card_x + 85)
                draw_main.text((card_x + 85, by), line.strip(), font=font_bullet, fill=(255, 255, 255, text_alpha))
                by += 60
                
    # Calculate Fade-to-Black transition at video end
    fade_factor = 0.0
    is_fading_out = False
    
    if is_last_scene:
        fade_duration = 1.0
        fade_start = duration - 2.5  
        
        if t >= fade_start:
            is_fading_out = True
            fade_progress = (t - fade_start) / fade_duration
            fade_factor = min(1.0, max(0.0, fade_progress))
            
            # Overlay a gradually darkening black layer over full screen
            overlay = Image.new('RGBA', img.size, (0, 0, 0, int(255 * fade_factor)))
            img.paste(overlay, (0,0), overlay)
            draw_main = ImageDraw.Draw(img) # Update draw object after paste
    
    # Render Call to Action (CTA) tag sliding up in final 2.5s
    if is_last_scene and t >= (duration - 2.5):
        # Calculate CTA animation parameters (slide up from bottom to center)
        time_since_start = t - (duration - 2.5)
        
        # CTA parameters
        c_font = ImageFont.truetype(font_path, 45)
        cta1 = "Theo dõi "
        cta2 = "TN Studio (@tnstudio)"
        cta3 = "để cập nhật tin tức công nghệ mới nhất nhé!"
        
        # Get width for center alignment
        w1 = c_font.getbbox(cta1)[2]
        w2 = c_font.getbbox(cta2)[2]
        w3 = c_font.getbbox(cta3)[2]
        
        # CTA background card (40px padding)
        pad_x, pad_y = 40, 30
        box_w = max(w1 + w2, w3) + pad_x * 2
        box_h = 150 + pad_y * 2
            
        target_cy = (img.height - box_h) // 2
        # Slide up from bottom of screen
        cta_y = ease_out_cubic(time_since_start, start=img.height + 50, end=target_cy, duration=0.8)
        
        cx = img.width // 2
        box_x = cx - box_w // 2
        
        # Render dark blue background
        dark_blue_cta = (20, 40, 80, 240) # Translucent dark blue
        draw_main.rounded_rectangle([box_x, cta_y, box_x + box_w, cta_y + box_h], radius=20, fill=dark_blue_cta)
        
        # Render text
        # Line 1: Follow TN Studio (@tnstudio)
        # Separate text to highlight "TN Studio (@tnstudio)" in yellow
        p_w = w1
        line1_w = p_w + w2
        x1 = cx - line1_w // 2
        
        draw_main.text((x1, cta_y + pad_y), cta1, font=c_font, fill=(255, 255, 255, 255))
        draw_main.text((x1 + p_w, cta_y + pad_y), cta2, font=c_font, fill=(255, 215, 0, 255)) # Yellow
        
        # Line 2: to stay updated on the latest tech news!
        x2 = cx - w3 // 2
        draw_main.text((x2, cta_y + pad_y + 70), cta3, font=c_font, fill=(255, 255, 255, 255))
        
        # Skip subtitles during CTA screen transition
        return np.array(img.convert("RGB"))
        
    # 3. Render Subtitles (Positioned mid-screen to prevent overlapping the banner)
    active_chunk = None
    for chunk in chunks:
        if chunk["start"] <= t <= chunk["end"]:
            active_chunk = chunk
            break
            
    if not active_chunk:
        return np.array(img.convert("RGB"))
        
    font_size = 55
    max_width = img.width - 2 * margin
    lines = []
    current_line = []
    current_line_width = 0
    space_width = font_sub.getbbox(" ")[2]
    
    for word_info in active_chunk["words"]:
        word_text = word_info["word"].upper()
        w = font_sub.getbbox(word_text)[2]
        if current_line_width + w > max_width and current_line:
            lines.append(current_line)
            current_line = []
            current_line_width = 0
        current_line.append((word_text, word_info))
        current_line_width += w + space_width
    if current_line:
        lines.append(current_line)
        
    total_text_height = len(lines) * (font_size + 15)
    y = target_banner_y - total_text_height - 60
    
    sharp_layer = Image.new("RGBA", img.size, (0,0,0,0))
    sharp_draw = ImageDraw.Draw(sharp_layer)
    
    for line in lines:
        line_width = sum([font_sub.getbbox(w[0])[2] for w in line]) + space_width * (len(line) - 1)
        x = (img.width - line_width) // 2
        for text, word_info in line:
            w = font_sub.getbbox(text)[2]
            if t >= word_info["start"]:
                # Precise time alignment without lingering frames
                is_active = word_info["start"] <= t <= word_info["end"]
                
                if is_active:
                    # Render light blue padding block behind active text
                    pad_x = 20
                    pad_y = 15
                    bg_color = (85, 170, 255, 255) # Bright light blue
                    sharp_draw.rounded_rectangle(
                        [x - pad_x, y - pad_y + 10, x + w + pad_x, y + font_size + pad_y - 5],
                        radius=15, fill=bg_color
                    )
                
                # Render white text with thick black outline
                sharp_draw.text((x, y), text, font=font_sub, fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255))
            
            x += w + space_width
        y += font_size + 15
        
    # Merge layers
    img.paste(sharp_layer, mask=sharp_layer)
        
    return np.array(img.convert("RGB"))

def build_video(audio_path, media_path, word_boundaries, output_path, article_title="", category="Tin Tức", key_points=[], scene_index=0, source_name="", publish_date="", is_last_scene=False, font_path="Montserrat-Bold.ttf"):
    print(f"Rendering video: {output_path}...")
    
    # Load audio
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # Check media type (Video or Image)
    ext = media_path.split('.')[-1].split('?')[0].lower()
    is_video = ext in ['mp4', 'webm', 'mov', 'avi']
    
    bg_video_clip = None
    if is_video:
        try:
            frame_maker, bg_video_clip = make_video_background_clip(media_path, duration)
        except Exception:
            frame_maker = make_ken_burns_clip(media_path, duration) # Fallback if video fails
    else:
        frame_maker = make_ken_burns_clip(media_path, duration)
    
    # Split into chunks
    chunks = split_into_chunks(word_boundaries, chunk_size=5)
    
    # Create VideoClip with custom frame processor
    from moviepy.editor import VideoClip
    
    def process_frame(get_frame, t):
        frame = frame_maker(t)
        frame_with_overlays = draw_overlays_and_subtitles(
            frame, t, duration, chunks, font_path, 
            article_title=article_title, category=category, 
            key_points=key_points, scene_index=scene_index,
            source_name=source_name, publish_date=publish_date,
            is_last_scene=is_last_scene
        )
        return frame_with_overlays
        
    video_clip = VideoClip(lambda t: process_frame(frame_maker, t), duration=duration)
    
    # Attach audio directly
    video_clip = video_clip.set_audio(audio_clip)
    
    video_clip.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        threads=4,
        preset="ultrafast"
    )
    
    # Close background video clip if present to avoid memory leaks
    if bg_video_clip:
        bg_video_clip.close()
        
    print(f"Completed video export: {output_path}")

if __name__ == "__main__":
    pass
