import os
import requests

def send_to_telegram(video_path, text_content):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("[-] Bỏ qua Telegram (không tìm thấy Token hoặc Chat ID trong .env).")
        return
        
    print(f"\n[*] Đang gửi siêu phẩm lên Telegram Bot cho Sếp duyệt...")
    
    # 1. Gửi Video
    video_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    try:
        with open(video_path, 'rb') as vf:
            resp = requests.post(video_url, data={"chat_id": chat_id}, files={"video": vf})
            if resp.status_code != 200:
                print(f"[-] Lỗi gửi Video Telegram: {resp.text}")
            else:
                print("  -> Gửi Video thành công!")
    except Exception as e:
        print(f"[-] Lỗi gửi video: {e}")
        
    # 2. Gửi Text (Caption) thành một tin nhắn riêng biệt để tiện Copy
    if text_content:
        text_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Chia nhỏ nếu text quá dài (Telegram max 4096)
        max_len = 4000
        chunks = [text_content[i:i+max_len] for i in range(0, len(text_content), max_len)]
        
        for chunk in chunks:
            data = {"chat_id": chat_id, "text": chunk}
            try:
                resp = requests.post(text_url, data=data)
                if resp.status_code == 200:
                    print("  -> Gửi Caption thành công!")
                else:
                    print(f"[-] Lỗi gửi Caption: {resp.text}")
            except Exception as e:
                print(f"[-] Lỗi gửi text: {e}")
