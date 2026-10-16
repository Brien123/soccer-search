import sys
import torch
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

query_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "defensive pressure leading to a ball recovery"

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

print(f"\nUser Analytical Query: '{query_text}'\n" + "="*60)
print("Retrieved Context (Prepared for LLM Prompt):\n")

context_chunks = []
for i, hit in enumerate(response["hits"]["hits"], 1):
    source = hit["_source"]
    narrative = source.get("narrative")
    context_chunks.append(narrative)
    print(f"[{i}] Minute {source.get('minute')} | Team: {source.get('team')} | {narrative}")

print("\n" + "="*60)
print("Prompt Template Ready for LLM Generation:")
print(f"Based on the following match events:\n" + "\n".join([f"- {c}" for c in context_chunks]))
print(f"\nAnswer the user query: '{query_text}'")