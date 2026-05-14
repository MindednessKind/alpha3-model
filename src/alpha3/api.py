import re
from typing import Dict, Iterable, List, Optional, Union

from . import charsets
from . import x64, x86


BytesLike = Union[bytes, bytearray, memoryview]


class Alpha3Error(Exception):
  pass


def _to_latin1_text(shellcode: BytesLike) -> str:
  if isinstance(shellcode, str):
    raise TypeError("shellcode must be bytes-like, not str")
  return bytes(shellcode).decode("latin-1")


def _to_bytes(shellcode: str) -> bytes:
  return shellcode.encode("latin-1")


def _check_encoded_shellcode(encoded_shellcode: str, encoder_settings: Dict[str, object]) -> List[str]:
  valid_chars = charsets.valid_chars[
      encoder_settings["character encoding"]][encoder_settings["case"]]
  errors = []
  for index, char in enumerate(encoded_shellcode):
    if char not in valid_chars:
      charcode_str = charsets.charcode_fmtstr[
          encoder_settings["character encoding"]] % ord(char)
      errors.append("Byte %d @0x%02X: %s (%s)" % (
          index, index, char, charcode_str))
  return errors


class ALPHA3:
  def __init__(self):
    self.encoders = []
    self.encoders.extend(x86.encoders)
    self.encoders.extend(x64.encoders)

  def list_encoders(self) -> List[Dict[str, object]]:
    return [dict(encoder) for encoder in self.encoders]

  def encode(
      self,
      shellcode: BytesLike,
      architecture: str = "x86",
      encoding: str = "ascii",
      case: str = "mixedcase",
      base_address: Optional[str] = None,
      encoder_name: Optional[str] = None,
  ) -> bytes:
    shellcode_text = _to_latin1_text(shellcode)
    matches = list(self._matching_encoders(
        architecture, encoding, case, base_address, encoder_name))
    if not matches:
      raise Alpha3Error("No encoder exists for the given settings.")
    if len(matches) > 1:
      names = ", ".join(encoder["name"] for encoder in matches)
      raise Alpha3Error(
          "Multiple encoders match; provide base_address or encoder_name: %s" % names)

    encoder_settings = matches[0]
    encoder_function = encoder_settings["function"]
    encoder_function_args = encoder_settings.get("function args", {})
    encoded_shellcode = encoder_function(
        base_address, shellcode_text, *encoder_function_args)

    errors = _check_encoded_shellcode(encoded_shellcode, encoder_settings)
    if errors:
      raise Alpha3Error(
          "Encoded shellcode contains bad characters:\n%s" % "\n".join(errors))
    return _to_bytes(encoded_shellcode)

  def _matching_encoders(
      self,
      architecture: str,
      encoding: str,
      case: str,
      base_address: Optional[str],
      encoder_name: Optional[str],
  ) -> Iterable[Dict[str, object]]:
    for encoder in self.encoders:
      if encoder["architecture"] != architecture:
        continue
      if encoder["character encoding"] != encoding:
        continue
      if encoder["case"] != case:
        continue
      if encoder_name is not None and encoder["name"] != encoder_name:
        continue
      if base_address is not None and not re.match(
          encoder["base address"], base_address, re.IGNORECASE):
        continue
      yield encoder


def encode(
    shellcode: BytesLike,
    architecture: str = "x86",
    encoding: str = "ascii",
    case: str = "mixedcase",
    base_address: Optional[str] = None,
    encoder_name: Optional[str] = None,
) -> bytes:
  return ALPHA3().encode(
      shellcode,
      architecture=architecture,
      encoding=encoding,
      case=case,
      base_address=base_address,
      encoder_name=encoder_name,
  )


def list_encoders() -> List[Dict[str, object]]:
  return ALPHA3().list_encoders()
