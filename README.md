# Finance News Summary System

## System Architecture
![system_architecture](system_architecture.png)

## Worker pipeline
![worker_pipeline](worker_pipeline.png)

## Quick Start
```
python news_url_collector.py --query keyword --start_data YY-MM-DD --end_date YY-MM-DD --language en --sort_by relevancy --page 1
```
This script will use newsapi to get urls of news with keyword

```
python news_crawler.py --url_file_name url.json --workers num_workers
```
This script will use url in url.json to request html code, and then use trafilatura to extract the content. num_workers is the parameter that can use multi thread requests. Faster

```
python summary_BART.py --num_beams 2 --max_output_length 60 --batch_size 4
```
This script will use the content in news.json, and summarize each news. num_beams controls the quality of summary, max_output_length regarding the length of summary, batch_size is related to parallel summarizing.