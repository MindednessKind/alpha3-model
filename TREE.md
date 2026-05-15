# 当前项目文件树

生成时间基于当前工作区状态。以下树不展开 `.git/`、`.agents/`、`.codex/` 等运行环境目录。

```text
.
├── README.md
├── REVIEW.md
├── TREE.md
├── NAVIGATION.md
├── COPYRIGHT.txt
├── .gitmodules
├── alpha3-python3 (submodule)
├── pyproject.toml
├── setup.py
├── src
│   └── alpha3
│       ├── __init__.py
│       └── _bridge.py
└── tests
    └── test_api.py
```

## 文件说明

- `README.md`：中文项目说明、使用方式、参数解释和测试命令。
- `REVIEW.md`：本轮代码审计记录，包含发现项、修复建议、验证方法和 shellcode 可运行检查结果。
- `TREE.md`：当前项目文件树。
- `NAVIGATION.md`：项目交接导航，记录功能完成情况和实现地址。
- `COPYRIGHT.txt`：上游 SkyLined ALPHA3 授权说明副本，供当前 wrapper 元数据引用。
- `.gitmodules`：声明 `alpha3-python3` 子模块及其 GitHub 地址。
- `alpha3-python3`：指向 `https://github.com/MindednessKind/alpha3-python3.git` 的 Git submodule，上游 ALPHA3 实现从这里加载。
- `pyproject.toml`：Python 打包配置，只声明 `alpha3` 包，并引用 `COPYRIGHT.txt`。
- `setup.py`：setuptools 兼容入口。
- `src/alpha3/__init__.py`：唯一公开 API，提供 `alpha3.build(...)`。
- `src/alpha3/_bridge.py`：内部桥接层，负责加载上游 ALPHA3 并执行 shellcode 编码。
- `tests/test_api.py`：单元测试，覆盖当前公开 API、子模块和旧入口移除情况。
