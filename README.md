# pyc_obscure (demo)
a simple obfuscator for pyc


## theory

insert junk data into co_code of PyCodeObject to obfuscate decompiler like uncompyle6


## usage

```python
from pyc_obscure import Obscure

obs = Obscure('test.pyc')
obs.basic_obscure()
obs.write_pyc('obs_test.pyc')
```

# TODO

- support multi version of python (python3.7 only now)
- complex obscure (not just junk JUMP), add fake control flow
- ~~support add consts like string~~
- compute JUMP offset in loop (loop implementations differs with different version)

