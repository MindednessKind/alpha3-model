# 项目交接导航

## 当前完成情况

项目已重构为单一公开入口：

```python
import alpha3

payload = alpha3.build(
    b"\x90\x90\xcc",
    pack="mixedcase",
    register="rax",
)
```

当前公开 API 只有 `alpha3.build(...)`。旧入口 `ALPHA3`、`encode`、`shellcode`、`x86`、`x64` 已从项目源码中移除，并由测试确认不可作为顶层模块导入。

上游 ALPHA3 源码没有复制到 `src/alpha3/` 内，而是通过项目根目录的
Git submodule 加载：

```text
alpha3-python3 (submodule) -> https://github.com/MindednessKind/alpha3-python3.git
```

本轮代码审计记录在 `REVIEW.md`。审计确认当前仓库内的 wrapper API
可以生成并运行 x64/x86 测试 shellcode。旧 wheel 已删除，NULL 字节
校验已移入 wrapper，license 元数据已改为引用仓库内 `COPYRIGHT.txt`。
当前模块设计为通过本仓库子模块加载上游源码，不面向独立 wheel 安装使用。

克隆时需要同步拉取子模块：

```bash
git clone --recurse-submodules https://github.com/MindednessKind/alpha3-model.git
```

已克隆仓库可执行：

```bash
git submodule update --init --recursive
```

## 功能与实现地址

### 1. 唯一公开入口 `alpha3.build`

地址：`src/alpha3/__init__.py`

实现内容：

- 定义 `build(shellcode=None, *, pack, register, arch=None, encode="ascii")`
- 支持直接传入 shellcode 并返回 `bytes`
- 支持省略 shellcode，返回可复用 encoder 函数
- 公开面通过 `__all__ = ["build"]` 限制为单一 API

### 2. 参数别名与默认值

地址：`src/alpha3/__init__.py`

实现内容：

- `ARCH_ALIASES`：支持 `amd64`、`x86_64`、`x64`、`i386`、`i686`、`x86` 等架构别名
- `PACK_ALIASES`：支持 `lowercase`、`mixedcase`、`uppercase` 及短别名
- `ENCODE_ALIASES`：支持 `ascii`、`cp437`、`latin-1`、`utf-16` 及常见别名
- `encode` 默认值为 `ascii`
- 用户默认只需要显式提供 `pack` 和 `register`

### 3. 从 pwntools `context.arch` 读取架构

地址：`src/alpha3/__init__.py`

实现函数：

- `_context_arch()`

行为：

- 当 `arch` 参数为空时尝试读取 `from pwn import context`
- 使用 `context.arch` 作为架构来源
- 如果 pwntools 不可用或无法读取，则默认返回 `x86`

### 4. 上游 ALPHA3 加载

地址：`src/alpha3/_bridge.py`

实现内容：

- `ROOT_DIR`：定位当前项目根目录
- `UPSTREAM_DIR`：定位 `alpha3-python3` 子模块
- `load_upstream_al3()`：加载 `alpha3-python3/ALPHA3.py`
- 加载期间临时处理 `sys.path` 和上游老式顶层模块名，加载完成后恢复，避免污染当前项目的公开模块空间

### 5. shellcode 编码桥接

地址：`src/alpha3/_bridge.py`

实现函数：

- `encode_shellcode(...)`
- `_matching_encoders(...)`
- `_base_address_matches(...)`
- `_check_encoded_shellcode(...)`

行为：

- 将 Python `bytes` shellcode 转为上游 ALPHA3 使用的 latin-1 字符串
- 显式拒绝包含 NULL 字节的输入，避免依赖上游 `assert`
- 根据 `arch`、`encode`、`pack`、`register` 匹配上游 encoder
- 对 x86 ascii mixedcase countslide 寄存器形式做大小写兼容，将
  `countslide:eax+...` 规范化为上游 decoder 文件使用的
  `countslide:EAX+...`
- 调用上游 encoder 函数生成编码 shellcode
- 检查编码结果是否满足对应字符集限制
- 返回 `bytes`

### 6. 打包配置

地址：`pyproject.toml`

当前配置：

- `package-dir = {"" = "src"}`
- `packages = ["alpha3"]`
- `license = {file = "COPYRIGHT.txt"}`

含义：

- 打包时只发布 `alpha3` 包
- 不发布旧的 `ALPHA3`、`encode`、`shellcode`、`x86`、`x64` 顶层模块
- 当前仓库不保留历史 `dist` wheel，避免旧 API 通过构建产物重新暴露

### 7. 测试覆盖

地址：`tests/test_api.py`

覆盖内容：

- `alpha3-python3` 子模块存在，且 `.gitmodules` 指向 `https://github.com/MindednessKind/alpha3-python3.git`
- `alpha3.build(...)` 可直接生成 amd64 mixedcase ascii payload
- `alpha3.build(...)` 可直接生成 x86 uppercase ascii payload
- `alpha3.build(...)` 支持小写 x86 countslide 寄存器参数
- `encode` 参数默认值为 `ascii`
- 省略 shellcode 时返回可复用 encoder
- 包含 NULL 字节的输入会稳定抛出 `ValueError`
- `arch` 省略时可读取模拟的 `pwn.context.arch`
- 旧入口 `ALPHA3`、`encode`、`shellcode`、`x86`、`x64` 不可导入

测试命令：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

最近验证：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 - <<'PY'
import alpha3
payload = alpha3.build(
    b"\x90\x90\xcc",
    arch="i386",
    pack="mixedcase",
    register="countslide:eax+0x0~0x200",
)
assert isinstance(payload, bytes) and payload.isalnum()
PY
```

## 常用维护入口

- 修改公开 API：`src/alpha3/__init__.py`
- 修改上游加载逻辑：`src/alpha3/_bridge.py`
- 增加或调整测试：`tests/test_api.py`
- 查看代码审计记录：`REVIEW.md`
- 更新项目文档：`README.md`
- 更新文件树：`TREE.md`
- 更新交接说明：`NAVIGATION.md`

## 交接注意事项

- 不要重新引入 `src/alpha3/ALPHA3.py` 等上游源码副本。
- 不要重新开放 `ALPHA3`、`encode`、`shellcode`、`x86`、`x64` 顶层入口。
- 如果上游项目地址变化，需要同步更新 `.gitmodules` 和 `alpha3-python3` 子模块指针。
- 每次改动公开 API 后应运行完整测试命令，并同步更新 README 与 NAVIGATION。
