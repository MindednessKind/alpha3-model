# alpha3-py

Python 3 library wrapper for SkyLined ALPHA3.

```python
from alpha3 import ALPHA3

encoder = ALPHA3()
shellcode = b"\x90\x90\xcc"
encoded = encoder.encode(
    shellcode,
    architecture="x64",
    encoding="ascii",
    case="mixedcase",
    base_address="rax",
)
```

Convenience function:

```python
from alpha3 import encode

encoded = encode(b"\x90\x90\xcc", architecture="x86", base_address="eax")
```

The returned value is `bytes`. ALPHA3 shellcode must be NULL-free.
