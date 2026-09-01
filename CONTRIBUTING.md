# Contributing

Thank you for improving Portfolio Scraper. Keep changes focused, testable, and safe for
people who run the CLI against public services.

## Development setup

Python 3.10 or newer is required.

```bash
git clone <repository-url>
cd Scraper
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,analysis]"
```

Run the same checks used by CI before opening a pull request:

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov=scraper --cov-report=term-missing
python -m build
```

## Branches and commits

Create a topic branch from the current default branch. Prefer small commits that each leave
the tests passing. Conventional commit subjects such as `feat:`, `fix:`, `test:`, `docs:`,
and `build:` make the history easier to review. Do not rewrite shared branch history.

## Test-driven changes

For behavior changes, first add a focused failing test, run it to confirm the expected
failure, implement the smallest complete behavior, and rerun both the focused tests and the
full suite. Network access is prohibited in unit tests; use fixture files or `pytest-httpx`.

## Adding an adapter

An adapter belongs in `src/scraper/adapters/`, defines a stable `source` name, and returns a
`CollectionResult` containing normalized `Record` instances. Keep service-specific fields
inside `Record.metadata`. Use `HttpClient` rather than calling `httpx` directly so timeout,
retry, size, and error behavior remains consistent.

Cover at least:

- successful parsing from a compact, deterministic fixture;
- empty or missing optional fields;
- invalid configuration;
- malformed remote content and service-specific error responses;
- authentication behavior, when the service supports an optional token.

Fixtures belong in `tests/fixtures/`. Remove personal data and keep only the smallest payload
needed for the test.

## Credentials and responsible use

Never commit cookies, session IDs, API keys, access tokens, `.env` files, or captured private
responses. Use environment variables and document only placeholder values. The repository
hygiene test blocks known Bilibili session fields, but it does not replace review or secret
scanning.

Adapters must use public APIs or static public pages. Respect service terms, robots guidance,
rate limits, and applicable law. Do not add login automation, CAPTCHA bypasses, or controls
intended to evade access restrictions.
