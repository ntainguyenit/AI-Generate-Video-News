import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_video_script(article_text):
    """
    Sử dụng Gemini API để tóm tắt bài báo và chia thành các phân cảnh, kèm theo Caption đăng mxh.
    Trả về tuple: (category, key_points, danh sách scenes, reels_caption)
    """
    print("[*] Đang tạo kịch bản video bằng Gemini API...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[-] Lỗi: Không tìm thấy GEMINI_API_KEY trong biến môi trường.")
        return None

    try:
        # Initialize client with api_key
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
Bạn là một biên tập viên video chuyên nghiệp. Hãy tóm tắt nội dung bài báo sau thành một kịch bản video (Reels/Shorts/TikTok) thời lượng khoảng 60-90 giây.
Chia kịch bản thành 5-7 phân cảnh nhỏ (scenes). Mỗi phân cảnh chứa một câu thoại DÀI và CHI TIẾT (khoảng 3-4 câu hoàn chỉnh, cung cấp thông tin sâu) để giữ chân người xem và kéo dài video. Kèm theo đó là một từ khóa (prompt tiếng Anh ngắn) để tìm hoặc tạo ảnh minh họa tương ứng.
Đồng thời xác định chuyên mục (category) của bài báo (ngắn gọn tối đa 3 từ, ví dụ: "Tin Công Nghệ", "Thể Thao", "Kinh Tế").
Ngoài ra, trích xuất 3-4 ý chính (key_points) quan trọng nhất của bài báo để hiển thị trên màn hình.
Đồng thời, viết một đoạn caption để đăng Reels/TikTok (reels_caption) dựa trên nội dung bài báo. Cấu trúc caption phải bao gồm:
1. TIÊU ĐỀ (Viết IN HOA, giật tít thu hút).
2. Nội dung chính (Tóm tắt hấp dẫn, chia đoạn dễ nhìn).
3. Lời kêu gọi hành động (CTA) phù hợp với nội dung.
4. Gợi ý Hashtag dễ trending, bắt buộc phải có #tnstudio ở cuối cùng.
Vui lòng gộp chung caption này thành một chuỗi (string) duy nhất có chứa ký tự xuống dòng (\n).

Yêu cầu định dạng đầu ra chỉ là mã JSON có cấu trúc như sau (không kèm theo văn bản khác):
{{
  "category": "Tên chuyên mục",
  "key_points": [
    "Ý chính 1",
    "Ý chính 2",
    "Ý chính 3"
  ],
  "scenes": [
    {{
      "text": "Câu thoại phân cảnh 1",
      "image_prompt": "Image prompt for scene 1"
    }},
    {{
      "text": "Câu thoại phân cảnh 2",
      "image_prompt": "Image prompt for scene 2"
    }}
  ],
  "reels_caption": "Nội dung caption mẫu..."
}}

Nội dung bài báo:
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
        print("[+] Tạo kịch bản và caption thành công.")
        category = script_data.get("category", "Tin Tức")
        key_points = script_data.get("key_points", [])
        scenes = script_data.get("scenes", [])
        reels_caption = script_data.get("reels_caption", "")
        return category, key_points, scenes, reels_caption
        
    except Exception as e:
        print(f"[-] Lỗi khi gọi Gemini API: {e}")
        return "Tin Tức", [], None, ""

if __name__ == "__main__":
    test_text = "Tập đoàn công nghệ Apple vừa ra mắt iPhone 16 với nhiều cải tiến về camera và trí tuệ nhân tạo. Sự kiện thu hút sự chú ý lớn từ giới mộ điệu trên toàn thế giới. Giá khởi điểm từ 799 USD."
    cat, kps, scenes, caption = generate_video_script(test_text)
    if scenes:
        print(f"Category: {cat}")
        print(f"Key Points: {kps}")
        print(json.dumps(scenes, indent=2, ensure_ascii=False))
        print(f"\nCaption:\n{caption}")
