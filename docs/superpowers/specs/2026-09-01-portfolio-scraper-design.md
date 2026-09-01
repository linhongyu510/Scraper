# Scraper 作品集工程化改造设计

## 目标

将当前以 Bilibili 弹幕抓取实验脚本为主的仓库，重构为一个可安装、可扩展、可测试的通用采集与文本分析工具。首版强调清晰的适配器边界、可靠的命令行体验、安全的配置方式和可信的测试证据，使项目适合作为 Python 工程能力作品集。

## 成功标准

- 支持 Python 3.10 及以上版本，并可通过标准 Python 包管理工具安装。
- 提供统一 CLI，可采集 Bilibili、GitHub、RSS/Atom 和静态网页。
- 四类适配器输出相同的数据模型，并支持 JSONL 与 CSV 导出。
- 支持对已有数据执行去重、词频统计和词云生成。
- 仓库不再包含有效 Cookie、Token、会话字段或用户身份信息。
- 单元测试不依赖真实网络，覆盖核心模型、适配器解析、导出、分析和 CLI。
- README 能让新用户在五分钟内完成安装并运行第一个示例。

## 非目标

- 不实现登录态自动化或验证码处理。
- 不抓取需要绕过访问控制、付费墙或平台限制的内容。
- 不支持 JavaScript 动态渲染和浏览器自动化。
- 不实现分布式任务、定时调度、数据库存储或 Web 管理界面。
- 不在首版定义 YAML 工作流 DSL。

## 总体架构

项目采用适配器式架构。核心层只定义领域模型、HTTP 行为和适配器契约，不依赖具体来源；每个数据源通过独立适配器实现统一接口。导出与分析消费标准记录，因此新增来源时无需修改下游模块。

```text
CLI
 ├─ collect ─> Adapter ─> HTTP Client ─> Record stream ─> Exporter
 └─ analyze ─> Record/Text loader ─> Analyzer ─> CSV / PNG
```

建议目录：

```text
src/scraper/
├── cli.py
├── models.py
├── exceptions.py
├── http.py
├── adapters/
│   ├── base.py
│   ├── bilibili.py
│   ├── github.py
│   ├── rss.py
│   └── web.py
├── exporters/
│   ├── csv.py
│   └── jsonl.py
└── analysis/
    ├── frequency.py
    └── wordcloud.py
tests/
├── fixtures/
├── test_adapters/
├── test_exporters.py
├── test_analysis.py
└── test_cli.py
```

## 统一数据模型

所有适配器产出 `Record`：

- `source`：来源适配器名称。
- `id`：来源内稳定标识。
- `title`：标题，可为空字符串。
- `url`：规范化原始地址。
- `content`：正文、描述或弹幕文本。
- `author`：作者名称，可为空。
- `published_at`：带时区时间，可为空。
- `metadata`：来源特有的 JSON 可序列化字段。

模型在构造阶段校验必填字段。CSV 导出时将 `metadata` 序列化为 JSON 字符串；JSONL 保留其对象结构。

## 适配器契约

`SourceAdapter` 暴露统一的采集入口，并接收已经配置好的 HTTP 客户端。适配器只负责参数校验、请求构建、响应解析和记录转换，不负责文件写入或终端展示。

### Bilibili

支持通过 BV 号采集公开视频元数据和当前公开弹幕。默认不携带 Cookie；如公开接口确实需要用户配置，只允许通过环境变量读取，并在日志中脱敏。搜索页批量发现不作为首版稳定接口，以降低页面结构变更风险。

### GitHub

支持采集公开仓库信息、Issue 和 Release。匿名请求可直接运行；`GITHUB_TOKEN` 为可选配置，用于提高公开 API 限额。Token 不写入配置文件示例、日志或错误消息。

### RSS / Atom

支持标准 RSS 与 Atom 订阅源，将每个条目转换为记录。解析器应处理缺失作者、发布时间和正文的情况，并优先保留稳定 GUID。

### 静态网页

用户提供 URL 和 CSS 选择器。首版支持列表容器、标题、链接、正文和作者选择器；不执行 JavaScript。相对链接基于页面 URL 解析，并遵守统一超时和响应体大小限制。

## CLI 设计

核心命令：

```bash
scraper collect bilibili --bvid BV... --output data.jsonl
scraper collect github --repo owner/repo --resource issues --output issues.csv
scraper collect rss --url https://example.com/feed.xml --output feed.jsonl
scraper collect web --url https://example.com --item article --title h2 --content p
scraper analyze frequency data.jsonl --top 30 --output frequency.csv
scraper analyze wordcloud data.jsonl --output wordcloud.png
```

CLI 使用非零退出码表示整体失败。批量任务允许部分成功：成功记录正常导出，失败项在结束时汇总，并通过 `--fail-fast` 切换为首次失败即停止。

## HTTP 与错误处理

统一 HTTP 客户端提供：

- 明确的连接和读取超时。
- 仅对连接错误、超时、`429` 和可恢复的 `5xx` 执行有限次数指数退避。
- 尊重 `Retry-After`，不对确定性的 `4xx` 自动重试。
- 可配置请求间隔和清晰的限速提示。
- 响应状态、内容类型和最大响应体校验。
- 不在日志中输出认证头、Cookie 或完整敏感查询参数。

错误分为配置错误、认证错误、限速错误、远端响应错误、解析错误和导出错误。CLI 将异常转换为简洁消息；调试模式才显示堆栈。

## 分析能力

分析模块只读取本地 JSONL、CSV 或纯文本，不依赖在线采集。词频统计支持字段选择、中文分词、停用词文件、最小词长和 Top N。词云为可选依赖；用户未安装分析依赖时，CLI 给出精确安装提示，而不是在基础采集功能启动时失败。

## 安全与合规

删除源码中的硬编码 Cookie、SESSDATA、CSRF 值和账户标识，并加入 `.env.example` 与敏感字段扫描测试。由于敏感值已进入 Git 历史，应在 README 安全说明中提示旧凭据必须视为已泄露并撤销；默认保留历史，不在本次改造中强制重写提交记录。

工具仅面向公开、获授权的数据。README 明确要求遵守目标站点服务条款、robots 规则、API 限额和适用法律，不提供规避验证、风控或访问控制的功能。

## 测试策略

- 使用固定响应夹具验证四个适配器的成功、空数据、缺失字段和畸形响应。
- 使用伪 HTTP 客户端验证超时、重试、`Retry-After` 和敏感信息脱敏。
- 使用契约测试确保所有适配器都返回合法 `Record`。
- 使用临时目录验证 JSONL/CSV round-trip、UTF-8 和 metadata 序列化。
- 验证中文词频、停用词和空输入。
- 使用 CLI runner 验证帮助信息、退出码、错误摘要和基本命令。
- CI 覆盖 Python 3.10、3.11、3.12 和 3.13，并运行格式、静态检查与测试。

真实网络验证与单元测试分离。只有实际执行过的线上探针才能在 README 或发布说明中称为真实验证；固定夹具只作为确定性解析测试证据。

## 仓库整理

旧脚本不继续作为生产入口。可将具有历史价值的实验代码移动到 `examples/legacy/`，同时删除其中的凭据并标注不受支持；重复、明显失效且包含敏感信息的脚本直接删除。抓取结果、Excel、原始文本和大图不放在仓库根目录，精选一个脱敏的小型示例放入 `examples/data/`，展示图片放入 `docs/assets/`。

新增 `pyproject.toml`、`LICENSE`、`.gitignore`、`.env.example`、`CONTRIBUTING.md` 和 GitHub Actions。项目采用 `src` 布局，避免从仓库根目录意外导入。

## README 包装

README 使用英文主文档，并提供 `README.zh-CN.md` 中文版本，顶部互相跳转。结构如下：

1. 项目名称、短定位与简洁徽章。
2. 一张真实生成的词云或终端演示图。
3. 四项核心能力和适用场景。
4. 安装与一分钟快速开始。
5. 四类来源的命令示例。
6. 统一记录格式示例。
7. 架构图与新增适配器教程。
8. 配置、认证与安全说明。
9. 测试命令、项目状态、路线图与贡献方式。
10. 合规声明与许可证。

文档不夸大可用性，不展示未经验证的性能数字，也不把模拟响应测试描述为真实平台兼容性证明。

## 交付边界

本轮交付包括工程重构、四个适配器、两种导出格式、两项离线分析、测试与 CI、仓库清理和中英文 README。发布到 PyPI、创建 GitHub Release、重写 Git 历史和配置仓库 Secrets 不在默认范围内，可在本地验证完成后另行执行。
