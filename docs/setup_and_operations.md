# Setup and operations

[← Back to README](../README.md)

## Getting started

**Requirements:** a recent Python 3, a Gemini API key, and about 2 GB of disk for the virtual environment and downloaded models. Developed on macOS (Apple Silicon).

```
git clone https://github.com/d4t4forge-debugX/regpulse.git
cd regpulse
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and fill in your keys:

```
GEMINI_API_KEY=your-gemini-api-key-here
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key-here
LANGSMITH_PROJECT=regpulse
SEC_CONTACT_EMAIL=you@example.com
```

LangSmith is optional tracing; set `LANGSMITH_TRACING=false` to skip it. `SEC_CONTACT_EMAIL` goes into the User-Agent header that SEC EDGAR requires.

Build the vector store **once**. It reads the Risk Factors text file named in `config.py`, so that file must stay in the project root:

```
python -m vectorstore.chroma_store
```

Do not run this again on an existing collection: it adds chunks with fixed IDs rather than replacing them. To point RegPulse at another company, set its values in `config.py` and use a new collection name.

The first run downloads the Hugging Face models (the zero-shot model is over 1 GB), so it takes a while.

**Optional:** the ColQwen2 visual-retrieval experiment needs extra packages: `pip install -r requirements-colpali.txt`, then `playwright install chromium`. The main pipeline, dashboard and evaluations do not need them.

## Running

Run everything from the project root, as modules.

```
./scripts/run_pipeline.sh            # full pipeline: fetch, then graph
python -m pipeline.run_graph         # graph only; skips documents already processed
python -m pipeline.run_graph --all   # reprocess every document
streamlit run app/streamlit_app.py   # dashboard, with approve/reject buttons
```

Each pipeline run writes a timestamped log to `logs/`. The pipeline is safe to re-run: it merges new documents into the existing files and skips work already done.

Add specific documents by number (for example to label a new gold-set case):

```
python -m ingestion.refresh_documents 2024-25088 2023-20333
```

## Scheduling

cron runs the pipeline on weekdays at 11:30:

```
30 11 * * 1-5 /path/to/Regpulse/scripts/run_pipeline.sh >> /path/to/Regpulse/logs/cron.log 2>&1
```

Add it with `crontab -e`, using your real absolute paths. Weekdays only, because the Federal Register publishes on weekdays.

- `run_pipeline.sh` calls `.venv/bin/python` by path and does its own `cd`, because cron does not load your shell startup files.
- `>> logs/cron.log 2>&1` captures launch errors (bad path, permissions) that the pipeline's own logs cannot.
- On macOS, a project under `~/Desktop` needs Full Disk Access granted to `/usr/sbin/cron`, or the job fails with "Operation not permitted".
- **cron does not run while the machine is asleep or shut down, and it does not catch up afterwards.**
- When a run adds a new rule, the data files change. Commit them as a `Data:` commit, since CI evaluates the committed files.

To check a run afterwards:

```
ls -t logs | head -3 && cat logs/cron.log
```

A healthy run leaves a `pipeline_<date>_11-30-...` log and an empty `cron.log`.

## Cost

A normal scheduled run makes **0 Gemini calls**: it skips every document already processed. A new real rule costs one call to judge it, plus one to write a memo if it is covered or uncovered. A not-applicable rule costs only the judge call.

The Gemini free tier proved too small for this project (about 20 requests per day per model, with per-minute limits as well), so it runs on a billed account. Everything else, including embeddings, the vector store and zero-shot tagging, runs locally for free.

## How this would run in production

Each local piece maps onto a managed equivalent:

| Here | In production | Why it maps cleanly |
|---|---|---|
| Gemini API, `pipeline/gemini_client.py` | AWS Bedrock or Azure OpenAI | Every model call goes through one client with retry and backoff, so the provider changes in one file |
| Local Chroma collection | A managed vector store (for example pgvector or OpenSearch) | Retrieval is one function, `query_collection`, called with a query and a count |
| cron on a Mac | A scheduled cloud job | The job is one script, `scripts/run_pipeline.sh`: fetch, then the graph |
| JSON files keyed by `document_number` | A database table with that key | Every save already merges by key and is safe to re-run |
| Streamlit on localhost | An internal web app behind single sign-on | The dashboard only reads `graph_results.json` and writes `review_decisions.json` |
| LangSmith tracing | Stays | Each regulation's run is already traced node by node |
| GitHub Actions evals | Stays, plus a scheduled `--rerun` against the live model | Catches model or prompt drift, not only code changes |
