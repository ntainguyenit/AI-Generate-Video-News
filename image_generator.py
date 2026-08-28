import requests
import urllib.parse
import os

def download_image(url, output_path):
    """
    Download image from a static URL.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return False

def generate_ai_image(prompt, output_path):
    """
    Generate image using free AI from pollinations.ai
    Aspect ratio 9:16 (1080x1920)
    """
    print(f"Generating AI image for prompt: '{prompt}'")
    # Add style information for professional look
    style_prompt = f"{prompt}, professional photography, high quality, highly detailed, vertical 9:16 format"
    encoded_prompt = urllib.parse.quote(style_prompt)
    
    # Vertical resolution
    width = 1080
    height = 1920
    
    # Pollinations URL (nologo=true to remove watermark)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    return download_image(url, output_path)

if __name__ == "__main__":
    generate_ai_image("a futuristic city with flying cars", "test_ai_image.jpg")
    print("Done generating test image.")
