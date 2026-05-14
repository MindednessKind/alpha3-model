import unittest

from alpha3 import ALPHA3, encode, list_encoders


def is_alnum(data):
  return all(
      0x30 <= b <= 0x39 or 0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A
      for b in data)


class Alpha3ApiTests(unittest.TestCase):
  def test_convenience_encode_x86(self):
    encoded = encode(b"\x90\x90\xcc", architecture="x86", base_address="eax")
    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_alnum(encoded))

  def test_class_encode_x64(self):
    encoded = ALPHA3().encode(
        b"\x90\x90\xcc", architecture="x64", base_address="rax")
    self.assertIsInstance(encoded, bytes)
    self.assertTrue(is_alnum(encoded))

  def test_list_encoders(self):
    encoders = list_encoders()
    self.assertTrue(encoders)
    self.assertTrue(any(encoder["architecture"] == "x64" for encoder in encoders))


if __name__ == "__main__":
  unittest.main()
