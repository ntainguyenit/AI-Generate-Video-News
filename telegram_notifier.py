import os
import requests

def send_to_telegram(video_path, text_content):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Skipping Telegram notification (Token or Chat ID missing in .env).")
        return
        
    print("\nSending generated video to Telegram Bot...")
    
    # 1. Send Video
    video_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    try:
        with open(video_path, 'rb') as vf:
            resp = requests.post(video_url, data={"chat_id": chat_id}, files={"video": vf})
            if resp.status_code != 200:
                print(f"Error sending Video to Telegram: {resp.text}")
            else:
                print("Video sent successfully!")
    except Exception as e:
        print(f"Error sending video: {e}")
        
    # 2. Send Text (Caption) as a separate message
    if text_content:
        text_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Split text if it exceeds Telegram's 4096 character limit
        max_len = 4000
        chunks = [text_content[i:i+max_len] for i in range(0, len(text_content), max_len)]
        
        for chunk in chunks:
            data = {"chat_id": chat_id, "text": chunk}
            try:
                resp = requests.post(text_url, data=data)
                if resp.status_code == 200:
                    print("Caption sent successfully!")
                else:
                    print(f"Error sending Caption: {resp.text}")
            except Exception as e:
                print(f"Error sending text: {e}")
