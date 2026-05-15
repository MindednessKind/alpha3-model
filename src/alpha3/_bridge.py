from __future__ import annotations

import importlib.util
import os
import re
import sys
from functools import lru_cache
from types import ModuleType
from typing import Dict, Iterable, List, Optional


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPSTREAM_DIR = os.path.join(ROOT_DIR, "alpha3-python3")
COUNT_SLIDE_RM32_PATTERN = re.compile(
    r"^(countslide:)(?P<register>EAX|EBX|ECX|EDX|ESI|EDI)(?P<tail>\+.*)$",
    re.IGNORECASE,
)


def _ensure_upstream_path() -> None:
  if UPSTREAM_DIR not in sys.path:
    sys.path.insert(0, UPSTREAM_DIR)


def _remove_upstream_path() -> None:
  sys.path[:] = [path for path in sys.path if path != UPSTREAM_DIR]


@lru_cache(maxsize=None)
def load_upstream_al3() -> ModuleType:
  _ensure_upstream_path()
  shadowed_names = [
      "ALPHA3",
      "charsets",
      "encode",
      "print_functions",
      "x86",
      "x64",
  ]
  sentinel = object()
  saved_modules = {
      name: sys.modules.get(name, sentinel)
      for name in shadowed_names
  }
  for name in shadowed_names:
    sys.modules.pop(name, None)

  file_path = os.path.join(UPSTREAM_DIR, "ALPHA3.py")
  spec = importlib.util.spec_from_file_location("ALPHA3", file_path)
  if spec is None or spec.loader is None:
    raise ImportError("Unable to load upstream ALPHA3 from %s" % file_path)
  module = importlib.util.module_from_spec(spec)
  sys.modules["ALPHA3"] = module
  try:
    spec.loader.exec_module(module)
  finally:
    for name, saved in saved_modules.items():
      if saved is sentinel:
        sys.modules.pop(name, None)
      else:
        sys.modules[name] = saved
    _remove_upstream_path()
  return module


def encode_shellcode(
    shellcode: bytes,
    architecture: str = "x86",
    encoding: str = "ascii",
    case: str = "mixedcase",
    base_address: Optional[str] = None,
) -> bytes:
  upstream = load_upstream_al3()
  if isinstance(shellcode, str):
    raise TypeError("shellcode must be bytes-like, not str")
  shellcode_bytes = bytes(shellcode)
  if b"\x00" in shellcode_bytes:
    raise ValueError("shellcode must be NULL-free")
  shellcode_text = shellcode_bytes.decode("latin-1")
  matches = list(_matching_encoders(
      upstream, architecture, encoding, case, base_address))
  if not matches:
    raise ValueError("No encoder exists for the given settings.")
  if len(matches) > 1:
    names = ", ".join(encoder["name"] for encoder in matches)
    raise ValueError(
        "Multiple encoders match; provide register: %s" % names)

  encoder_settings = matches[0]
  upstream_base_address = _upstream_base_address(
      encoder_settings, base_address)
  encoded_shellcode = encoder_settings["function"](
      upstream_base_address, shellcode_text)
  errors = _check_encoded_shellcode(upstream, encoded_shellcode, encoder_settings)
  if errors:
    raise ValueError(
        "Encoded shellcode contains bad characters:\n%s" % "\n".join(errors))
  return encoded_shellcode.encode("latin-1")


def _matching_encoders(
    upstream: ModuleType,
    architecture: str,
    encoding: str,
    case: str,
    base_address: Optional[str],
) -> Iterable[Dict[str, object]]:
  for encoder in _all_encoders(upstream):
    if encoder["architecture"] != architecture:
      continue
    if encoder["character encoding"] != encoding:
      continue
    if encoder["case"] != case:
      continue
    if base_address is not None and not _base_address_matches(
        encoder["base address"], base_address):
      continue
    yield encoder


def _all_encoders(upstream: ModuleType) -> List[Dict[str, object]]:
  return list(upstream.x86.encoders) + list(upstream.x64.encoders)


def _base_address_matches(pattern: str, base_address: str) -> bool:
  if re.match(pattern, base_address, re.IGNORECASE):
    return True
  if "%s" not in pattern:
    return False
  expanded_pattern = pattern % "[A-Z]+"
  return re.match(expanded_pattern, base_address, re.IGNORECASE) is not None


def _upstream_base_address(
    encoder_settings: Dict[str, object],
    base_address: Optional[str],
) -> Optional[str]:
  if base_address is None:
    return None
  if encoder_settings["name"] != "AscMix Countslide (rm32)":
    return base_address
  match = COUNT_SLIDE_RM32_PATTERN.match(base_address)
  if match is None:
    return base_address
  return "%s%s%s" % (
      match.group(1), match.group("register").upper(), match.group("tail"))


def _check_encoded_shellcode(
    upstream: ModuleType,
    encoded_shellcode: str,
    encoder_settings: Dict[str, object],
) -> List[str]:
  valid_chars = upstream.charsets.valid_chars[
      encoder_settings["character encoding"]][encoder_settings["case"]]
  errors = []
  for index, char in enumerate(encoded_shellcode):
    if char not in valid_chars:
      charcode_str = upstream.charsets.charcode_fmtstr[
          encoder_settings["character encoding"]] % ord(char)
      errors.append("Byte %d @0x%02X: %s (%s)" % (
          index, index, char, charcode_str))
  return errors
