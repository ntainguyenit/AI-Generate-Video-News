import os
from newspaper import Article

def scrape_article(url):
    """
    Download and parse article from URL.
    Returns a dict containing title, text, and top_image.
    """
    print(f"Downloading content from: {url}")
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
        print("Article downloaded successfully.")
        return data
    except Exception as e:
        print(f"Error downloading article: {e}")
        return None

if __name__ == "__main__":
    # Test with an article URL
    test_url = "https://vnexpress.net/thu-tuong-keu-goi-doanh-nghiep-my-dau-tu-vao-viet-nam-4654946.html"
    data = scrape_article(test_url)
    if data:
        print("Title:", data['title'])
        print("Image:", data['top_image'])
        print("Content len:", len(data['text']))
