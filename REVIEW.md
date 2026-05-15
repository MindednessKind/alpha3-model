# Code Review

Review date: 2026-05-15

Update: based on maintainer direction, this wrapper is not intended for
standalone wheel installation. The repo-local upstream loading model is now an
`alpha3-python3` Git submodule pointing at
`https://github.com/MindednessKind/alpha3-python3.git`. Findings about stale
artifacts, NULL-byte bypass, and license metadata were acted on in this
workspace.

Scope:

- Reviewed `src/alpha3/__init__.py`, `src/alpha3/_bridge.py`, `tests/test_api.py`,
  `pyproject.toml`, `setup.py`, `README.md`, `TREE.md`, `NAVIGATION.md`, and the
  retained `dist/alpha3_py-1.0.0-py3-none-any.whl`.
- Performed runnable shellcode validation for wrapper-generated x64 and x86
  payloads with Unicorn.
- Included an independent read-only review from the requested `gpt-5.4`
  subagent and verified the actionable findings locally.

## Findings

### 1. High: Fresh wheel installs but cannot encode outside the repository

- Location: `src/alpha3/_bridge.py:12`, `src/alpha3/_bridge.py:44`,
  `pyproject.toml:16`
- Status: Accepted as out of scope. The current module design is repo-local,
  loads upstream from the `alpha3-python3` submodule, and is not intended for
  standalone wheel installation.
- Description: `ROOT_DIR` is computed as two directories above the installed
  `alpha3` package and `UPSTREAM_DIR` was hard-coded to a repo-local upstream
  path.
  The fresh wheel built from the current source only contains `alpha3/__init__.py`
  and `alpha3/_bridge.py`; it does not include the upstream `ALPHA3.py` or the
  upstream decoder assets. Installing that wheel into a clean venv outside this
  checkout makes `alpha3.build(...)` fail with `FileNotFoundError` for
  repo-local upstream path.
- Fix action: either package the required upstream ALPHA3 files as package data
  and load them relative to the installed package, or explicitly make this
  project repo-local and remove/avoid distributable artifacts that imply
  standalone installation support.
- Verification method: build a fresh wheel, install it in a clean venv outside
  the checkout, then run:

  ```bash
  python - <<'PY'
  import alpha3
  alpha3.build(b"\x90\x90\xcc", arch="amd64", pack="mixedcase", register="rax")
  PY
  ```

  The reviewed workspace reproduced the failure after:

  ```bash
  python3 -m pip wheel . --no-deps --no-build-isolation --wheel-dir /tmp/alpha3-review-dist
  python3 -m venv /tmp/alpha3-review-venv
  /tmp/alpha3-review-venv/bin/python -m pip install --no-index /tmp/alpha3-review-dist/alpha3_py-1.0.0-py3-none-any.whl
  ```

### 2. High: Checked-in wheel does not match the current public API contract

- Location: `dist/alpha3_py-1.0.0-py3-none-any.whl`, `README.md:7`,
  `README.md:109`, `tests/test_api.py:71`
- Status: Fixed. The stale `dist` directory was removed so the old API is no
  longer present as a retained artifact in this workspace.
- Description: source, docs, and tests say the only public API is
  `import alpha3; alpha3.build(...)` and that old entry points are removed. The
  retained wheel still contains old top-level modules and metadata:
  `ALPHA3`, `charsets`, `encode`, `io`, `print_functions`, `x64`, and `x86`.
  Its `alpha3/__init__.py` exports `ALPHA3`, `Alpha3Error`, `encode`, and
  `list_encoders`, which contradicts the current source API.
- Fix action: rebuild or remove the stale `dist` artifact. Add a release check
  that unzips the produced wheel and verifies `top_level.txt`, packaged files,
  and import surface against `tests/test_api.py`.
- Verification method:

  ```bash
  python3 -m zipfile -l dist/alpha3_py-1.0.0-py3-none-any.whl
  python3 -m zipfile -e dist/alpha3_py-1.0.0-py3-none-any.whl /tmp/alpha3-wheel-review
  sed -n '1,120p' /tmp/alpha3-wheel-review/alpha3_py-1.0.0.dist-info/top_level.txt
  sed -n '1,80p' /tmp/alpha3-wheel-review/alpha3/__init__.py
  ```

### 3. Medium: NULL-byte rejection depends on upstream `assert`

- Location: `src/alpha3/_bridge.py:72`
- Status: Fixed. The wrapper now converts to bytes and explicitly raises
  `ValueError("shellcode must be NULL-free")` when input contains `b"\x00"`.
- Description: the README documents that input shellcode must not contain NULL
  bytes, and upstream ALPHA3 enforces that with `assert`. The wrapper does not
  perform its own explicit check before calling upstream. Under normal Python,
  `alpha3.build(b"\x90\x00\xcc", ...)` raises `AssertionError`; under
  `python -O`, asserts are removed and the same invalid input is encoded.
- Fix action: validate `b"\x00" not in shellcode` in the wrapper after converting
  to bytes and raise a stable `ValueError` before calling upstream.
- Verification method:

  ```bash
  PYTHONPATH=src python3 -O - <<'PY'
  import alpha3
  alpha3.build(b"\x90\x00\xcc", arch="amd64", pack="mixedcase", register="rax")
  PY
  ```

  This currently generates output instead of rejecting the invalid input.

### 4. Medium: Packaging metadata points at a missing license file

- Location: `pyproject.toml:11`
- Status: Fixed. `COPYRIGHT.txt` was added at repository root and
  `pyproject.toml` now uses `license = {file = "COPYRIGHT.txt"}`.
- Description: package metadata says `license = {text = "See COPYRIGHT.txt"}`,
  but this wrapper repository has no root `COPYRIGHT.txt`, and the current source
  package does not include `src/alpha3/COPYRIGHT.txt`. The upstream submodule has
  `alpha3-python3/COPYRIGHT.txt`, but that is not packaged in the fresh wheel.
- Fix action: add the referenced license file to this repo and include it in
  release artifacts, or update metadata to accurately describe the wrapper
  license and upstream notice location.
- Verification method: inspect the built wheel metadata and installed package
  contents for the referenced file.

### 5. Medium: Automated tests do not prove decoder execution

- Location: `tests/test_api.py:21`, `tests/test_api.py:32`
- Description: unit tests assert that generated payloads are `bytes` and ASCII
  alphanumeric, but they do not verify that the ALPHA3 decoder runs, restores the
  original payload, transfers control, and executes it. This matters because the
  decoder contract depends on initial register or memory state, not only output
  charset.
- Fix action: add an emulator-based integration test for at least one x64
  register encoder and one x86 register encoder. Keep Windows/Testival-specific
  upstream tests separate.
- Verification method: run a Unicorn harness that generates bytes through
  `alpha3.build(...)`, maps the encoded payload, initializes the required base
  register, verifies decoded memory equals `raw + b"\x00"`, hooks syscalls, and
  asserts expected stdout and exit code.

### 6. Low: Upstream path cleanup removes a caller-provided `sys.path` entry

- Location: `src/alpha3/_bridge.py:16`, `src/alpha3/_bridge.py:21`,
  `src/alpha3/_bridge.py:58`
- Description: `_ensure_upstream_path()` only inserts `UPSTREAM_DIR` if absent,
  but `_remove_upstream_path()` removes every matching entry unconditionally. If
  application code already had `UPSTREAM_DIR` in `sys.path`, loading ALPHA3
  removes that caller-owned path entry.
- Fix action: track whether `_ensure_upstream_path()` inserted the path and only
  remove it when this bridge inserted it. Alternatively snapshot and restore
  `sys.path` around the load.
- Verification method:

  ```bash
  PYTHONPATH=src python3 - <<'PY'
  import sys
  from alpha3._bridge import UPSTREAM_DIR, load_upstream_al3
  load_upstream_al3.cache_clear()
  sys.path.insert(0, UPSTREAM_DIR)
  load_upstream_al3()
  print(UPSTREAM_DIR in sys.path)
  PY
  ```

  This currently prints `False`.

## Shellcode Runtime Check

Runnable checks were performed against wrapper-generated payloads, not the
upstream CLI:

```bash
PYTHONPATH=src python3 - <<'PY'
# Unicorn harness omitted here for brevity; see review transcript.
PY
```

Results:

- x64: `alpha3.build(raw_orw_payload, arch="amd64", pack="mixedcase",
  register="rax")` produced 167 bytes, all ASCII alphanumeric, decoded to
  `raw + b"\x00"`, executed an emulated `open/read/write/exit` payload, printed
  `alpha3 wrapper x64 ok\n`, and exited with code 0.
- x86: `alpha3.build(raw_write_payload, arch="i386", pack="uppercase",
  register="eax")` produced 111 bytes, all uppercase ASCII alphanumeric, decoded
  to `raw + b"\x00"`, executed an emulated `int 0x80` write/exit payload,
  printed `OK!\n`, and exited with code 0.

Command output:

```text
x64: runnable length=167 payload_entry_offset=0x3a sha256=9f5a9171daae70c5544f2545296085a8e76274b4961ea51293a436ca98455dfe
x86: runnable length=111 payload_entry_offset=0x34 sha256=317efdb493dd45e7c3c6e83dfc61da13f06ddc40c60e0fadd4a6ab1313aec3ec
```

## Verification Run

Commands run during review:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 - <<'PY'
import hashlib
import alpha3
payload = alpha3.build(b"\x90\x90\xcc", arch="amd64", pack="mixedcase", register="rax")
print("len=%d sha256=%s prefix=%r alnum=%s" % (
    len(payload), hashlib.sha256(payload).hexdigest(), payload[:16], payload.isalnum()))
PY
```

Observed:

```text
Ran 6 tests in 0.008s
OK
len=67 sha256=d1bac6627042ab7ed56c1e66560f87185d9f5a1b333628bb40db8b46582e2511 prefix=b'Ph0666TY1131Xh33' alnum=True
```

Build note: `python3 -m build --wheel` was unavailable because the `build`
module is not installed. `pip wheel` with build isolation attempted to download
`setuptools>=61` and failed due restricted network/DNS. The fresh wheel check was
completed with `python3 -m pip wheel . --no-deps --no-build-isolation`.
