import re
import urllib.request

URLS = {
    "اونس جهانی": "https://www.tgju.org/profile/ons",
    "مثقال": "https://www.tgju.org/profile/mesghal",
    "گرم ۱۸ عیار": "https://www.tgju.org/profile/geram18",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.8",
}

for name, url in URLS.items():
    print("=" * 60)
    print("نام:", name)
    print("آدرس:", url)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            print("کد وضعیت:", resp.status)
            print("حجم صفحه (کاراکتر):", len(html))
    except Exception as e:
        print("خطا:", repr(e))
        continue

    title = re.search(r"<title>(.*?)</title>", html, re.S)
    print("عنوان صفحه:", title.group(1).strip() if title else "پیدا نشد")

    found = re.findall(r'data-col="([^"]+)"[^>]*>\s*([^<]+?)\s*<', html)
    print("تعداد عنصرهای data-col با متن:", len(found))
    for key, text in found[:20]:
        print("  ", key, "=>", text)
