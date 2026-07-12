# tibanna_ff — agent guide

Fourfront-portal-specific extensions of the external [`tibanna`](https://github.com/4dn-dcic/tibanna)
PyPI package ("Unicorn", the portal-agnostic engine). This repo adds portal (get/post/patch metadata)
integration for the 4DN, CGAP, and SMaHT data portals. `ff` = *fourfront*, **not** Foursight.

Authoritative docs: https://tibanna-ff.readthedocs.io/en/latest (source in `docs/`, esp.
`docs/overview.rst` for code structure and `docs/behavior.rst` for expected run behavior). This file
records the durable facts and sharp edges those docs miss (notably SMaHT/tiger, which `overview.rst`
predates) — prefer pointing to the docs/code over duplicating them.

## Layout: one shared base + three portal variants

Naming convention (animal codenames — used everywhere in code, tests, and deployed resource names):

| Package           | Codename  | Portal | `LAMBDA_TYPE`/`SFN_TYPE` | CLI            | `vars.py` DEV/PROD env      |
|-------------------|-----------|--------|--------------------------|----------------|-----------------------------|
| `tibanna_ffcommon`| —         | shared base, library-only (no CLI) | — | —      | —                           |
| `tibanna_4dn`     | **pony**  | 4DN    | `pony`                   | `tibanna_4dn`  | `webdev` / `data`           |
| `tibanna_cgap`    | **zebra** | CGAP   | `zebra`                  | `tibanna_cgap` | `cgapwolf` / `cgap`         |
| `tibanna_smaht`   | **tiger** | SMaHT  | `tiger`                  | `tibanna_smaht`| `smaht-wolf` / `smaht-production` |

There is no "cheetah". Default step function name per variant is `'tibanna_' + LAMBDA_TYPE`
(e.g. `tibanna_pony`). CLI entry points are declared in `pyproject.toml` `[tool.poetry.scripts]` →
`<pkg>/__main__.py:main`.

### Inheritance pattern (the key architecture fact)

`tibanna` (Unicorn, external) → `tibanna_ffcommon` `*Abstract` classes → concrete per-variant subclasses.
- **Shared abstract logic** lives in `tibanna_ffcommon/portal_utils.py`: `FFInputAbstract`,
  `FourfrontStarterAbstract`, `FourfrontUpdaterAbstract`, `ProcessedFileMetadataAbstract`,
  `QualityMetricsGenericMetadataAbstract` (also `WorkflowRunMetadataAbstract` in `wfr.py`).
- **Env-specific concrete impls** live in `<pkg>/{pony,zebra,tiger}_utils.py` (`FourfrontStarter`,
  `FourfrontUpdater`, `FFInput`, `ProcessedFileMetadata`, …). This is where portal-specific business
  logic goes. SMaHT/tiger uses consortium + submission-center attribution instead of 4DN's lab/award.
- **Env identity/config** lives in `<pkg>/vars.py` (each starts `from tibanna_ffcommon.vars import *`).
  Change shared metadata behavior in `ffcommon/portal_utils.py`; change env identity in `<pkg>/vars.py`.

## Workflow & check data flow

A run is a Step Function of Lambdas. Beyond Unicorn's `run_task` + `check_task`, each variant adds
`start_run` and `update_ffmeta` (see `docs/overview.rst`). Lambda source is in `<pkg>/lambdas/`
(`start_run.py`, `run_task.py`, `check_task.py`, `update_ffmeta.py`, `update_cost.py`); the thin
handlers delegate to `<pkg>/start_run.py`, `<pkg>/update_ffmeta.py`, etc. Lambda *names* are defined
in `tibanna_ffcommon/vars.py` (`RUN_TASK_LAMBDA_NAME`, `CHECK_TASK_LAMBDA_NAME`, …); the `.py`
filenames omit the codename suffix but deployed Lambdas always carry it.

Flow: `start_run` (build `FourfrontStarter`, resolve input files + job JSON) → `run_task` (launch
AWSEM EC2) → `check_task` (poll until done) → `update_ffmeta` (`FourfrontUpdater`: register output
files, QC, and patch portal metadata / handle errors). `update_cost` runs on a separate cost-updater
step function (`<pkg>/stepfunction_cost_updater.py`). Job Description JSON schema: `docs/execution_json.rst`.

QC pipeline: `ffcommon/qc.py` (QC workflow-argument models), `ffcommon/generic_qc_utils.py` (pydantic
threshold/ruleset pass-warn-fail evaluation), `ffcommon/misc_utils.py` (`LogicalExpressionParser` for
and/or/not ruleset strings). SMaHT generic-QC specifics: `docs/qc_smaht.rst`.

## Key shared modules (`tibanna_ffcommon/`)

`core.py` (programmatic `API`), `vars.py` (config constants, bucket-name helpers, lambda names),
`portal_utils.py` (portal abstraction — the big one), `wfr.py` (workflow-run metadata),
`stepfunction.py` (SFN definitions + retry conditions), `iam_utils.py` (IAM roles/policies),
`input_files.py` / `extra_files.py` / `file_format.py` (file resolution & format↔extension maps),
`config.py` (HiGlass config), `exceptions.py`.

## Build / test / lint commands

Poetry-managed, Python `>=3.8,<3.12`. See `Makefile` and `tasks.py` (invoke tasks).
- Install: `make install` (or `make build`). Lint: `flake8 .` / `make lint` (config `.flake8`, max line 120).
- Unit tests: `make test` (= `pytest -vv ./tests/tibanna`) or `poetry run invoke test`. Rerun failures: `make retest`.
- CI-equivalent: `poetry run invoke test --no-flake --no-post`. Single: `pytest tests/tibanna/pony/test_pony_utils.py`.
- pytest config in `pyproject.toml` (`--cov-fail-under 2`). Coverage scoped to the four packages.

## Test layout (`tests/`, `test_json/`)

- `tests/tibanna/{pony,zebra,smaht,ffcommon}/` — unit tests mirroring the variant split; event-JSON
  fixtures under per-lambda subdirs (`start_run/`, `check_task/`, …). Small sample data in `tests/files/`.
- `*_post.py` (`tests/tibanna/{pony,zebra}/test_*_utils_post.py`) — POST real items to dev portals /
  S3; **skipped in CI** via `invoke test --no-post`. The zebra one is currently `pytest.mark.skip`.
- `tests/post_deployment/` — integration tests that **spin up real AWSEM EC2 (costs money)** against
  dev step functions (`tibanna_pony_pre`, `DEV_SUFFIX='pre'`); run via
  `poetry run invoke test --deployment --subnets <id> --security-groups <id>`. Job-description inputs
  in `test_json/{pony,zebra}/` (`pony_archive/` is a historical archive).

## CI / deploy (`.github/workflows/`)

GitHub Actions, ubuntu-22.04, Python 3.11, Poetry 1.3.2. **Workflows key on branch `master`**
(not this checkout's default branch). `main.yml` (CI) runs on push/PR to `master`. Others are
`workflow_dispatch` (manual): `main-run-tests.yml` (post-deployment path), `main-deploy-pony-{data,webdev}.yml`
(`tibanna_4dn deploy_pony`), `main-publish.yml` (PyPI, on tag push), `main-deploy-docs.yml` (ReadTheDocs).
No zebra/smaht deploy workflows exist. Prod deploy details + required env vars: `docs/production.rst`,
`docs/permissions.rst`.

## Sharp edges

- **`GLOBAL_ENV_BUCKET` must be set in the environment** or importing `tibanna_ffcommon.vars` raises at
  import time (fails collection of nearly all tests). CI passes it as a secret. Also expects
  `S3_ENCRYPT_KEY`. This is why local test runs need these env vars, not just AWS creds.
- **Secure AMI region gate**: `ffcommon/vars.py` `AMI_PER_REGION` only lists `us-east-1`/`us-east-2`;
  importing in an unsupported `AWS_REGION` raises. Adding a region means replicating the AMI + editing this map.
- Single version string for all four packages (`tibanna_ffcommon/_version.py`); `AWSF_IMAGE` ECR tag is
  derived from the base `tibanna` version.
- `docs/tests.rst` mentions Travis — stale; actual CI is GitHub Actions.
- `CheckTask`/`cw_utils.py` (CloudWatch `TibannaResource`) exist only in cgap & smaht; 4dn inherits Unicorn's.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
