import json
import argparse
import torch
import time
from transformers import AutoTokenizer, BartForConditionalGeneration

class SummaryBART:
    def __init__(self, model_name="facebook/bart-large-cnn", num_beams=2,max_output_length=20):
        self.model = BartForConditionalGeneration.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.num_beams = num_beams
        self.max_output_length = max_output_length
        self.batch_size = 10
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def summarize(self, article):
        # max token length is 1024 (number of tokens), and return tensor is pytorch tensor
        inputs = self.tokenizer([article], max_length=1024, return_tensors="pt")
        print(f"Input tokens: {inputs["input_ids"].shape[1]}")
        
        # num_beams=2 means the width of beam search is 2, which preserve 2 different paths (2 different summaries)
        # the larger the num_beams, the better quality of the summary, but the trade-off is the speed
        # min_length, max_length are the min and max number of tokens the output summary should have
        summary_ids = self.model.generate(inputs["input_ids"], num_beams=self.num_beams, min_length=0, max_length=self.max_output_length)

        return self.tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    def batch_summarize(self, articles):
        inputs = self.tokenizer(articles, max_length=1024, truncation=True, padding=True, return_tensors="pt")
        
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"].to(self.device), 
                attention_mask=inputs["attention_mask"].to(self.device), 
                num_beams=self.num_beams, min_length=0, 
                max_length=self.max_output_length
            )

            return self.tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)

    def write_summary_to_file(self, output_f,summary):
        output_f.write(json.dumps(summary, ensure_ascii=False) + '\n')
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Summary BART')
    parser.add_argument('--model_name', type=str, required=False, help='The model name', default='facebook/bart-large-cnn')
    parser.add_argument('--num_beams', type=int, required=True, help='The number of beams', default=2)
    parser.add_argument('--max_output_length', type=int, required=True, help='The max output length', default=40)
    parser.add_argument('--batch_size', type=int, required=False, help='The batch size', default=10)
    args = parser.parse_args()

    # initialize the summary BART model
    summary_BART = SummaryBART('facebook/bart-large-cnn', args.num_beams, args.max_output_length)
    
    # from news.json read the article
    start_time = time.perf_counter()
    with open('news.json', 'r') as f:
        # for line in f:
        #     article = json.loads(line)['content']

        #     summary = summary_BART.summarize(article)
        #     summary_BART.write_summary_to_file(summary)

        with open('summary.json', 'w') as output_f:
            batch = []
            
            for line in f:
                article = json.loads(line)['content']
                if len(batch) < args.batch_size:
                    batch.append(article)
                else:
                    summaries = summary_BART.batch_summarize(batch)
                    batch = []
                    batch.append(article)

                    for summary in summaries:
                        summary_BART.write_summary_to_file(output_f, summary)
        
            

    end_time = time.perf_counter()
    print(f"Time taken: {end_time - start_time} seconds")
    
