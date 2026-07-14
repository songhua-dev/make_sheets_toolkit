# make_sheets_toolkit

A toolkit demonstrating three different integration patterns for connecting Python automation logic to Google Sheets and Make.com/n8n workflows — built to show how the same data-cleaning logic can be wired into a no-code automation platform in three distinct ways, and the trade-offs between them.

## Why this exists

Many real-world automation jobs involve a client who already has a no-code workflow (Make.com, n8n, Zapier) set up, but hits a wall when the built-in modules can't handle custom logic — data cleaning, validation, or conditional processing that the platform's native blocks don't support. This project simulates that exact situation: a "dirty" dataset (~240 rows, sourced from a production forklift-dealer scraping project) needs to be cleaned before it's usable, and three different architectures are used to solve it.

All three approaches share a single source of truth for the cleaning logic (`shared/clean_data.py`), proving the logic itself is portable and platform-agnostic — only the integration layer changes.

## The three integration patterns

| Pattern | How it works | Best fit for |
|---|---|---|
| **Make.com Webhook** (`process_endpoint_main.py`) | Make.com reads raw rows from Google Sheets, batches them, and calls a FastAPI `/process` endpoint over HTTP. The cleaned result is written back to a new sheet and a summary email is sent — all orchestrated by Make.com. | Clients already using Make.com who need one custom step it can't do natively, without touching their existing workflow's other logic. |
| **Python + OAuth (direct)** (`python_oauth_main.py`, `google_sheets_client.py`) | A standalone Python script authenticates directly against the Google Sheets API and performs the full read → clean → write cycle with no automation platform involved. | Clients who want a self-contained script or scheduled job (cron, Cloud Function) with no dependency on a third-party automation subscription. |
| **n8n Code Node** (`n8n_workflow/`) | The same cleaning logic is ported into n8n's built-in Code Node (Python mode), so the entire pipeline runs inside n8n with no external service to host or maintain. | Clients who prefer a single self-hosted or all-in-one platform and don't want to manage a separate API server. |

## Repository structure

```
make_sheets_toolkit/
├── shared/
│   └── clean_data.py           # Single source of truth for the cleaning logic
├── process_endpoint_main.py               # FastAPI endpoint, called by Make.com
├── python_oauth_main.py          # Standalone direct-to-Sheets script
├── google_sheets_client.py       # OAuth authentication helper for gspread
├── make_scenario/
│   ├── blueprint.json            # Exported Make.com scenario
│   └── screenshot.png
├── n8n_workflow/
│   ├── workflow.json             # Exported n8n workflow
│   └── screenshot.png
├── assets/
│   └── before_after_cleaning.png # Visual proof of the cleaning result
├── .env.example
├── .gitignore
└── README.md
```

## The cleaning logic

`shared/clean_data.py` takes a list of raw row dictionaries and applies a strict validation pass:

- Rejects rows with a missing or blank `Product Name`
- Rejects rows where `Price` is blank or literally `"CALL FOR PRICE"`
- Rejects rows with a missing `Company`, `Tel`, or `Location`
- Normalizes `Product Name` to lowercase

Everything that fails validation is counted, not silently dropped — the function returns a structured summary (`total_processed`, `success_count`, `incomplete_count`) alongside the cleaned rows, so every consumer (Make.com, the Python script, n8n) can report on data quality, not just move data around.

## Results

Below is a before/after comparison on a real run against the sample dataset:

![Before and after cleaning](assets/before_after_cleaning.png)

| Platform | Total processed | Success | Incomplete |
|---|---|---|---|
| Python (direct OAuth) | 239 | 73 | 166 |
| n8n | 239 | 73 | 166 |
| Make.com | 239 | 71 | 168 |

Python and n8n — two independently built implementations against the same source data — agree exactly. The Make.com run was captured during an earlier debugging pass, before a Google Sheets range misconfiguration (see Technical Notes below) was corrected; the discrepancy is consistent with the header row being included in that run rather than a logic difference.

## Setup

### 1. Make.com webhook (`process_endpoint_main.py`)

```bash
pip install fastapi uvicorn
uvicorn process_endpoint_main:app --reload
```

Expose it publicly for Make.com to reach during development with a tunneling tool (e.g. ngrok), then point Make.com's HTTP module at `https://<your-tunnel-url>/process`. The full scenario is importable from `make_scenario/blueprint.json`.

### 2. Python direct (`python_oauth_main.py`)

```bash
pip install gspread google-auth-oauthlib google-auth-httplib2 python-dotenv
```

1. In Google Cloud Console, create an OAuth 2.0 Client ID (type: Desktop app) and download the credentials JSON.
2. Copy `.env.example` to `.env` and fill in `GOOGLE_CREDENTIALS_PATH` and `SPREADSHEET_NAME`.
3. Run `python python_oauth_main.py`. The first run opens a browser window for one-time Google account authorization; subsequent runs reuse the cached token.

### 3. n8n (`n8n_workflow/`)

Import `n8n_workflow/workflow.json` into an n8n instance, connect your own Google Sheets and Gmail credentials (these are never included in the exported file), and run.

## Technical notes / known limitations

A record of the non-obvious platform behaviors encountered while building this, kept here because most of them aren't well documented elsewhere:

- **Make.com Array Aggregator (Custom target structure) does not support custom field naming.** When the source module is used as the field template, aggregated fields are keyed by index (`"0"`, `"1"`, `"2"`...) rather than by their original column name, and this appears to be a hard platform limitation, not a configuration option — confirmed by testing both the collapsed field list and the Headers/Query Parameters target structures. Worked around by mapping indices to field names in the FastAPI layer (`FIELD_MAP`) rather than in Make.com.
- **Make.com's JSON string body input does not automatically wrap aggregated arrays in `[ ]`.** The Array Aggregator's output variable needs to be manually bracketed (`[{{array}}]`) in the HTTP module's body field, or the resulting body is a comma-separated sequence of objects with no enclosing array — which fails JSON parsing with a "non-whitespace character after JSON" error.
- **Google Sheets' "Table contains headers" option only affects field labeling in the Make.com editor UI** — it does not exclude the header row from the actual data range. The header row must be excluded explicitly via the range itself (e.g. `A2:E300` instead of `A1:E300`).
- **Make.com's Add a Row module can only select from sheets that existed before the scenario started running** — a sheet created earlier in the same execution (via Add a Sheet) is not available in its dropdown. There's no way to reference it dynamically; the practical workaround is creating the target sheet once, manually, ahead of time.
- **New Google Cloud projects may default into an organization with `iam.disableServiceAccountKeyCreation` enforced** (part of Google's "secure by default" rollout for newly created projects), which blocks downloading a service account JSON key even for a personal Gmail account with no prior organizational structure. OAuth 2.0 (user consent flow) was used instead for this project's direct-Sheets script, since it isn't affected by this policy — with the trade-off that it requires one-time interactive browser login rather than being fully unattended.
- **n8n's Python-mode Code Node uses `_items` (not `items` or `_input`) as the variable exposing incoming data** in this environment/version — undocumented in the example snippets, found through trial and error.
- **n8n Cloud's Python Code Node cannot import any packages, standard library or third-party** (it runs on Pyodide/WASM). This project's cleaning logic only uses built-in string/dict operations, so it was portable without modification — a constraint worth checking before assuming any existing Python logic can move to n8n as-is.

## Security notes

OAuth client secrets, tokens, and `.env` files are excluded via `.gitignore` and are not present in this repository. Exported Make.com and n8n workflow files do not contain credential secrets (both platforms exclude these by design), but were reviewed before publishing to ensure credential *names* didn't reveal any personal account information.