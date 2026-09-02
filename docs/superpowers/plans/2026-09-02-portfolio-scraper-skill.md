# Portfolio Scraper Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个可被其他 Agent 自动发现的 Portfolio Scraper Skill，覆盖安全使用现有 CLI 和扩展数据源适配器的标准流程。

**Architecture:** Skill 以单一 `.trae/skills/portfolio-scraper/SKILL.md` 提供触发条件、决策流程、命令模板、安全约束与开发门禁。仓库测试负责验证目录、frontmatter、描述长度、关键工作流和敏感内容禁令，避免后续文档漂移。

**Tech Stack:** Markdown、YAML frontmatter、Python 标准库、pytest。

---

### Task 1: 添加 Skill 结构回归测试

**Files:**
- Create: `tests/test_skill.py`

- [ ] **Step 1: 写失败测试**

```python
from pathlib import Path
import re

SKILL = Path(".trae/skills/portfolio-scraper/SKILL.md")


def test_skill_has_valid_frontmatter() -> None:
    content = SKILL.read_text(encoding="utf-8")
    match = re.match(r'^---\nname: "([^"]+)"\ndescription: "([^"]+)"\n---\n', content)
    assert match is not None
    assert match.group(1) == "portfolio-scraper"
    assert len(match.group(2)) < 200
    assert "Invoke when" in match.group(2)


def test_skill_covers_required_workflows_without_secrets() -> None:
    content = SKILL.read_text(encoding="utf-8")
    for text in (
        "collect bilibili",
        "collect github",
        "collect rss",
        "collect web",
        "analyze frequency",
        "analyze wordcloud",
        "SourceAdapter",
        "CollectionResult",
        "HttpClient",
    ):
        assert text in content
    assert "SESSDATA=" not in content
    assert "Cookie:" not in content
```

- [ ] **Step 2: 验证测试因 Skill 文件不存在而失败**

Run: `env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev pytest tests/test_skill.py -v`
Expected: FAIL，错误包含 `.trae/skills/portfolio-scraper/SKILL.md` 不存在。

- [ ] **Step 3: 提交测试**

```bash
git add tests/test_skill.py
git commit -m "test: define reusable skill contract"
```

### Task 2: 创建 Portfolio Scraper Skill

**Files:**
- Create: `.trae/skills/portfolio-scraper/SKILL.md`

- [ ] **Step 1: 写合法 frontmatter 与触发说明**

```markdown
---
name: "portfolio-scraper"
description: "Collects and analyzes public data with Portfolio Scraper and guides adapter development. Invoke when agents handle Bilibili, GitHub, RSS, static HTML, or local text analysis."
---
```

正文必须包括：使用边界、来源决策表、安装检查、四类采集命令、两类分析命令、输出验证、退出码、错误分类、安全规则、适配器扩展契约和完整质量命令。

- [ ] **Step 2: 运行 Skill 合约测试**

Run: `env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev pytest tests/test_skill.py -v`
Expected: 2 tests PASS。

- [ ] **Step 3: 运行仓库完整门禁**

Run: `env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis ruff format --check .`
Run: `env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis ruff check .`
Run: `env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis mypy src`
Run: `env -u PYTHONHOME -u PYTHONPATH uv run --isolated --extra dev --extra analysis pytest -q`
Expected: 所有命令退出码为 0。

- [ ] **Step 4: 提交 Skill**

```bash
git add .trae/skills/portfolio-scraper/SKILL.md
git commit -m "feat: add reusable portfolio scraper skill"
```

### Task 3: 发布 Draft PR

**Files:**
- No repository file changes expected.

- [ ] **Step 1: 核对分支与提交**

Run: `git status -sb && git log --oneline main..HEAD`
Expected: 工作树干净，包含设计、计划、测试和 Skill 提交。

- [ ] **Step 2: 推送功能分支**

Run: `git push -u origin feat/portfolio-scraper-skill`
Expected: 远端分支创建成功。

- [ ] **Step 3: 创建 Draft PR**

使用 `gh pr create --draft --base main --head feat/portfolio-scraper-skill`，PR 描述说明触发场景、使用工作流、扩展流程、安全边界和验证结果。

- [ ] **Step 4: 核对 PR**

Run: `gh pr view --json url,isDraft,state,baseRefName,headRefName,statusCheckRollup`
Expected: PR 为 OPEN、Draft，目标 `main`，来源 `feat/portfolio-scraper-skill`。

## 自检结论

- 设计中的 Skill 路径、frontmatter、触发条件、CLI 使用、适配器扩展、错误处理、安全与验收均有对应步骤。
- Skill 不新增运行时代码或依赖。
- 测试先于 Skill 文件创建，符合 TDD。
- 示例使用通用占位符，不包含私有路径或凭据。
