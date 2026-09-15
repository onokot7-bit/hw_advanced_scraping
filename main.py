import sys
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


KEYWORDS = ["дизайн", "фото", "web", "python"]
URL = "https://habr.com/ru/articles/"
# Десктопная версия страницы содержит хабы и полный анонс в HTML.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
}


def find_articles(html, keywords):
    """Находит статьи по всей preview-информации на странице ленты."""
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.tm-articles-list__item")
    if not articles:
        raise ValueError("Карточки статей не найдены. Проверьте разметку сайта.")

    keywords = [word.strip().casefold() for word in keywords if word.strip()]
    results = []
    seen_links = set()

    for article in articles:
        # Весь текст карточки: автор, заголовок, хабы, метки и анонс.
        preview = article.get_text(" ", strip=True).casefold()
        if not any(word in preview for word in keywords):
            continue

        title_tag = article.select_one("a.tm-title__link")
        time_tag = article.find("time")
        if title_tag is None or time_tag is None:
            raise ValueError("Не удалось получить заголовок или дату статьи.")

        href = title_tag.get("href")
        published = time_tag.get("datetime")
        if not href or not published:
            raise ValueError("У статьи отсутствует ссылка или дата публикации.")

        link = urljoin(URL, href)
        if link in seen_links:
            continue
        seen_links.add(link)

        date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        title = title_tag.get_text(" ", strip=True)
        results.append((date.strftime("%d.%m.%Y"), title, link))

    return results


def main():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        articles = find_articles(response.text, KEYWORDS)
    except (requests.RequestException, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    for date, title, link in articles:
        print(f"{date} – {title} – {link}")

    if not articles:
        print("На текущей странице нет статей с заданными ключевыми словами.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
