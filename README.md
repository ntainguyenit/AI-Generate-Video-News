[English Below]

**AI Tự Động Tạo Video Tin Tức**

Công cụ hoàn toàn tự động giúp chuyển đổi bài báo thành video định dạng dọc (Reels, TikTok, Shorts) chuyên nghiệp bằng trí tuệ nhân tạo.

**Tính Năng Chính**
- Cào dữ liệu bài báo tự động từ URL.
- Tóm tắt và lên kịch bản video bằng Gemini AI.
- Tạo giọng đọc AI chân thực qua Edge-TTS (Hỗ trợ nhiều giọng đọc).
- Tạo video tự động với hiệu ứng UI hiện đại (Glassmorphism, Slide-in, Phụ đề Karaoke).
- Tự động chèn nhạc nền và hỗ trợ chèn ảnh/video tùy chỉnh.
- Gửi video tự động qua Telegram Bot sau khi hoàn thành.
- Cơ chế khôi phục phiên làm việc (Session Recovery) khi xảy ra gián đoạn.

**Yêu Cầu Hệ Thống**
- Python 3.10 trở lên
- ImageMagick (Dành cho MoviePy)
- FFmpeg

**Cài Đặt**
1. Clone repository:
```bash
git clone https://github.com/ntainguyenit/AI-Generate-Video-News.git
cd AI-Generate-Video-News
```

2. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

3. Cấu hình biến môi trường:
Đổi tên file `.env.example` thành `.env` và điền thông tin của bạn:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```
**Lưu ý Bảo mật:** API Key và Token là thông tin bí mật. Tuyệt đối không lưu trực tiếp (hardcode) vào source code hoặc commit file `.env` lên GitHub. Mã nguồn được thiết kế để đọc cấu hình thông qua Environment Variables nhằm đảm bảo an toàn tối đa.

**Sử Dụng**
Khởi chạy hệ thống bằng lệnh:
```bash
python main.py
```

---

**AI Auto-Generate News Video**

A fully automated tool that converts news articles into short vertical videos (Reels, TikTok, Shorts) using artificial intelligence.

**Key Features**
- Automatically scrapes article data from URLs.
- Summarizes and scripts professional videos using Gemini AI.
- Generates realistic AI voices via Edge-TTS (Supports multiple voice profiles).
- Automatically builds videos with modern UI effects (Glassmorphism, Slide-in, Karaoke Subtitles).
- Automatically mixes background music and supports custom media overlays.
- Delivers the final video automatically via Telegram Bot.
- Smart session recovery mechanism for uninterrupted workflows.

**System Requirements**
- Python 3.10 or higher
- ImageMagick (For MoviePy)
- FFmpeg

**Installation**
1. Clone the repository:
```bash
git clone https://github.com/ntainguyenit/AI-Generate-Video-News.git
cd AI-Generate-Video-News
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Environment Variables:
Rename `.env.example` to `.env` and configure your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```
**Security Notice:** API Keys and Tokens are secret credentials. Never hardcode them into the source code or commit the `.env` file to GitHub. This application is designed to securely read credentials from Environment Variables.

**Usage**
Run the main script:
```bash
python main.py
```
