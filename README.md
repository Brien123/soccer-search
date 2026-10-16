# statsbomb-search

## Purpose

This project lets you search football match events with words.
You type a question. The system returns the events that match.

Example: type "late goals in the final minutes".
The system returns goals that players scored after minute 85.

## How It Works

The project has four parts:

1. Raw data: StatsBomb match files in JSON format.
2. Scripts: tools that prepare the data and test the search.
3. Search index: Elasticsearch stores text and vectors.
4. Web app: a FastAPI backend and a web page for search.

Data flows in this order:

1. `scripts/create_index.py` makes a clean index in Elasticsearch.
2. `scripts/ingest.py` reads match files and writes one sentence per event.
3. Each sentence gets a vector from an embedding model.
4. Elasticsearch stores the sentence, the vector, and facts (team, player, minute, event type, xG).
5. You send a query to the web app or to the API.
6. Elasticsearch returns the best events.

## Requirements

- Python 3.14
- `uv`
- Docker (for Elasticsearch)
- 1 GB free RAM (for the embedding model)

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

```zsh
.venv/bin/uvicorn stats.main:app --reload --port 8000
```

Open this page in a browser:

```text
http://127.0.0.1:8000/
```

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

## Project Structure

```text
scripts/               Tools: index, ingest, test queries
src/stats/             Web app: API, search service, config
src/stats/templates/   Web page
src/stats/static/      Web page style and logic
statsbomb-rag-data/    Local match data (not in git)
```

## Important Notes

- The search works in English only.
- The location words (for example "attacking third") assume attacks go to +x.
- Vector search (RAG) works in scripts only. The web API uses word search now. The code is ready for vectors later.
- Do not commit `statsbomb-rag-data/`. Git ignores this folder.
- Copy `.env.example` to `.env` to change the Elasticsearch address.
