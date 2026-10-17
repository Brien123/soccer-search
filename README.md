# statsbomb-search

## Purpose

This project lets you search football match events with words.
You type a question. The system returns the events that match.

It also answers questions in plain English.
A language model reads the best events and writes an answer with citations.

Example: type "late goals in the final minutes".
The system returns goals that players scored after minute 85.
The RAG tab also explains who scored these goals, with the source events.

## Features

- Keyword search over event narratives with filters (team, player, match, minute range).
- Hybrid search that combines keyword match with vector similarity.
- RAG answers from a local language model, grounded only in retrieved events.
- Citations: each answer shows the top 10 source events for verification.
- Web page with two tabs: Search and Ask RAG.
- Event enrichment: phase (early, late, final minutes), zone (thirds, wide, central), pressure flags, and xG buckets.
- Clean skip rules that drop low-value events (ball receipts, lineups, camera events).
- Numeric search evaluation with precision, recall, F1, nDCG, and MRR.
- A test suite that runs without any live services.

## How It Works

The project has four parts:

1. Raw data: StatsBomb match files in JSON format.
2. Scripts: tools that prepare the data and test the search.
3. Search index: Elasticsearch stores text and vectors.
4. Web app: a FastAPI backend and a web page for search and RAG.

Data flows in this order:

1. `scripts/create_index.py` makes a clean index in Elasticsearch.
2. `scripts/ingest.py` reads match files and writes one sentence per event.
3. Each sentence gets a vector from an embedding model.
4. Elasticsearch stores the sentence, the vector, and facts (team, player, minute, event type, xG).
5. You send a query to the web app or to the API.
6. Elasticsearch returns the best events.
7. In RAG mode, the events go to a language model, which writes the answer.

## Requirements

- Python 3.14
- `uv`
- Docker (for Elasticsearch)
- 1 GB free RAM (for the embedding model)
- LM Studio with a chat model (for RAG answers)

## Start Elasticsearch

Start Elasticsearch before all other steps:

```zsh
docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.15.0
```

Check that it runs:

```zsh
curl -s http://localhost:9200/ | head -5
```

## Install

```zsh
uv sync
```

## Make The Index

This step deletes the old index and makes a new one.
Do this step once:

```zsh
.venv/bin/python scripts/create_index.py
```

## Add Data

This step reads match files and adds them to the index.
It takes some minutes. The model must load first.

Add 3 matches (default):

```zsh
.venv/bin/python scripts/ingest.py
```

Add 10 matches:

```zsh
MAX_MATCHES=10 .venv/bin/python scripts/ingest.py
```

The script skips events with no value, for example ball receipts.
It prints the number of added and skipped events.

## Start The Web App

Start LM Studio first. Load a chat model and start the server on port 1234.
Then start the web app:

```zsh
.venv/bin/uvicorn stats.main:app --reload --port 8000
```

Open this page in a browser:

```text
http://127.0.0.1:8000/
```

The page has two tabs:

1. Search: keyword search with filters.
2. Ask RAG: a question box. The answer appears with the top 10 source events.

## Search With The API

Send a GET request to `/api/search`:

```zsh
curl -s "http://127.0.0.1:8000/api/search?q=high+expected+goals&size=5"
```

You can filter the search:

| Filter       | Meaning                          |
| ------------ | -------------------------------- |
| q            | Words to find in the events      |
| team         | Team name (exact match)          |
| player       | Player name (exact match)        |
| match_id     | Match file name (exact match)    |
| minute_from  | First minute of the time range   |
| minute_to    | Last minute of the time range    |
| size         | Number of results (max 50)       |
| offset       | Number of results to skip        |

## Ask With The API

Send a POST request to `/api/rag`:

```zsh
curl -s -X POST http://127.0.0.1:8000/api/rag \
  -H "Content-Type: application/json" \
  -d '{"question": "who scored late goals in the final minutes?", "size": 10}'
```

The reply has four parts:

| Field     | Meaning                                  |
| --------- | ---------------------------------------- |
| question  | The question you sent                    |
| answer    | The model answer, grounded in the events |
| model     | The model name used                      |
| citations | The source events for verification       |

Check system health:

```zsh
curl -s http://127.0.0.1:8000/api/health
```

## Test The Search From Scripts

Test hybrid search (words plus vectors) without the web app:

```zsh
.venv/bin/python scripts/rag_query.py "key passes leading to a chance"
```

Good test queries:

- "shots taken with high expected goals value"
- "clutch late-game goals scored in the final minutes"
- "defensive pressure high up in the attacking third"
- "goalkeeper performing a high-pressure save action"

## Evaluate The Search

This project measures search quality with numbers, not with feeling.

The evaluation uses a set of questions in `eval/queries.jsonl`.
Most questions have a known answer, defined by a filter.
For example, "late goals" means goals after minute 85.
The system marks a result as correct if it passes that filter.
This gives free and repeatable ground truth for precision, recall, and F1.

Some questions are open, such as "clutch performances".
These have no filter. Add your own labels in `eval/labels.jsonl` to grade them.

### What The Numbers Mean

- Precision: how many of the top results are correct.
- Recall: how many of the correct events the system found.
- F1: the balance between precision and recall.
- nDCG: how good the order of the results is.
- MRR: where the first correct result appears.

### Run The Evaluation

```zsh
.venv/bin/python scripts/evaluate.py --modes keyword,hybrid,oracle
```

The command prints a score table and writes `eval/report.md` and `eval/report.json`.

Options:

| Option     | Default              | Meaning                          |
| ---------- | -------------------- | -------------------------------- |
| queries    | eval/queries.jsonl   | Question set                     |
| labels     | eval/labels.jsonl    | Human labels for open questions  |
| modes      | keyword,hybrid,oracle| Search modes to compare          |
| cutoffs    | 5,10                 | Result counts to score           |
| out-md     | eval/report.md       | Score table output               |
| out-json   | eval/report.json     | Full result output               |

`oracle` is the upper bound. It returns the known answer directly.
Use it to check that the ground truth is correct.

### Current Results

Measured on the local index (7,573 events) with 28 scored questions:

| mode    | P@5   | R@5   | F1@5  | nDCG@5 | P@10  | R@10  | F1@10 | MRR   |
| ------- | ----- | ----- | ----- | ------ | ----- | ----- | ----- | ----- |
| keyword | 0.543 | 0.170 | 0.214 | 0.562  | 0.514 | 0.309 | 0.306 | 0.633 |
| hybrid  | 0.571 | 0.186 | 0.224 | 0.592  | 0.543 | 0.315 | 0.316 | 0.638 |
| oracle  | 0.964 | 0.242 | 0.331 | 0.964  | 0.964 | 0.387 | 0.492 | 0.964 |

Hybrid search beats keyword search on every metric.
The oracle row is near 1.0, which shows the ground truth is correct.

Recall is low on purpose. The known answer per question is capped at 50 events.
The system only returns the top 10, so recall cannot pass about 0.2.
Raise the cutoffs to compare fairly:

```zsh
.venv/bin/python scripts/evaluate.py --cutoffs 10,50
```

Open questions stay unscored until you add `eval/labels.jsonl` entries.

## Run The Tests

The test suite runs without Elasticsearch or LM Studio.
It uses fakes for the client, the embedding model, and the language model.

```zsh
.venv/bin/python -m pytest
```

## Project Structure

```text
scripts/               Tools: index, ingest, evaluate, test queries
src/stats/             Web app: API, search service, RAG service, config
src/stats/templates/   Web page
src/stats/static/      Web page style and logic
eval/                  Evaluation questions, labels, and reports
tests/                 Test suite with fakes (no live services)
statsbomb-rag-data/    Local match data (not in git)
```

The web app has one class per file:

| File                     | Role                              |
| ------------------------ | --------------------------------- |
| config.py                | Settings from the environment     |
| elasticsearch_provider.py| Elasticsearch client and index    |
| embedding_provider.py    | Turns query text into a vector    |
| llm_provider.py          | Calls the language model          |
| search_service.py        | Keyword and hybrid search         |
| rag_service.py           | Retrieval plus answer generation  |
| app_factory.py           | Builds the FastAPI app and routes |

The evaluation code also has one class per file:

| File                     | Role                              |
| ------------------------ | --------------------------------- |
| eval_case.py             | One evaluation question           |
| intent_filter.py         | Turns a filter into an ES query   |
| gold_set_builder.py      | Builds the known answer set       |
| relevance_judge.py       | Judge protocol                    |
| set_relevance_judge.py   | Judge by id membership            |
| metric_calculator.py     | Precision, recall, F1, nDCG, MRR  |
| eval_result.py           | Score for one question and mode   |
| eval_report.py           | Groups results and averages them  |
| retrieval_evaluator.py   | Runs every question and mode      |
| query_loader.py          | Reads the question set            |
| labels_loader.py         | Reads human labels                |
| report_writer.py         | Writes the markdown and json      |

## Configuration

Copy `.env.example` to `.env` to change settings:

| Variable             | Default                  | Meaning                        |
| -------------------- | ------------------------ | ------------------------------ |
| ELASTICSEARCH_HOST   | http://localhost:9200    | Elasticsearch address          |
| INDEX_NAME           | statsbomb_events         | Index name                     |
| EMBEDDING_MODEL      | google/embeddinggemma-2  | Vector model                   |
| LLM_HOST             | http://localhost:1234/v1 | LM Studio server               |
| LLM_MODEL            | qwen/qwen3-1.7b          | Chat model name                |

## Important Notes

- The search works in English only.
- The location words (for example "attacking third") assume attacks go to +x.
- RAG answers stay grounded in the retrieved events. The model must not invent facts.
- The language model is small. Short, event-worded questions work best.
- Do not commit `statsbomb-rag-data/`. Git ignores this folder.
