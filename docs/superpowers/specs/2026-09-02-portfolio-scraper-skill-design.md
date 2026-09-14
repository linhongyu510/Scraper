# Portfolio Scraper Skill 设计

## 目标

为仓库新增一个可被其他 Agent 自动发现和复用的 TRAE Skill。Skill 同时覆盖现有 CLI 的安全使用和新适配器的工程化扩展，使 Agent 无需重新阅读整个仓库即可完成采集、导出、分析、故障判断与开发验证。

## 交付物

创建 `.trae/skills/portfolio-scraper/SKILL.md`，包含合法 frontmatter：

- `name`: `portfolio-scraper`
- `description`: 用英文简洁说明能力和触发场景，长度低于 200 字符

Skill 不增加运行时代码、包装脚本或额外依赖。

## 触发场景

Agent 应在以下任务中调用该 Skill：

- 用户要求采集 Bilibili 公开视频与弹幕。
- 用户要求采集 GitHub 仓库、Issue 或 Release。
- 用户要求读取 RSS/Atom 订阅源。
- 用户要求通过 CSS 选择器提取静态网页。
- 用户要求将采集结果导出为 JSONL/CSV。
- 用户要求分析本地 JSONL、CSV 或文本文件的词频或生成词云。
- 用户要求为 Portfolio Scraper 新增或维护数据源适配器。

普通浏览器自动化、动态网页渲染、登录态采集、验证码处理和访问控制绕过不应触发该 Skill。

## 使用工作流

Skill 指导 Agent 按以下顺序执行：

1. 确认数据来源、输入标识、输出格式和用户授权边界。
2. 检查仓库中是否存在 `pyproject.toml` 与 `src/scraper/cli.py`。
3. 优先使用隔离环境运行 CLI，避免依赖宿主 Python 状态。
4. 按来源选择 `collect bilibili`、`collect github`、`collect rss` 或 `collect web`。
5. 对输出文件执行存在性、非空、记录数量和必要字段检查。
6. 需要文本洞察时，再运行 `analyze frequency` 或 `analyze wordcloud`。
7. 如实区分真实网络结果、平台拒绝和固定夹具测试。

## 命令模板

Skill 提供四类采集命令和两类分析命令的通用模板。示例使用 `owner/repo`、`BV...`、`https://example.com` 等占位符，不包含用户路径、真实 Token、Cookie 或一次性数据。

GitHub Token 仅允许从 `GITHUB_TOKEN` 环境变量读取。Skill 不指导 Agent 将认证信息写入命令历史、文件、日志或源代码。

## 适配器扩展

新增适配器时，Skill 要求：

- 遵循 `SourceAdapter` 契约并返回 `CollectionResult`。
- 所有记录通过 `Record` 模型校验。
- 网络访问复用 `HttpClient`。
- 来源特有字段放入 `metadata`。
- 先写失败测试，再实现最小代码。
- 网络测试使用固定夹具，不把模拟结果描述为线上验证。
- 完成 Ruff、mypy、pytest 和构建验证。

Skill 不重复粘贴生产代码，而是指向稳定模块和明确接口，降低代码演进后的文档漂移。

## 错误处理

Skill 将错误分为：

- 配置错误：输入格式、选择器或输出扩展名无效。
- 认证与限速：GitHub `401/403`、远端 `429`。
- 平台拒绝：例如公开接口返回 `412`，不得绕过。
- 解析错误：响应结构、JSON、XML、Feed 或 HTML 不符合预期。
- 部分失败：保留成功记录，报告失败项，退出码为 `2`。
- 整体失败：不产出伪造数据，退出码为 `1`。

## 安全与合规

Skill 只允许处理公开或用户明确授权的数据。禁止提供或执行绕过登录、验证码、robots、付费墙、访问控制、平台风控或速率限制的方案。禁止提交 Cookie、Token、会话标识、个人数据样本或原始抓取结果。

若平台拒绝请求，Agent 应停止该来源的尝试并报告限制，可建议用户在合规网络和授权条件下自行验证。

## 验收

- Skill 文件位于规定目录，frontmatter 可解析。
- 描述同时包含“做什么”和“何时调用”。
- 所有命令与当前 CLI 帮助一致。
- 示例不包含敏感数据或本地绝对路径。
- 覆盖使用、输出验证、错误处理、适配器开发和质量门禁。
- Markdown 无占位符、矛盾和悬空引用。
- 仓库现有测试与静态检查继续通过。
