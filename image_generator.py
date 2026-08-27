import requests
import urllib.parse
import os

def download_image(url, output_path):
    """
    Tải ảnh từ URL tĩnh.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"[-] Lỗi khi tải ảnh {url}: {e}")
        return False

def generate_ai_image(prompt, output_path):
    """
    Tạo ảnh bằng AI miễn phí từ pollinations.ai
    Tỷ lệ 9:16 (1080x1920)
    """
    print(f"[*] Đang tạo ảnh AI cho prompt: '{prompt}'")
    # Thêm thông tin style để ảnh chuyên nghiệp hơn
    style_prompt = f"{prompt}, professional photography, high quality, highly detailed, vertical 9:16 format"
    encoded_prompt = urllib.parse.quote(style_prompt)
    
    # Kích thước dọc
    width = 1080
    height = 1920
    
    # URL pollinations (nologo=true để bỏ logo)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    return download_image(url, output_path)

if __name__ == "__main__":
    generate_ai_image("a futuristic city with flying cars", "test_ai_image.jpg")
    print("Done generating test image.")
