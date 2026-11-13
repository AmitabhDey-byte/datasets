# Dataset Generator

A small local web app that turns raw text into structured datasets using a Gemini API key.

Upload a text file, describe the dataset you need, choose the structure, and download JSONL. You can generate question-answer examples, instructions, summaries, classifications, extracted facts, or records with your own fields and types.

## Setup with uv

Requirements:

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.10 or newer; uv can install Python if needed
- Internet access and a [Gemini API key](https://aistudio.google.com/apikey)
- A Gemini model available to your account that supports structured output

In PowerShell:

```powershell
cd D:\datasets_manual
uv sync
uv run uvicorn app:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Keep the terminal running while generating. Press Ctrl+C to stop.

Dependencies are declared in `pyproject.toml`. `uv.lock` records their resolved versions, and `uv sync` installs them into `.venv`. You do not need to activate the environment manually.

If port 8000 is busy, change it to 8001 and open the matching address.

## Gemini key and model

Paste your API key into the password field, or set it for the current PowerShell session before starting the app:

```powershell
$env:GEMINI_API_KEY = "your-key"
uv run uvicorn app:app --host 127.0.0.1 --port 8000
```

A key entered in the UI takes precedence over the environment variable. The UI clears it after starting a job. The backend uses it in memory and does not write it to run files. The app does not load a `.env` file automatically.

Enter the exact model ID shown in your AI Studio account. Model availability changes, so the app leaves the model field editable and requires you to select one. Use the model ID without a `models/` prefix.

Generation sends your requirements, JSON schema and source chunks to Google. API usage follows your Google account's quota and billing. Start with a small record count.

Implementation references: [Gemini content generation](https://ai.google.dev/api/generate-content) and [structured output](https://ai.google.dev/gemini-api/docs/structured-output).

## Generate a dataset

1. Upload a UTF-8 `.txt` or `.md` file, or paste raw text. Loading a file replaces the text box.
2. Describe what the records should contain: task, audience, language, difficulty, answer length, labels and exclusions.
3. Choose chat messages, instruction records, or a custom JSON schema.
4. Set the target number of accepted records, from 1 to 1,000.
5. Enter your API key if it is not set in the environment, and enter a model ID.
6. Click **Generate dataset**.
7. Review the first 10 accepted records and download the JSONL file.

The source is required. Input is limited to 2 million characters. PDF, Word, CSV and JSONL are not parsed as input formats; first extract their text into a UTF-8 text file.

## Writing useful requirements

For question-answer training:

> Create beginner question-answer examples from this installation manual. Use English. Cover setup, configuration and troubleshooting. Keep answers under 80 words and use only facts in the source.

For extraction:

> Extract product records from the source. Include name, price and currency. Do not invent prices. Use null for a missing price, as allowed by my schema.

For classification:

> Select customer feedback from the source and label its sentiment as positive, negative or neutral. Keep the original feedback wording and distribute labels as evenly as the source allows.

Requirements influence generation, but only structural rules in the JSON schema are checked automatically. Label balance, factual accuracy and language quality still require review.

## Output structures

Each line of `dataset.jsonl` is one JSON object. There is no surrounding JSON array.

### Chat messages

```json
{"messages":[{"role":"user","content":"Context: The device uses USB-C power.\n\nHow is the device powered?"},{"role":"assistant","content":"It uses USB-C power."}]}
```

Every accepted record contains exactly one user turn followed by one assistant turn. The prompt asks Gemini to include any source material needed to understand the task.

### Instruction / input / output

```json
{"instruction":"How is the device powered?","input":"The device uses USB-C power.","output":"It uses USB-C power."}
```

All three fields are strings. Instruction and output must be nonempty. Input may be empty when the instruction is self-contained.

### Custom JSON schema

Choose **Custom JSON schema** and describe one record. For example:

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string", "minLength": 1},
    "price": {"type": ["number", "null"]},
    "currency": {"type": "string"},
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["name", "price", "currency", "tags"],
  "additionalProperties": false
}
```

Use `properties` for fields, `required` for mandatory fields, `enum` for allowed labels, and `additionalProperties: false` to reject unexpected fields. Nested objects, arrays, booleans and numbers are supported by the local validator.

The top level must be an object. References such as `$ref` and `$dynamicRef` are not supported. Gemini accepts a subset of JSON Schema; if a schema is rejected by the API, simplify it according to Google's structured output documentation.

## Cleaning and generation

The app:

1. Saves the source text from the text box.
2. Normalizes Unicode, removes null characters, collapses repeated spaces and tabs, and limits repeated blank lines.
3. Splits the cleaned text into roughly 6,000-character chunks with 200 characters of overlap, preferring word boundaries.
4. Sends one chunk per Gemini request and asks for one record.
5. Trims generated strings and validates each record against the selected schema.
6. Rejects invalid responses and duplicate records, ignoring key order and letter case when comparing duplicates.
7. Writes accepted records to disk immediately.

Chunks are used in source order, cycling when more records are requested than there are chunks. If the target is smaller than the number of chunks, later chunks may not be visited. There is no guarantee of complete source coverage.

The target is an accepted-record count, not a promise. The app makes at most twice that many API attempts. A quota, connection or API error stops the run immediately; accepted records remain downloadable. Invalid, incomplete and duplicate responses consume attempts and are skipped.

Statuses:

- `running`: generation is in progress.
- `done`: the requested count was reached.
- `partial`: some records were saved, but the target was not reached.
- `failed`: no records were accepted.

Cleaning does not prove factual correctness, remove personal information or detect semantic duplicates. Indentation in source code may be altered by source whitespace cleanup. Review the output before training.

## Saved files

Each run gets its own folder:

```text
data/
  <job-id>/
    raw.txt
    cleaned.txt
    settings.json
    dataset.jsonl
    report.json
```

- `raw.txt`: source text submitted from the UI, not the original file bytes.
- `cleaned.txt`: normalized source text.
- `settings.json`: requirements, model, target, format and schema, without the API key.
- `dataset.jsonl`: accepted records, including partial results.
- `report.json`: final status, counts and any error.

The `data/` directory is ignored by Git. Job status and preview are held in memory, so restarting the server clears the UI's job history. Saved files remain available on disk. Jobs do not resume after a restart. Run one server process; the app accepts one generation job at a time.

## Project files

```text
app.py               API routes, input validation and job status
core/generator.py    Cleaning, Gemini requests, validation and export
index.html           Browser UI, styling and interactions
pyproject.toml       Project metadata and dependencies
uv.lock              Locked dependencies
fineweb.ipynb        Existing, separate FineWeb exploration notebook
```

The notebook and `cleanded_dataset/` folder are separate from this app. To use FineWeb text here, export the desired passages to a text file.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Missing API key | Enter the key in the UI or set GEMINI_API_KEY before starting. |
| Invalid key or access denied | Check the key and its permissions in AI Studio. |
| Model not found | Copy an available model ID from your account. |
| Request or schema rejected | Use a model with structured output and simplify the custom schema. |
| Quota or rate limit reached | Check your Gemini quota, wait, then start a new smaller run. |
| Connection timed out | Check internet access; each request has a 180-second timeout. |
| Fewer records than requested | Read the report; duplicates, invalid records or API failures can stop completion. |
| Empty or invalid source | Supply nonempty UTF-8 text. |
| Job not found after restart | Open the saved dataset under data/ directly. |

## Local API

- `GET /`: web UI.
- `POST /api/generate`: start a job; returns `job_id`.
- `GET /api/jobs/{job_id}`: progress, counts, preview and error.
- `GET /api/jobs/{job_id}/download`: download accepted records after the run ends.

Interactive request documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The app is intended to run locally on `127.0.0.1`; it has no user accounts or authentication.

