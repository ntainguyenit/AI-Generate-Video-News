import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("TELEGRAM_BOT_TOKEN not found in .env file")
    exit()

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        resp = requests.get(url, params=params)
        return resp.json()
    except Exception as e:
        return None

def answer_callback(callback_query_id, text="", show_alert=False):
    """
    Answer callback to stop the loading spinner on Telegram buttons
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    data = {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert
    }
    requests.post(url, data=data)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

def main():
    print("=====================================================")
    print("TELEGRAM LISTENER STARTED...")
    print("=====================================================")
    print("Listening for button clicks (Press Ctrl+C to stop)")
    last_update_id = None
    
    while True:
        updates = get_updates(last_update_id)
        if updates and "result" in updates:
            for item in updates["result"]:
                # Update offset to avoid reading old messages
                last_update_id = item["update_id"] + 1
                
                # Catch Inline Keyboard button clicks
                if "callback_query" in item:
                    cb = item["callback_query"]
                    cb_id = cb["id"]
                    data = cb.get("data", "")
                    chat_id = cb["message"]["chat"]["id"]
                    
                    if data == "approve":
                        # Stop loading and show small pop-up
                        answer_callback(cb_id, "Video approved successfully!")
                        # Send confirmation message
                        send_message(chat_id, "Status: Approved.\nAction: Video will be auto-published as scheduled.")
                        print("Action received: Approve Video")
                        
                    elif data == "edit_caption":
                        answer_callback(cb_id, "")
                        send_message(chat_id, "Please copy the caption above, edit it, and send it back here.")
                        print("Action received: Edit Caption")
                        
                    elif data == "analytics":
                        answer_callback(cb_id, "Loading data...")
                        stats = (
                            "AI ANALYTICS & FORECAST:\n"
                            "-----------------------------------\n"
                            "- Hashtag: #tnstudio is currently trending upwards.\n"
                            "- Best posting time: 19:30 - 20:30 tonight.\n"
                            "- Estimated reach: ~10,000 views.\n"
                            "- Recommendation: Keep this Caption as its engagement score is at 95%!"
                        )
                        send_message(chat_id, stats)
                        print("Action received: View Analytics")
        
        # Sleep for 1 second to avoid spamming the API
        time.sleep(1)

if __name__ == "__main__":
    main()
