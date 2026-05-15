import importlib
import sys
import unittest
from pathlib import Path

import alpha3


def is_ascii_alnum(data):
  return all(
      0x30 <= b <= 0x39 or 0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A
      for b in data)


class Alpha3ApiTests(unittest.TestCase):
  def test_alpha3_python3_is_submodule(self):
    root = Path(__file__).resolve().parents[1]
    upstream = root / "alpha3-python3"
    gitmodules = root / ".gitmodules"
    self.assertTrue(upstream.is_dir())
    self.assertTrue((upstream / "ALPHA3.py").is_file())
    self.assertIn("path = alpha3-python3", gitmodules.read_text())
    self.assertIn(
        "url = https://github.com/MindednessKind/alpha3-python3.git",
        gitmodules.read_text(),
    )

  def test_build_direct_x64(self):
    encoded = alpha3.build(
        b"\x90\x90\xcc",
        arch="amd64",
        pack="mixedcase",
        encode="ascii",
        register="rax",
    )
    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_ascii_alnum(encoded))

  def test_build_direct_x86_defaults_encode(self):
    encoded = alpha3.build(
        b"\x90\x90\xcc",
        arch="i386",
        pack="uppercase",
        register="eax",
    )
    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_ascii_alnum(encoded))

  def test_build_returns_encoder_when_shellcode_is_omitted(self):
    encoder = alpha3.build(arch="amd64", pack="mixedcase", register="rax")
    encoded = encoder(b"\x90\x90\xcc")
    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_ascii_alnum(encoded))

  def test_build_rejects_null_bytes(self):
    with self.assertRaisesRegex(ValueError, "NULL-free"):
      alpha3.build(
          b"\x90\x00\xcc",
          arch="amd64",
          pack="mixedcase",
          register="rax",
      )

  def test_build_normalizes_countslide_register_case(self):
    encoded = alpha3.build(
        b"\x90\x90\xcc",
        arch="i386",
        pack="mixedcase",
        register="countslide:eax+0x0~0x200",
    )
    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_ascii_alnum(encoded))

  def test_build_reads_pwntools_context_arch(self):
    class FakeContext:
      arch = "amd64"

    fake_pwn = type(sys)("pwn")
    fake_pwn.context = FakeContext()
    old_pwn = sys.modules.get("pwn")
    sys.modules["pwn"] = fake_pwn
    try:
      encoded = alpha3.build(
          b"\x90\x90\xcc",
          pack="mixedcase",
          register="rax",
      )
    finally:
      if old_pwn is None:
        sys.modules.pop("pwn", None)
      else:
        sys.modules["pwn"] = old_pwn

    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_ascii_alnum(encoded))

  def test_old_entrypoints_are_removed(self):
    for module_name in ("ALPHA3", "encode", "shellcode", "x86", "x64"):
      with self.subTest(module=module_name):
        sys.modules.pop(module_name, None)
        with self.assertRaises(ModuleNotFoundError):
          importlib.import_module(module_name)


if __name__ == "__main__":
  unittest.main()
