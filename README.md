# Duke–ISCVID Infective Endocarditis Criteria

An educational reference implementation of the **2023 Duke–International Society for Cardiovascular Infectious Diseases (Duke–ISCVID)** classification rules. The primary workflows are a static browser checklist, a zero-dependency Python CLI, CSV batch classification and a local FastAPI endpoint.

**Clinical limitation:** The tool only combines criterion domains that a qualified user has already adjudicated. It **does not interpret cultures, images, molecular studies, or pathology**, and is not validated as a medical device. Incomplete investigations must not be entered as negative findings. A “Rejected” result based on insufficient criteria does **not** exclude endocarditis. Refer to the original publication and clinical judgment.

## Main features

- Explicit pathologic and 3 major / 7 minor clinical criterion domains, including the 2023 surgical, imaging and examination updates
- Definite, Possible or Rejected classification from published combinations, with counts and a reason
- Validation against conflicting or double-counted categories
- Local-only, dependency-free browser form with JSON export
- Python single-case and CSV batch workflows; optional FastAPI interface

## Browser application

The app lives in `web/index.html` and uses `web/app.mjs`. Open it through a local HTTP server:

```bash
python -m http.server 8080 --directory web
```

Visit `http://localhost:8080/`. It is designed for deployment to GitHub Pages from the `web/` directory; live deployment should be independently verified before sharing a link. Desktop and mobile browsers supporting modern JavaScript modules are required.

**Privacy:** Browser criterion selections are processed locally; no data are sent to an API or browser storage. JSON export downloads to the user's device. Do not enter patient identifiers. The optional server and legacy audit utilities are separate and **are not HIPAA-compliance or de-identification guarantees**.

## Python usage

Python 3.10 or newer is required for the core classifier, with no third-party dependencies.

```bash
python duke_endocarditis.py single --major-microbiologic --major-imaging
python duke_endocarditis.py single --major-imaging --minor-fever
python duke_endocarditis.py batch -i sample.csv -o results.csv
```

The `single` command interprets every omitted flag as **reviewed and absent**, not unknown; use only after reviewing all 14 domains. CSV input requires each of the 14 named columns with `true` or `false` values. See `sample.csv` for examples. Batch files are limited to 5 MB/10,000 records and output is escaped to prevent spreadsheet formula execution in free-text fields.

## Optional API and legacy utilities

```bash
python -m pip install -r requirements.txt
python cli.py serve --host 127.0.0.1 --port 8000
```

The same browser UI is served at `http://127.0.0.1:8000/`. `POST /api/classify` accepts an object with the 14 required boolean fields; responses provide the category, criterion counts and basis. Input violations return HTTP 422.

The older `cli.py audit`, `cli.py batch`, `cli.py chat`, `agents/`, `enrichment.py` and `simulator.py` are retained as **experimental legacy utilities**. Their numerical thresholds, mock chat and worker alerts **are not Duke criteria or medical advice**. They should not be used to classify infective endocarditis.

## Tests

```bash
python -m pip install -r requirements.txt
python -m pytest -q
node --test tests/duke_web.test.mjs
node --check web/app.mjs
```

Continuous integration checks Python 3.10–3.13 and Node.js 22. The browser classifier uses JavaScript, **not in-browser Python**; this avoids a heavyweight Pyodide runtime for a small deterministic ruleset.

## Criteria and evidence

Fowler VG Jr, Durack DT, Selton-Suty C, et al. *The 2023 Duke-International Society for Cardiovascular Infectious Diseases Criteria for Infective Endocarditis: Updating the Modified Duke Criteria.* Clin Infect Dis. 2023;77(4):518–526. [doi:10.1093/cid/ciad271](https://doi.org/10.1093/cid/ciad271).

Li JS, Sexton DJ, Mick N, et al. *Proposed modifications to the Duke criteria for the diagnosis of infective endocarditis.* Clin Infect Dis. 2000;30(4):633–638. [doi:10.1086/313753](https://doi.org/10.1086/313753). The original Modified Duke criteria and the 2023 revision have different definitions; this repository's primary classifier uses the **2023** version.

## License

MIT; see [LICENSE](LICENSE).
