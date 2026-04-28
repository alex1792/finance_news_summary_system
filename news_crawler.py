import requests
import time
import json
import argparse
import trafilatura
from bs4 import BeautifulSoup
import multiprocessing as mp
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

class NewsCrawler:
    def __init__(self, url_file_name='output/json/url.json', load_urls=True):
        self.url_file_name = url_file_name
        self.urls = []
        self.items = []
        self.load_urls = load_urls

        if self.load_urls:
            # read urls from file, and save urls to self.urls
            with open(self.url_file_name, 'r') as f:
                for line in f:
                    json_data = json.loads(line)
                    self.urls.append(json_data['url'])
                    self.items.append(json.loads(line))
   
    def crawl_news(self, item, new_f_name=None):
        url = item['url']
        response = requests.get(url, headers=DEFAULT_HEADERS)
        html = response.text

        # extract text content from html code using trafilatura
        text = trafilatura.extract(html)

        # print(text)
        # save to another json file
        new_json_data = {
            "source": item['source']['name'] if item['source'] and item['source']['name'] else "",
            "title": item.get('title'),
            "author": item.get('author'),
            "description": item.get('description'),
            "url": url,
            "publishedAt": item.get('publishedAt'),
            "content": text
        }

        if self.load_urls:
            with open(new_f_name, 'w', encoding='utf-8') as new_f:
                new_f.write(json.dumps(new_json_data, ensure_ascii=False) + '\n')

        return new_json_data

    def crawl_all_news(self):
        success_cnt = 0
        records = []
        
        for item in self.items:
            record = self._build_crawled_record(item)
            records.append(record)
            time.sleep(3)
        
        with open('output/json/news.json', 'w') as new_f:
            for rec in records:
                new_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                if rec.get('content'):
                    success_cnt += 1
                else:
                    print(f"Error: {rec.get('error')}")

        print(f"Successfully crawled {success_cnt} news")

    def _build_crawled_record(self, item):
        url = item['url']
        source = item.get('source', {})
        name = source.get('name', '')

        try:
            response = requests.get(url, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            text = trafilatura.extract(response.text)

        except Exception as e:
            return {
                "source": name,
                "title": item.get('title'),
                "author": item.get('author'),
                "description": item.get('description'),
                "url": url,
                "publishedAt": item.get('publishedAt'),
                "content": "",
                "error": str(e)
            }
        return {
            "source": name,
            "title": item.get('title'),
            "author": item.get('author'),
            "description": item.get('description'),
            "url": url,
            "publishedAt": item.get('publishedAt'),
            "content": text,
        }
    
    def crawl_all_news_parallel(self, max_workers=8):
        success_cnt = 0
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            records = list(ex.map(self._build_crawled_record, self.items))
            time.sleep(3)

        with open('output/json/news.json', 'w', encoding='utf-8') as new_f:
            for rec in records:
                new_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                if rec.get('content'):
                    success_cnt += 1
                else:
                    print(f"Error: {rec.get('error')}")
        
        print(f"Successfully crawled {success_cnt} news")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl news from urls and save to news.json file')
    parser.add_argument('--url_file_name', type=str, required=False, default='output/json/url.json', help='The name of the url file')
    parser.add_argument('--workers', type=int, required=False, default=8, help='The number of workers to use')
    args = parser.parse_args()

    news_crawler = NewsCrawler(args.url_file_name)

    # start_time = time.perf_counter()
    # news_crawler.crawl_all_news()
    # end_time = time.perf_counter()
    # print(f"Single ThreadTime taken: {end_time - start_time} seconds")

    start_time = time.perf_counter()
    news_crawler.crawl_all_news_parallel(args.workers)
    end_time = time.perf_counter()
    print(f"Parallel Thread Time taken: {end_time - start_time} seconds")

    # test news crawler with single url
    # url = "https://tw.news.yahoo.com/川普槍擊案是因為太自由-學者揭中共處理不同聲音的極權手法-005500457.html"
    # test_data = {
    #     "source": None,
    #     "title": None,
    #     "author": None,
    #     "description": None,
    #     "url": url,
    #     "publishedAt": None,
    # }

    # with open('output/json/test_data.json', 'w') as f:
    #     news_crawler.crawl_news(test_data, f)
    