---
name: "portfolio-scraper"
description: "Collects and analyzes public data with Portfolio Scraper and guides adapter development. Invoke when agents handle Bilibili, GitHub, RSS, static HTML, or local text analysis."
---

# Portfolio Scraper

Use this skill to collect public data with the repository CLI, analyze local exports, or add a
source adapter. Prefer existing commands over custom scraping code.

## Boundaries

- Collect only public data the user is authorized to access.
- Do not automate browsers, log in, bypass access controls, or execute page JavaScript.
- Follow platform terms, robots guidance, rate limits, copyright, privacy, and applicable law.
- Ask for clarification when the target, authorization, or intended use is ambiguous.

## Choose a workflow

| Source or goal | Workflow |
| --- | --- |
| Public Bilibili video metadata and XML danmaku | `collect bilibili` |
| Public GitHub repository, issues, or releases | `collect github` |
| Public RSS 2.0 or Atom feed | `collect rss` |
| Repeated elements in static HTML | `collect web` |
| Word counts from local JSONL, CSV, or text | `analyze frequency` |
| PNG visualization from local text fields | `analyze wordcloud` |
| Unsupported public source | Extend `SourceAdapter` test-first |

## Check installation

Run from the repository root:

```bash
env -u PYTHONHOME -u PYTHONPATH uv run --isolated scraper --help
```

Use `uv run --isolated --extra analysis scraper ...` for word-cloud generation. If `uv` is
unavailable, create a Python 3.10+ virtual environment and install `-e ".[dev,analysis]"`.

## Collect public data

Always use placeholders until the user supplies a public target. Add `--request-delay` when a
service needs gentler pacing. Collection output must end in `.jsonl` or `.csv`.

```bash
scraper collect bilibili --bvid <PUBLIC_BVID> --output bilibili.jsonl --request-delay 0.5
scraper collect github --repo <OWNER/REPOSITORY> --resource repository --output repository.jsonl
scraper collect github --repo <OWNER/REPOSITORY> --resource issues --output issues.csv
scraper collect github --repo <OWNER/REPOSITORY> --resource releases --output releases.jsonl
scraper collect rss --url <PUBLIC_FEED_URL> --output feed.jsonl
scraper collect web --url <PUBLIC_PAGE_URL> --item <ITEM_SELECTOR> --title <TITLE_SELECTOR> \
  --content <CONTENT_SELECTOR> --link <LINK_SELECTOR> --output posts.csv
```

All collectors accept `--timeout`, `--retries`, `--request-delay`, `--fail-fast`, and `--debug`.
Omit `--output` only when a count-only run is intended.

## Analyze local data

```bash
scraper analyze frequency records.jsonl --field content --min-length 2 --top 30
scraper analyze frequency records.csv --field title --stopwords stopwords.txt --format json
scraper analyze wordcloud records.jsonl --field content --output wordcloud.png
scraper analyze wordcloud records.csv --font-path <LOCAL_FONT_PATH> --output wordcloud.png
```

Valid analysis fields are `title`, `content`, and `author`. Word clouds require the `analysis`
extra and a discoverable font or explicit `--font-path`.

## Validate output and status

1. Confirm the command summary reports the expected record and failed-item counts.
2. For JSONL, parse every non-empty line as JSON and verify `source`, `id`, and `url`.
3. For CSV, verify the header and inspect representative rows for encoding and selector quality.
4. For word clouds, confirm the PNG exists, is non-empty, and renders the expected language.

Exit code `0` means success. Exit code `2` means records were produced with recoverable
item-level errors. Exit code `1` means a fatal error, or any collected error when `--fail-fast`
is enabled. Do not treat partial results as complete without telling the user.

## Classify errors

- Configuration: invalid output suffix, field, format, selector, path, or source argument.
- Network: timeout, DNS, connection, HTTP status, retry exhaustion, or response-size limit.
- Parsing: malformed remote payload or an upstream schema change.
- Partial collection: inspect warnings and `CollectionResult.errors`; preserve valid records.
- Analysis: unreadable input, missing optional dependencies, missing font, or empty terms.

Retry only transient network failures with bounded retries and delay. Use `--debug` for local
diagnosis, then remove sensitive values from logs before sharing them.

## Safety rules

- Never request, print, embed, or commit passwords, access tokens, session identifiers, cookies,
  authorization headers, private URLs, or copied browser state.
- Pass optional `GITHUB_TOKEN` through the environment or a secret manager; never place its value
  in commands, examples, fixtures, issue text, or commits.
- Keep samples synthetic and use public URLs. Do not weaken TLS, response-size limits, retries,
  throttling, header redaction, or repository hygiene checks.
- Stop rather than circumvent authentication, CAPTCHAs, anti-bot controls, or explicit denials.

## Extend an adapter

1. Start with a failing offline test and compact fixture under `tests/`.
2. Add a module under `src/scraper/adapters/` implementing the `SourceAdapter` protocol with a
   stable `source` value.
3. Reuse `HttpClient` for bounded HTTP behavior; never instantiate an unbounded ad hoc client.
4. Normalize every item to `Record`, put source-specific JSON values in `metadata`, and return a
   `CollectionResult` containing valid records plus recoverable item errors.
5. Convert remote failures to domain exceptions, avoid network access in tests, and register the
   command in `src/scraper/cli.py`.
6. Run the focused test, observe it pass, then run the complete quality gate.

## Complete quality gate

```bash
env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis ruff format --check .
env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis ruff check .
env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis mypy src
env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis pytest -q
```
