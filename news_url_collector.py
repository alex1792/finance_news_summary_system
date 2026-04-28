import sys
import json
import argparse
from newsapi import NewsApiClient

"""
This script is to get the html data from the website, mainly for finance news websites.
We use NewsAPI to get the news html data.

You can search for articles with any combination of the following criteria:

- Keyword or phrase. Eg: find all articles containing the word 'Microsoft'.
- Date published. Eg: find all articles published yesterday.
- Source domain name. Eg: find all articles published on thenextweb.com.
- Language. Eg: find all articles written in English.

You can sort the results in the following orders:

- Date published
- Relevancy to search keyword
- Popularity of source

"""
class UrlCollector:
    def print_usage(self):
        print("Usage: python news_url_collector.py --query <query> --start_date <start_date> --end_date <end_date> --language <language> --sort_by <sort_by> --page <page>")
        print("Parameter - query: the query string for the news search")
        print("Parameter - start_date: the start date for the news search. Format: YYYY-MM-DD")
        print("Parameter - end_date: the end date for the news search. Format: YYYY-MM-DD")
        print("Parameter - language: the language for the news search (default: en)")
        print("Parameter - sort_by: the sort by for the news search (default: relevancy)")
        print("Parameter - page: the page number for the news search (default: 1)")
        print("Example: python news_url_collector.py --query 'bitcoin' --start_date '2026-04-01' --end_date '2026-04-23' --language 'en' --sort_by 'relevancy' --page 1")

    def get_url(self,q, start_date, end_date, language='en', sort_by='relevancy', page=1):
        # init
        news_api = NewsApiClient(api_key='bede7a513ac24c42bdc6b860a86c70da')

        # /v2/top-headlines
        # top_headlines = news_api.get_top_headlines(category='technology',
        #                                           language='en',
        #                                           country='us')

        # /v2/everything
        all_articles = news_api.get_everything(q=q,
                                        from_param=start_date,
                                        to=end_date,
                                        language=language,
                                        sort_by=sort_by,
                                        page=page)

        # /v2/top-headlines/sources
        # sources = news_api.get_sources()

        articles = all_articles['articles']
        # print(articles)

        # write to json file
        with open('output/json/url.json', 'w') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch news from NewsAPI and save to url.json file')
    parser.add_argument('--query', type=str, required=True, help='The query string for the news search')
    parser.add_argument('--start_date', type=str, required=True, help='The start date for the news search. Format: YYYY-MM-DD')
    parser.add_argument('--end_date', type=str, required=True, help='The end date for the news search. Format: YYYY-MM-DD')
    parser.add_argument('--language', type=str, required=False, default='en', help='The language for the news search (default: en)')
    parser.add_argument('--sort_by', type=str, required=False, default='relevancy', help='The sort by for the news search (default: relevancy)')
    parser.add_argument('--page', type=int, required=False, default=1, help='The page number for the news search (default: 1)')
    args = parser.parse_args()

    url_collector = UrlCollector()
    url_collector.get_url(args.query, args.start_date, args.end_date, args.language, args.sort_by, args.page)