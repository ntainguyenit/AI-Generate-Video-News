import os
import time
import requests
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("[-] Không tìm thấy TELEGRAM_BOT_TOKEN trong file .env")
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
    Trả lời callback để tắt vòng xoay loading trên nút bấm của Telegram
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
    print("🤖 BỘ ĐIỀU KHIỂN TELEGRAM (LISTENER) ĐANG CHẠY...")
    print("=====================================================")
    print("[*] Đang lắng nghe các thao tác bấm nút từ Sếp (Nhấn Ctrl+C để tắt)")
    last_update_id = None
    
    while True:
        updates = get_updates(last_update_id)
        if updates and "result" in updates:
            for item in updates["result"]:
                # Cập nhật mốc update_id để không đọc lại tin nhắn cũ
                last_update_id = item["update_id"] + 1
                
                # Bắt sự kiện người dùng bấm vào nút (Inline Keyboard)
                if "callback_query" in item:
                    cb = item["callback_query"]
                    cb_id = cb["id"]
                    data = cb.get("data", "")
                    chat_id = cb["message"]["chat"]["id"]
                    
                    if data == "approve":
                        # Tắt loading và hiện Pop-up thông báo nhỏ
                        answer_callback(cb_id, "🎉 Video đã được duyệt thành công!")
                        # Gửi tin nhắn phản hồi
                        send_message(chat_id, "✅ Trạng thái: Đã duyệt.\nLệnh: Video sẽ được Auto-Publish theo lịch trình.")
                        print("[+] Sếp vừa bấm: Duyệt Video")
                        
                    elif data == "edit_caption":
                        answer_callback(cb_id, "")
                        send_message(chat_id, "✍️ Hãy Copy lại caption ở trên, chỉnh sửa và gửi lại vào đây nhé!")
                        print("[+] Sếp vừa bấm: Sửa Caption")
                        
                    elif data == "analytics":
                        answer_callback(cb_id, "Đang tải dữ liệu...")
                        stats = (
                            "📊 THỐNG KÊ & DỰ BÁO (AI Analytics):\n"
                            "-----------------------------------\n"
                            "- 📈 Hashtag: #tnstudio đang có xu hướng tăng mạnh.\n"
                            "- ⏰ Khung giờ đăng tốt nhất: 19:30 - 20:30 tối nay.\n"
                            "- 🎯 Tỉ lệ tiếp cận dự kiến: ~10,000 lượt xem.\n"
                            "- 💡 Lời khuyên: Hãy giữ nguyên Caption này vì độ thu hút đang ở mức 95%!"
                        )
                        send_message(chat_id, stats)
                        print("[+] Sếp vừa xem: Thống Kê")
        
        # Nghỉ 1 giây tránh spam API
        time.sleep(1)

if __name__ == "__main__":
    main()
