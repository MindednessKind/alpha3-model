from __future__ import annotations

from ._bridge import encode_shellcode


ARCH_ALIASES = {
    "x86": "x86",
    "i386": "x86",
    "i686": "x86",
    "386": "x86",
    "x64": "x64",
    "amd64": "x64",
    "x86_64": "x64",
    "64": "x64",
}

PACK_ALIASES = {
    "lower": "lowercase",
    "lowercase": "lowercase",
    "mix": "mixedcase",
    "mixed": "mixedcase",
    "mixedcase": "mixedcase",
    "upper": "uppercase",
    "uppercase": "uppercase",
}

ENCODE_ALIASES = {
    "ascii": "ascii",
    "cp437": "cp437",
    "latin1": "latin-1",
    "latin-1": "latin-1",
    "utf16": "utf-16",
    "utf-16": "utf-16",
}


def build(shellcode=None, *, pack, register, arch=None, encode="ascii"):
  architecture = _normalize_arch(arch or _context_arch())
  case = _normalize_pack(pack)
  encoding = _normalize_encode(encode)

  def encoder(data):
    return encode_shellcode(
        data,
        architecture=architecture,
        encoding=encoding,
        case=case,
        base_address=register,
    )

  if shellcode is None:
    return encoder
  return encoder(shellcode)


def _context_arch() -> str:
  try:
    from pwn import context
  except Exception:
    return "x86"
  return getattr(context, "arch", None) or "x86"


def _normalize_arch(arch: str) -> str:
  key = _normalize_key(arch)
  if key not in ARCH_ALIASES:
    raise ValueError("Unsupported ALPHA3 arch: %r" % arch)
  return ARCH_ALIASES[key]


def _normalize_pack(pack: str) -> str:
  key = _normalize_key(pack)
  if key not in PACK_ALIASES:
    raise ValueError("Unsupported ALPHA3 pack: %r" % pack)
  return PACK_ALIASES[key]


def _normalize_encode(encode: str) -> str:
  key = _normalize_key(encode)
  if key not in ENCODE_ALIASES:
    raise ValueError("Unsupported ALPHA3 encode: %r" % encode)
  return ENCODE_ALIASES[key]


def _normalize_key(value: str) -> str:
  if value is None:
    raise ValueError("ALPHA3 setting cannot be None")
  return str(value).replace("_", "-").lower()


__all__ = ["build"]
