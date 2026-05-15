#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
UPSTREAM_DIR = ROOT_DIR / "alpha3-python3"


def main(argv=None) -> int:
  parser = argparse.ArgumentParser(
      description="Deploy the local alpha3 wrapper with its upstream submodule.")
  parser.add_argument(
      "--no-submodule",
      action="store_true",
      help="Skip git submodule initialization/update.")
  parser.add_argument(
      "--no-install",
      action="store_true",
      help="Skip pip editable installation.")
  parser.add_argument(
      "--no-smoke",
      action="store_true",
      help="Skip the post-install import and build smoke test.")
  parser.add_argument(
      "--build-isolation",
      action="store_true",
      help="Let pip create an isolated build environment.")
  parser.add_argument(
      "--user",
      action="store_true",
      help="Pass --user to pip install.")
  parser.add_argument(
      "--python",
      default=sys.executable,
      help="Python executable used for pip and smoke test.")
  args = parser.parse_args(argv)

  _require_supported_python(args.python)
  _ensure_project_root()

  if not args.no_submodule:
    _update_submodules()
  _ensure_upstream_ready()

  if not args.no_install:
    _install_editable(args.python, args.user, args.build_isolation)

  if not args.no_smoke:
    _smoke_test(args.python, use_source_path=args.no_install)

  print("alpha3 deploy complete")
  return 0


def _require_supported_python(python: str) -> None:
  script = "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)"
  result = subprocess.run(
      [python, "-c", script],
      cwd=str(ROOT_DIR),
      check=False,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  if result.returncode != 0:
    raise SystemExit("Python 3.8 or newer is required: %s" % python)


def _ensure_project_root() -> None:
  required = [
      ROOT_DIR / "pyproject.toml",
      ROOT_DIR / "src" / "alpha3" / "__init__.py",
  ]
  missing = [str(path) for path in required if not path.exists()]
  if missing:
    raise SystemExit("deploy.py must run from this repository: %s" % missing)


def _update_submodules() -> None:
  if not (ROOT_DIR / ".git").exists():
    print("Skipping submodule update: .git directory not found")
    return
  if not (ROOT_DIR / ".gitmodules").exists():
    print("Skipping submodule update: .gitmodules not found")
    return
  _run(["git", "submodule", "update", "--init", "--recursive"])


def _ensure_upstream_ready() -> None:
  alpha3_py = UPSTREAM_DIR / "ALPHA3.py"
  if not alpha3_py.is_file():
    raise SystemExit(
        "Missing upstream ALPHA3.py. Run `git submodule update --init --recursive`.")


def _install_editable(python: str, user: bool, build_isolation: bool) -> None:
  command = [python, "-m", "pip", "install"]
  if user:
    command.append("--user")
  command.extend(["-e", "."])
  if not build_isolation and _has_setuptools_backend(python):
    command.append("--no-build-isolation")
  _run(command)


def _smoke_test(python: str, use_source_path: bool) -> None:
  script = (
      "import alpha3\n"
      "payload = alpha3.build("
      "b'\\x90\\x90\\xcc', arch='amd64', pack='mixedcase', register='rax')\n"
      "assert isinstance(payload, bytes) and payload\n"
      "print(payload[:8])\n"
  )
  env = _clean_env()
  if use_source_path:
    env["PYTHONPATH"] = str(ROOT_DIR / "src")
  _run([python, "-c", script], env=env)


def _run(command, env=None) -> None:
  print("$ %s" % " ".join(command), flush=True)
  subprocess.run(
      command,
      cwd=str(ROOT_DIR),
      check=True,
      env=env if env is not None else _clean_env(),
  )


def _has_setuptools_backend(python: str) -> bool:
  script = (
      "import re, sys\n"
      "from importlib.metadata import version\n"
      "try:\n"
      "  raw = version('setuptools')\n"
      "except Exception:\n"
      "  raise SystemExit(1)\n"
      "parts = []\n"
      "for chunk in raw.replace('-', '.').split('.'):\n"
      "  match = re.match(r'\\d+', chunk)\n"
      "  if match is None:\n"
      "    break\n"
      "  parts.append(int(match.group(0)))\n"
      "raise SystemExit(0 if tuple(parts) >= (61,) else 1)\n"
  )
  result = subprocess.run(
      [python, "-c", script],
      cwd=str(ROOT_DIR),
      env=_clean_env(),
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      check=False,
  )
  return result.returncode == 0


def _clean_env():
  env = os.environ.copy()
  env.pop("PYTHONPATH", None)
  return env


if __name__ == "__main__":
  raise SystemExit(main())
