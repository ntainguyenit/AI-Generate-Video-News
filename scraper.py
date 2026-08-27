import os
from newspaper import Article

def scrape_article(url):
    """
    Tải và phân tích bài báo từ URL.
    Trả về dict chứa title, text và top_image.
    """
    print(f"[*] Đang tải nội dung từ: {url}")
    try:
        article = Article(url, language='vi')
        article.download()
        article.parse()
        
        data = {
            "title": article.title,
            "text": article.text,
            "top_image": article.top_image,
            "authors": article.authors,
            "publish_date": article.publish_date
        }
        print("[+] Tải bài báo thành công.")
        return data
    except Exception as e:
        print(f"[-] Lỗi khi tải bài báo: {e}")
        return None

if __name__ == "__main__":
    # Test thử với một link bài báo
    test_url = "https://vnexpress.net/thu-tuong-keu-goi-doanh-nghiep-my-dau-tu-vao-viet-nam-4654946.html"
    data = scrape_article(test_url)
    if data:
        print("Title:", data['title'])
        print("Image:", data['top_image'])
        print("Content len:", len(data['text']))
