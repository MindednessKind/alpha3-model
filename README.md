# alpha3-py

Python 3 的 ALPHA3 wrapper。功能很单一：接收 shellcode 和参数，调用 SkyLined 的 ALPHA3 编码器，返回 alphanumeric shellcode。

编码器本体通过子模块引入，不在本仓库中维护：

```text
alpha3-python3 -> https://github.com/MindednessKind/alpha3-python3.git
```

这边的代码负责参数整理、调用上游、将结果以 `bytes` 返回。

入口函数是 `alpha3.build(...)`：

```python
import alpha3

payload = alpha3.build(
    b"\x90\x90\xcc",
    arch="amd64",
    pack="mixedcase",
    encode="ascii",
    register="rax",
)
```

## 安装

克隆时带上子模块：

```bash
git clone --recurse-submodules https://github.com/MindednessKind/alpha3-model.git
```

已经克隆过的话，补上子模块：

```bash
git submodule update --init --recursive
```

也可以用部署脚本一步完成：

```bash
python3 deploy.py
```

`deploy.py` 会做这几件事：

- 初始化或更新 `alpha3-python3` 子模块
- `pip install -e .` 安装 wrapper
- 跑一次 smoke test 确认可用

离线环境下，如果本地已有 setuptools，脚本会自动加 `--no-build-isolation` 以避免访问 PyPI。需要标准隔离构建时传 `--build-isolation`。

## 使用

不安装也能用，指定 `PYTHONPATH` 即可：

```bash
PYTHONPATH=src python3 your_script.py
```

```python
import alpha3

payload = alpha3.build(
    b"\x90\x90\xcc",
    pack="mixedcase",
    register="eax",
)
```

返回值是 `bytes`。输入的 shellcode 需要是 bytes-like 对象，且不能包含 NULL 字节——这是 ALPHA3 本身的限制，wrapper 会提前检查并给出明确报错。

## 参数

```python
alpha3.build(shellcode=None, *, pack, register, arch=None, encode="ascii")
```

日常使用主要关注 `pack` 和 `register`。`arch` 不传时会读 `pwn.context.arch`，没有 pwntools 则默认 x86。

| 参数 | 说明 |
|------|------|
| `shellcode` | 可选。传入时直接返回编码结果；不传时返回一个可复用的 encoder 函数 |
| `pack` | 必填。`mixedcase` / `lowercase` / `uppercase`，也接受 `mix` `lower` `upper` 等缩写 |
| `register` | 必填。base address register，如 `rax` `eax` `ecx`，可用值取决于架构和编码器 |
| `arch` | 可选。支持 `amd64` `x86_64` `x64` `i386` `i686` `x86` 等常见写法 |
| `encode` | 可选，默认 `ascii`。另支持 `cp437` `latin-1` `utf-16` 及对应别名 |

register 匹配不区分大小写。countslide 格式也做了兼容处理，`countslide:eax+...` 会自动转为上游需要的 `countslide:EAX+...`。

## 示例

amd64：

```python
payload = alpha3.build(
    b"\x90\x90\xcc",
    arch="amd64",
    pack="mixedcase",
    register="rax",
)
```

x86 uppercase：

```python
payload = alpha3.build(
    b"\x90\x90\xcc",
    arch="i386",
    pack="uppercase",
    register="eax",
)
```

同一组参数需要反复使用时，可以先获取 encoder：

```python
enc = alpha3.build(arch="amd64", pack="mixedcase", register="rax")
payload = enc(b"\x90\x90\xcc")
```

配合 pwntools，由 context 决定架构：

```python
from pwn import context
import alpha3

context.arch = "amd64"
payload = alpha3.build(b"\x90\x90\xcc", pack="mixedcase", register="rax")
```

## 约束

- 公开接口只有 `import alpha3` 和 `alpha3.build(...)`。
- 旧入口 `ALPHA3`、`encode`、`shellcode`、`x86`、`x64` 已移除。
- 上游源码只从子模块加载，`src/alpha3/` 中不维护副本。

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

检查部署脚本语法：

```bash
python3 -m py_compile deploy.py
```

测试覆盖范围：子模块存在性与远程地址、amd64/x86 编码调用、countslide 大小写兼容、默认 encode 值、省略 shellcode 返回 encoder、NULL 字节抛出 ValueError、从 pwntools context 读取架构、旧入口不可导入。

## License

本仓库中的 wrapper、部署脚本、测试和文档使用 MIT License：

```text
Copyright (c) 2026 MindednessKind <mindednesskind@gmail.com>
```

这不影响上游 ALPHA3 的授权。上游版权和许可条款以 `COPYRIGHT.txt` 及子模块自身的授权文件为准。
