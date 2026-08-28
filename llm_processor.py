import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_video_script(article_text):
    """
    Use Gemini API to summarize the article and divide it into scenes, along with a social media caption.
    Returns a tuple: (category, key_points, scenes list, reels_caption)
    """
    print("Generating video script using Gemini API...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return None

    try:
        # Initialize client with api_key
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
You are a professional video editor. Summarize the following article into a video script (Reels/Shorts/TikTok) with a duration of about 60-90 seconds.
Divide the script into 5-7 short scenes. Each scene must contain a LONG and DETAILED dialogue sentence (about 3-4 complete sentences, providing in-depth information) to retain viewers and extend the video length. Include a short English image_prompt for each scene to search for or generate corresponding illustration images.
Also, identify the category of the article (short, max 3 words, e.g., "Technology", "Sports", "Economy").
Extract the 3-4 most important key_points of the article to display on the screen.
Write a caption for Reels/TikTok (reels_caption) based on the article content. The caption structure must include:
1. TITLE (UPPERCASE, clickbait/attractive).
2. Main content (Engaging summary, spaced into readable paragraphs).
3. Call to Action (CTA) suitable for the content.
4. Trending hashtag suggestions, must include #tnstudio at the very end.
Combine this caption into a single string containing newline characters (\n).

The output format requirement is strictly structured JSON code as follows (no other text included):
{{
  "category": "Category name",
  "key_points": [
    "Key point 1",
    "Key point 2",
    "Key point 3"
  ],
  "scenes": [
    {{
      "text": "Dialogue for scene 1",
      "image_prompt": "Image prompt for scene 1"
    }},
    {{
      "text": "Dialogue for scene 2",
      "image_prompt": "Image prompt for scene 2"
    }}
  ],
  "reels_caption": "Sample caption content..."
}}

Article content:
{article_text}
"""
        # Call gemini-3.6-flash which is fast and supports JSON schema
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        script_data = json.loads(response.text)
        print("Script and caption generated successfully.")
        category = script_data.get("category", "News")
        key_points = script_data.get("key_points", [])
        scenes = script_data.get("scenes", [])
        reels_caption = script_data.get("reels_caption", "")
        return category, key_points, scenes, reels_caption
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "News", [], None, ""

if __name__ == "__main__":
    test_text = "Tập đoàn công nghệ Apple vừa ra mắt iPhone 16 với nhiều cải tiến về camera và trí tuệ nhân tạo. Sự kiện thu hút sự chú ý lớn từ giới mộ điệu trên toàn thế giới. Giá khởi điểm từ 799 USD."
    cat, kps, scenes, caption = generate_video_script(test_text)
    if scenes:
        print(f"Category: {cat}")
        print(f"Key Points: {kps}")
        print(json.dumps(scenes, indent=2, ensure_ascii=False))
        print(f"\nCaption:\n{caption}")
