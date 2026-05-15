# alpha3-py

这是一个面向 Python 3 的 ALPHA3 调用入口项目。项目本身不再复制
SkyLined ALPHA3 的完整源码到 `src/alpha3/`，而是通过项目根目录下的
`alpha3-python3` Git submodule 加载上游实现：

```text
alpha3-python3 -> https://github.com/MindednessKind/alpha3-python3.git
```

当前公开 API 只保留一种调用方式：

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

## 安装与使用

克隆本仓库时同时拉取上游子模块：

```bash
git clone --recurse-submodules https://github.com/MindednessKind/alpha3-model.git
```

如果已经克隆过本仓库，初始化子模块：

```bash
git submodule update --init --recursive
```

在当前仓库中直接使用：

```bash
PYTHONPATH=src python3 your_script.py
```

或在脚本中：

```python
import alpha3

payload = alpha3.build(
    b"\x90\x90\xcc",
    pack="mixedcase",
    register="eax",
)
```

`alpha3.build` 返回 `bytes`。输入 shellcode 必须是 bytes-like 对象，且
ALPHA3 原始约束要求 shellcode 不含 NULL 字节。

## 参数说明

`alpha3.build(shellcode=None, *, pack, register, arch=None, encode="ascii")`

- `shellcode`：可选。传入时立即生成编码后的 shellcode；不传时返回一个可复用 encoder 函数。
- `pack`：必填。字符大小写包，可用值包括 `lowercase`、`mixedcase`、`uppercase`，也支持 `lower`、`mix`、`mixed`、`upper` 别名。
- `register`：必填。ALPHA3 base address/register，例如 `rax`、`eax`、`ecx` 等，具体取决于所选架构和编码器。
- `arch`：可选。支持 `amd64`、`x86_64`、`x64`、`i386`、`i686`、`x86` 等别名。省略时会读取 `pwn.context.arch`，无法读取 pwntools 时默认使用 x86。
- `encode`：可选。默认 `ascii`，也支持 `cp437`、`latin-1`、`utf-16` 及对应别名。

默认情况下，真正需要用户显式指定的配置只有 `pack` 和 `register`。

`register` 匹配大小写不敏感。对 x86 ascii mixedcase countslide
寄存器形式，wrapper 会把 `countslide:eax+...` 这类输入规范化为上游
decoder 文件使用的 `countslide:EAX+...` 形式。

## 示例

直接生成 amd64 alphanumeric shellcode：

```python
import alpha3

payload = alpha3.build(
    b"\x90\x90\xcc",
    arch="amd64",
    pack="mixedcase",
    register="rax",
)
```

生成 x86 uppercase payload：

```python
import alpha3

payload = alpha3.build(
    b"\x90\x90\xcc",
    arch="i386",
    pack="uppercase",
    register="eax",
)
```

复用 encoder：

```python
import alpha3

enc = alpha3.build(arch="amd64", pack="mixedcase", register="rax")
payload = enc(b"\x90\x90\xcc")
```

配合 pwntools 的 `context.arch`：

```python
from pwn import context
import alpha3

context.arch = "amd64"
payload = alpha3.build(
    b"\x90\x90\xcc",
    pack="mixedcase",
    register="rax",
)
```

## 当前约束

- 公开入口只保留 `import alpha3` 与 `alpha3.build(...)`。
- 旧调用入口 `ALPHA3`、`encode`、`shellcode`、`x86`、`x64` 已移除。
- 上游 ALPHA3 源码通过 `alpha3-python3` 子模块加载，不在 `src/alpha3/` 内维护副本。

## 测试

运行测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

测试覆盖：

- `alpha3-python3` 子模块是否存在并指向 `https://github.com/MindednessKind/alpha3-python3.git`
- `alpha3.build(...)` 的 amd64/x86 调用
- x86 countslide register 参数大小写兼容
- `encode="ascii"` 默认值
- 省略 shellcode 时返回可复用 encoder
- 包含 NULL 字节的输入会稳定抛出 `ValueError`
- 从 `pwn.context.arch` 读取架构
- 旧入口模块不可导入
