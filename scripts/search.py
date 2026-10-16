import sys
import torch
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

query_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "shot with high xG"

dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float32
model = SentenceTransformer("google/embeddinggemma-2", model_kwargs={"torch_dtype": dtype})

es = Elasticsearch("http://localhost:9200")
index_name = "statsbomb_events"

prefixed_query = f"title: none | text: {query_text}"
query_vector = model.encode(prefixed_query, normalize_embeddings=True).tolist()

search_body = {
    "size": 5,
    "query": {
        "bool": {
            "should": [
                {
                    "match": {
                        "narrative": {
                            "query": query_text,
                            "boost": 1.0
                        }
                    }
                },
                {
                    "knn": {
                        "field": "narrative_vector",
                        "query_vector": query_vector,
                        "k": 5,
                        "num_candidates": 50,
                        "boost": 2.0
                    }
                }
            ],
            "minimum_should_match": 1
        }
    }
}

response = es.search(index=index_name, body=search_body)

print(f"\nQuery: '{query_text}'\n" + "="*50)
for hit in response["hits"]["hits"]:
    source = hit["_source"]
    score = hit["_score"]
    print(f"Score: {score:.4f} | Minute {source.get('minute')} | Team: {source.get('team')}")
    print(f"Narrative: {source.get('narrative')}\n")