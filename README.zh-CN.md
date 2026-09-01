# Portfolio Scraper

[![CI](https://github.com/linhongyu510/Scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/linhongyu510/Scraper/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](README.md)

Portfolio Scraper 是一个可安装的 Python 命令行工具，用于采集 Bilibili、GitHub、
RSS/Atom 和静态网页中的公开数据。所有适配器输出统一记录模型，因此不同来源可以共用
JSONL/CSV 导出和离线文本分析能力。

项目展示了一套紧凑的适配器式采集架构，重点关注有边界的 HTTP 行为、确定性解析、
固定夹具测试和公开数据的合规使用。它不提供浏览器自动化、登录或访问控制绕过功能。

![Portfolio Scraper 生成的词云](docs/assets/demo-wordcloud.png)

## 功能

- 采集 Bilibili 公开视频信息与 XML 弹幕
- 采集 GitHub 仓库信息、Issue 和 Release
- 解析 RSS 2.0 与 Atom 条目
- 使用 CSS 选择器提取静态 HTML
- 导出 UTF-8 JSONL 和 CSV，并保留元数据
- 离线分析中文及混合语言词频
- 使用自动发现的中文字体生成可选 PNG 词云
- 统一处理超时、有限重试、请求间隔、响应体上限和请求头脱敏
- 提供类型化领域模型、离线测试夹具和 Python 3.10–3.13 CI

## 安装

需要 Python 3.10 或更高版本。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

按需安装分析能力和开发工具：

```bash
python -m pip install -e ".[analysis]"
python -m pip install -e ".[dev,analysis]"
```

## 快速开始

采集公开 RSS、查看正文高频词，并按需生成词云：

```bash
scraper collect rss \
  --url https://hnrss.org/frontpage \
  --output records.jsonl

scraper analyze frequency records.jsonl --field content --top 20
scraper analyze wordcloud records.jsonl --output wordcloud.png
```

`--output` 可省略；此时命令只报告记录数和错误数，不写文件。输出文件扩展名必须是
`.jsonl` 或 `.csv`。

## 采集命令

所有采集命令都支持 `--timeout`、`--retries`、`--request-delay`、`--fail-fast`
和 `--debug`。默认读取超时为 20 秒，最多重试两次，不额外延迟请求。

### Bilibili

```bash
scraper collect bilibili \
  --bvid BV1xx411c7mD \
  --output bilibili.jsonl \
  --request-delay 0.5
```

适配器访问公开视频信息和 XML 弹幕接口，不读取或发送浏览器 Cookie。

### GitHub

```bash
scraper collect github \
  --repo python/cpython \
  --resource repository \
  --output repository.jsonl

scraper collect github \
  --repo python/cpython \
  --resource issues \
  --output issues.csv

scraper collect github \
  --repo python/cpython \
  --resource releases \
  --output releases.jsonl
```

GitHub 的 Issue 接口也会返回 Pull Request，适配器会将这些项目过滤掉。

### RSS 与 Atom

```bash
scraper collect rss \
  --url https://hnrss.org/frontpage \
  --output feed.jsonl
```

记录 ID 优先使用 Feed GUID；若条目没有 GUID，则根据链接、标题和正文生成稳定 ID。

### 静态网页

```bash
scraper collect web \
  --url https://example.com/blog/ \
  --item article \
  --title h2 \
  --content p \
  --link a \
  --output posts.csv
```

标题、正文和链接选择器都在每个 item 元素内执行。相对链接会根据页面 URL 补全。该
适配器只读取原始 HTML，不执行 JavaScript。

## 记录格式

每个来源都输出以下结构：

```json
{
  "source": "rss",
  "id": "post-1",
  "title": "示例",
  "url": "https://example.com/posts/1",
  "content": "文章摘要",
  "author": "作者",
  "published_at": "2026-09-01T08:00:00Z",
  "metadata": {
    "kind": "entry",
    "tags": ["python"]
  }
}
```

`source`、`id` 和 `url` 为必填字段，各来源特有的数据存放在可 JSON 序列化的
`metadata` 对象中。

## 离线分析

加载器支持 `.jsonl`、`.csv` 和按行记录的 `.txt` 文件。

```bash
scraper analyze frequency examples/data/sample_danmaku.txt \
  --field content \
  --min-length 2 \
  --top 30

scraper analyze frequency records.jsonl \
  --stopwords stopwords.txt \
  --format json

scraper analyze wordcloud records.csv \
  --field content \
  --font-path /path/to/CJK-font.ttc \
  --output cloud.png
```

词云命令会搜索 macOS、Linux 和 Windows 上常见的中文字体。如果未找到字体，请通过
`--font-path` 指定。

## 架构

```text
CLI
 ├─ HttpClient：超时、重试、限速、响应体限制
 ├─ adapters：来源响应 → CollectionResult[Record]
 ├─ exporters：Record → JSONL 或 CSV
 └─ analysis：本地文件 → 词频或词云
```

`src` 布局使包导入不依赖仓库根目录。Pydantic 负责校验统一边界模型，适配器仅处理
来源特有的请求和解析逻辑。

## 扩展适配器

在 `src/scraper/adapters/` 中新增模块，定义稳定的 `source` 属性，并让 `collect`
返回 `CollectionResult`。网络请求应复用 `HttpClient`，远端错误应转换为领域异常，
来源特有字段应放入 `metadata`。先添加紧凑的离线夹具和测试，再在
`src/scraper/cli.py` 注册命令。

测试和夹具要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 环境变量

| 变量 | 必需 | 用途 |
| --- | --- | --- |
| `GITHUB_TOKEN` | 否 | 提高 GitHub 公开 API 的请求限额 |

`.env.example` 仅作变量说明。请通过 shell 或密钥管理工具设置变量；CLI 不会自动读取
`.env`。

## 安全与合规

只采集有权访问的公开数据，并遵守平台条款、robots 指引、速率限制、版权、隐私要求及
适用法律。可使用 `--request-delay` 降低请求频率。不要提交 Cookie、会话标识或访问
令牌。

HTTP 诊断信息会隐藏常见凭据请求头。仓库卫生测试会检测已跟踪文本中的已知 Bilibili
会话字段，但如果历史提交曾包含有效密钥，仍需另行审计和处置 Git 历史。

## 开发与测试

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov=scraper --cov-report=term-missing
python -m build
```

测试使用本地夹具和 `pytest-httpx`，无需访问公网。

## 路线图

- 为 GitHub 资源增加分页控制
- 增加各来源的记录数与日期过滤
- 增加流式导出选项
- 增加更多语言的分词策略

## 贡献

欢迎贡献。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，从失败测试开始修改，并让测试
中的网络交互始终使用模拟或本地夹具。

## 许可证

本项目采用 [MIT License](LICENSE)。
