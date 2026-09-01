# Portfolio Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将旧版 Bilibili 弹幕实验脚本重构为支持 Bilibili、GitHub、RSS/Atom 和静态网页的可安装 Python CLI，并提供统一导出、离线分析、测试、CI 与中英文文档。

**Architecture:** 使用 `src` 布局与适配器模式，所有来源输出统一 `Record`，共享带超时和重试的 HTTP 客户端。导出器与分析器只消费标准记录或本地文件，CLI 负责组合模块、展示错误与设置退出码。

**Tech Stack:** Python 3.10+、Typer、httpx、Pydantic 2、Beautiful Soup 4、feedparser、jieba、WordCloud、pytest、pytest-httpx、Ruff、mypy、GitHub Actions。

---

## 文件结构

```text
src/scraper/
├── __init__.py             # 包版本
├── cli.py                  # Typer 命令与错误展示
├── exceptions.py           # 领域异常
├── http.py                 # 超时、重试、限速与脱敏
├── models.py               # Record 与采集结果
├── adapters/
│   ├── __init__.py
│   ├── base.py             # SourceAdapter 协议
│   ├── bilibili.py         # 视频信息与公开弹幕
│   ├── github.py           # 仓库、Issue、Release
│   ├── rss.py              # RSS/Atom 条目
│   └── web.py              # CSS 选择器静态网页
├── exporters/
│   ├── __init__.py
│   ├── csv.py
│   └── jsonl.py
└── analysis/
    ├── __init__.py
    ├── frequency.py
    ├── loader.py
    └── wordcloud.py
tests/
├── fixtures/
├── adapters/
├── test_analysis.py
├── test_cli.py
├── test_exporters.py
├── test_http.py
└── test_models.py
```

### Task 1: 建立包骨架与质量门禁

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `LICENSE`
- Create: `src/scraper/__init__.py`
- Create: `src/scraper/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 写 CLI 冒烟失败测试**

```python
from typer.testing import CliRunner
from scraper.cli import app

runner = CliRunner()

def test_cli_help_lists_command_groups() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "collect" in result.stdout
    assert "analyze" in result.stdout
```

- [ ] **Step 2: 验证测试因包不存在而失败**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL，错误包含 `No module named 'scraper'`。

- [ ] **Step 3: 添加构建配置与最小 CLI**

`pyproject.toml` 声明项目 `portfolio-scraper`、Python `>=3.10`、基础依赖 `typer`、`httpx`、`pydantic`、`beautifulsoup4`、`feedparser`，可选依赖组 `analysis` 和 `dev`，脚本入口为 `scraper = "scraper.cli:app"`。Ruff 行宽设为 100，mypy 开启 `strict = true`，pytest 设置 `testpaths = ["tests"]`。

```python
import typer

app = typer.Typer(help="Collect and analyze public web data.")
collect_app = typer.Typer(help="Collect records from a source.")
analyze_app = typer.Typer(help="Analyze local records.")
app.add_typer(collect_app, name="collect")
app.add_typer(analyze_app, name="analyze")
```

- [ ] **Step 4: 安装开发依赖并通过测试**

Run: `python -m pip install -e ".[dev,analysis]" --break-system-packages`
Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add pyproject.toml .gitignore .env.example LICENSE src tests/test_cli.py
git commit -m "build: establish package and quality tooling"
```

### Task 2: 定义领域模型与适配器契约

**Files:**
- Create: `src/scraper/models.py`
- Create: `src/scraper/exceptions.py`
- Create: `src/scraper/adapters/__init__.py`
- Create: `src/scraper/adapters/base.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 写模型校验失败测试**

```python
from pydantic import ValidationError
from scraper.models import Record

def test_record_rejects_missing_source() -> None:
    with pytest.raises(ValidationError):
        Record(source="", id="1", url="https://example.com", content="hello")

def test_record_accepts_json_metadata() -> None:
    record = Record(
        source="rss", id="1", title="Post", url="https://example.com/1",
        content="hello", metadata={"tags": ["python"]},
    )
    assert record.metadata["tags"] == ["python"]
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL，`Record` 尚未定义。

- [ ] **Step 3: 实现模型、结果与协议**

```python
class Record(BaseModel):
    source: str = Field(min_length=1)
    id: str = Field(min_length=1)
    title: str = ""
    url: HttpUrl
    content: str = ""
    author: str = ""
    published_at: datetime | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

class CollectionResult(BaseModel):
    records: list[Record] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
```

`SourceAdapter` 定义 `source: str` 和 `collect(**kwargs: object) -> CollectionResult`。异常层定义 `ScraperError`、`ConfigurationError`、`AuthenticationError`、`RateLimitError`、`RemoteResponseError`、`ParseError`、`ExportError`。

- [ ] **Step 4: 运行模型与类型检查**

Run: `python -m pytest tests/test_models.py -v`
Run: `python -m mypy src`
Expected: 全部通过。

- [ ] **Step 5: 提交**

```bash
git add src/scraper/models.py src/scraper/exceptions.py src/scraper/adapters tests/test_models.py
git commit -m "feat: define records and adapter contract"
```

### Task 3: 实现可靠 HTTP 客户端

**Files:**
- Create: `src/scraper/http.py`
- Create: `tests/test_http.py`

- [ ] **Step 1: 写超时、重试与脱敏失败测试**

```python
def test_client_retries_503_then_returns_json(httpx_mock) -> None:
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(json={"ok": True})
    client = HttpClient(max_retries=1, backoff_factor=0)
    assert client.get_json("https://example.com") == {"ok": True}

def test_redact_headers_hides_credentials() -> None:
    redacted = redact_headers({"Authorization": "Bearer secret", "Cookie": "sid=secret"})
    assert redacted == {"Authorization": "***", "Cookie": "***"}
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest tests/test_http.py -v`
Expected: FAIL，HTTP 模块尚不存在。

- [ ] **Step 3: 实现客户端**

`HttpClient` 包装 `httpx.Client`，默认连接/读取超时 5/20 秒、最大响应体 10 MiB、最多重试 2 次。仅重试网络异常、`429`、`500`、`502`、`503`、`504`；优先读取 `Retry-After`，否则使用 `backoff_factor * 2**attempt`。提供 `get_json()` 与 `get_text()`，并将状态码映射到领域异常。

- [ ] **Step 4: 验证 HTTP 测试**

Run: `python -m pytest tests/test_http.py -v`
Expected: PASS，且测试不访问公网。

- [ ] **Step 5: 提交**

```bash
git add src/scraper/http.py tests/test_http.py
git commit -m "feat: add resilient HTTP client"
```

### Task 4: 实现 Bilibili 适配器

**Files:**
- Create: `src/scraper/adapters/bilibili.py`
- Create: `tests/fixtures/bilibili_view.json`
- Create: `tests/fixtures/bilibili_danmaku.xml`
- Create: `tests/adapters/test_bilibili.py`

- [ ] **Step 1: 写固定夹具解析失败测试**

```python
def test_collects_video_and_danmaku_records(fake_http) -> None:
    adapter = BilibiliAdapter(fake_http)
    result = adapter.collect(bvid="BV1xx411c7mD")
    assert result.errors == []
    assert [record.metadata["kind"] for record in result.records] == ["video", "danmaku", "danmaku"]
    assert all(record.source == "bilibili" for record in result.records)
```

- [ ] **Step 2: 验证失败**

Run: `python -m pytest tests/adapters/test_bilibili.py -v`
Expected: FAIL，适配器尚不存在。

- [ ] **Step 3: 实现公开数据采集**

校验 BV 号格式；调用公开视频详情接口获取标题、作者、发布时间和分 P CID，再读取公开 XML 弹幕。使用 `xml.etree.ElementTree` 解析文本并生成一个视频记录与若干弹幕记录；不读取或硬编码 Cookie。

- [ ] **Step 4: 验证解析与错误分支**

Run: `python -m pytest tests/adapters/test_bilibili.py -v`
Expected: 成功、空弹幕、API 错误码和畸形 XML 用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/scraper/adapters/bilibili.py tests/adapters/test_bilibili.py tests/fixtures/bilibili_*
git commit -m "feat: add Bilibili public data adapter"
```

### Task 5: 实现 GitHub、RSS 与网页适配器

**Files:**
- Create: `src/scraper/adapters/github.py`
- Create: `src/scraper/adapters/rss.py`
- Create: `src/scraper/adapters/web.py`
- Create: `tests/adapters/test_github.py`
- Create: `tests/adapters/test_rss.py`
- Create: `tests/adapters/test_web.py`
- Create: `tests/fixtures/github_*.json`
- Create: `tests/fixtures/feed.xml`
- Create: `tests/fixtures/page.html`

- [ ] **Step 1: 写三个适配器的失败测试**

```python
def test_github_issues_become_records(fake_http) -> None:
    result = GitHubAdapter(fake_http, token=None).collect(repo="owner/repo", resource="issues")
    assert result.records[0].metadata["kind"] == "issue"

def test_rss_uses_guid_as_id(fake_http) -> None:
    result = RssAdapter(fake_http).collect(url="https://example.com/feed.xml")
    assert result.records[0].id == "post-1"

def test_web_resolves_relative_links(fake_http) -> None:
    result = WebAdapter(fake_http).collect(
        url="https://example.com/blog/", item="article", title="h2", content="p", link="a"
    )
    assert str(result.records[0].url) == "https://example.com/post-1"
```

- [ ] **Step 2: 验证失败**

Run: `python -m pytest tests/adapters/test_github.py tests/adapters/test_rss.py tests/adapters/test_web.py -v`
Expected: FAIL，三个适配器尚不存在。

- [ ] **Step 3: 实现 GitHub 适配器**

支持 `repository`、`issues`、`releases` 三种资源；可选从 `GITHUB_TOKEN` 注入 Bearer 认证；过滤 Pull Request 伪装的 Issue；将 API 错误消息转换为领域异常。

- [ ] **Step 4: 实现 RSS 与网页适配器**

RSS 使用 feedparser 解析 RSS/Atom，缺失字段时使用确定性回退。网页适配器使用 Beautiful Soup 与 CSS 选择器，验证 item 至少匹配一项，使用 `urljoin` 解析相对链接，并以 URL 加内容摘要生成稳定 ID。

- [ ] **Step 5: 验证三个适配器**

Run: `python -m pytest tests/adapters -v`
Expected: 全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add src/scraper/adapters tests/adapters tests/fixtures
git commit -m "feat: add GitHub RSS and web adapters"
```

### Task 6: 实现导出与离线分析

**Files:**
- Create: `src/scraper/exporters/__init__.py`
- Create: `src/scraper/exporters/jsonl.py`
- Create: `src/scraper/exporters/csv.py`
- Create: `src/scraper/analysis/__init__.py`
- Create: `src/scraper/analysis/loader.py`
- Create: `src/scraper/analysis/frequency.py`
- Create: `src/scraper/analysis/wordcloud.py`
- Create: `tests/test_exporters.py`
- Create: `tests/test_analysis.py`

- [ ] **Step 1: 写 round-trip 与中文词频失败测试**

```python
def test_jsonl_round_trip_preserves_metadata(tmp_path, records) -> None:
    output = tmp_path / "records.jsonl"
    export_jsonl(records, output)
    assert load_records(output) == records

def test_frequency_filters_stopwords() -> None:
    rows = word_frequency(["保护海洋 保护地球", "保护海洋"], stopwords={"保护"})
    assert rows[0] == ("海洋", 2)
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest tests/test_exporters.py tests/test_analysis.py -v`
Expected: FAIL，模块尚不存在。

- [ ] **Step 3: 实现导出与加载**

JSONL 每行写入一个 UTF-8 JSON 对象；CSV 固定列顺序并将 metadata 写成无 ASCII 转义 JSON。加载器按扩展名读取 `.jsonl`、`.csv`、`.txt`，对无效行报告文件名和行号。

- [ ] **Step 4: 实现词频与词云**

词频使用 jieba，支持停用词、最小词长、字段和 Top N。词云延迟导入可选依赖，自动查找常见中文字体，也允许 `--font-path` 覆盖；无字体时抛出包含修复命令的 `ConfigurationError`。

- [ ] **Step 5: 验证**

Run: `python -m pytest tests/test_exporters.py tests/test_analysis.py -v`
Expected: 全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add src/scraper/exporters src/scraper/analysis tests/test_exporters.py tests/test_analysis.py
git commit -m "feat: add exporters and text analysis"
```

### Task 7: 完成 CLI 编排与部分失败语义

**Files:**
- Modify: `src/scraper/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写命令与退出码失败测试**

```python
def test_collect_rss_writes_jsonl(monkeypatch, tmp_path) -> None:
    output = tmp_path / "feed.jsonl"
    monkeypatch.setattr("scraper.cli.RssAdapter", FakeRssAdapter)
    result = runner.invoke(app, ["collect", "rss", "--url", "https://example.com/feed", "-o", str(output)])
    assert result.exit_code == 0
    assert output.exists()

def test_partial_failure_returns_exit_code_two(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("scraper.cli.GitHubAdapter", PartiallyFailingAdapter)
    result = runner.invoke(app, ["collect", "github", "--repo", "o/r", "--resource", "issues"])
    assert result.exit_code == 2
    assert "1 record collected; 1 item failed" in result.stdout
```

- [ ] **Step 2: 验证失败**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL，子命令尚未注册。

- [ ] **Step 3: 实现 collect 与 analyze 命令**

为四个来源创建独立命令参数；根据输出扩展名选择导出器；支持 `--fail-fast`、`--timeout`、`--retries`、`--request-delay` 和 `--debug`。整体成功返回 0，部分失败返回 2，配置或整体失败返回 1。

- [ ] **Step 4: 验证 CLI**

Run: `python -m pytest tests/test_cli.py -v`
Run: `scraper --help`
Expected: 测试 PASS，帮助列出所有来源与分析命令。

- [ ] **Step 5: 提交**

```bash
git add src/scraper/cli.py tests/test_cli.py
git commit -m "feat: expose collection and analysis CLI"
```

### Task 8: 清理旧代码与敏感信息

**Files:**
- Delete: `main.py`
- Delete: `analysis.py`
- Delete: `func/`
- Move selected sample data to: `examples/data/`
- Move selected screenshot to: `docs/assets/`
- Delete obsolete generated data and duplicate images
- Create: `tests/test_repository_hygiene.py`

- [ ] **Step 1: 写仓库敏感字段失败测试**

```python
def test_tracked_text_files_do_not_contain_session_credentials() -> None:
    forbidden = ("SESSDATA=", "bili_jct=", "DedeUserID=", "Cookie\":")
    offenders = scan_tracked_text_files(Path.cwd(), forbidden)
    assert offenders == []
```

- [ ] **Step 2: 验证当前仓库失败**

Run: `python -m pytest tests/test_repository_hygiene.py -v`
Expected: FAIL，并列出旧脚本中的 Cookie/会话字段。

- [ ] **Step 3: 清理仓库**

删除重复和失效脚本；只保留一个脱敏且体积小的示例数据集。将可复用展示图放入 `docs/assets/`，在 `.gitignore` 中忽略根目录运行产物、`.env`、缓存和构建目录。

- [ ] **Step 4: 验证当前树与历史提醒**

Run: `python -m pytest tests/test_repository_hygiene.py -v`
Run: `git grep -n -E 'SESSDATA=|bili_jct=|DedeUserID=|Cookie\"' -- ':!docs/superpowers/**'`
Expected: 测试 PASS，`git grep` 无输出。注意此检查不代表旧 Git 历史已净化。

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "security: remove embedded credentials and legacy scripts"
```

### Task 9: 添加 CI、贡献指南与中英文 README

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `CONTRIBUTING.md`
- Rewrite: `README.md`
- Create: `README.zh-CN.md`

- [ ] **Step 1: 添加 CI 配置**

Actions 在 Python 3.10、3.11、3.12、3.13 上安装 `.[dev,analysis]` 并运行：

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov=scraper --cov-report=term-missing
```

- [ ] **Step 2: 编写中英文 README**

两份 README 包含：互相跳转、真实项目定位、功能概览、安装、快速开始、四适配器命令、记录格式、分析命令、架构、扩展适配器、环境变量、安全合规、测试、路线图、贡献和许可证。仅引用实际存在的截图与实际通过的命令。

- [ ] **Step 3: 编写贡献指南**

说明开发安装、分支与提交约定、测试命令、新增适配器契约、夹具要求和禁止提交凭据。

- [ ] **Step 4: 验证文档命令与链接**

Run: `python -m build`
Run: `scraper --help`
Run: `python -m pytest -q`
Expected: 构建成功、CLI 可执行、测试全部通过。

- [ ] **Step 5: 提交**

```bash
git add .github CONTRIBUTING.md README.md README.zh-CN.md
git commit -m "docs: package Scraper as a portfolio project"
```

### Task 10: 完整质量验收

**Files:**
- Modify only if verification exposes defects.

- [ ] **Step 1: 执行静态与单元验证**

Run: `ruff format --check . && ruff check . && mypy src && pytest --cov=scraper --cov-report=term-missing`
Expected: 所有命令退出码为 0。

- [ ] **Step 2: 在隔离环境验证安装**

Run: `uv run --isolated --with '.[analysis]' scraper --help`
Expected: CLI 正常展示帮助，不依赖仓库外已安装包。

- [ ] **Step 3: 执行最小真实网络探针**

仅在网络可访问且无需规避验证时，各选择一个公开 Bilibili 视频、公开 GitHub 仓库、稳定 RSS 源和静态示例页运行采集，并记录命令、时间、状态码与记录数。若平台限制或网络不可用，明确标记“未验证”，不得用夹具结果替代。

- [ ] **Step 4: 核查工作树与差异**

Run: `git status --short`
Run: `git diff main...HEAD --check`
Run: `git log --oneline main..HEAD`
Expected: 工作树干净、无空白错误、提交按任务拆分。

- [ ] **Step 5: 如有验收修复则提交**

```bash
git add <修复文件>
git commit -m "fix: address final verification findings"
```

## 自检结论

- 设计文档中的四适配器、统一模型、HTTP 策略、导出、分析、安全、测试、仓库整理、CI 和中英文 README 均有对应任务。
- 所有后续任务使用同一 `Record`、`CollectionResult`、`HttpClient` 与 `collect()` 命名。
- 首版未引入动态浏览器、数据库、调度器、登录自动化或 YAML DSL，符合 YAGNI 边界。
