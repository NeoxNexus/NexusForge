from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nexusforge.config import Config
from nexusforge.models import IdeaRecord
from nexusforge.storage import list_ideas, save_idea, write_markdown
from nexusforge.taskboard import create_task_card
from nexusforge.timeutil import current_timestamp


@dataclass
class IncubationResult:
    idea: IdeaRecord
    report_path: Path
    task_card_id: str | None
    task_card_location: str | None


def select_new_ideas(config: Config, top: int = 3, preferred_tag: str | None = None) -> list[IdeaRecord]:
    ideas = [idea for idea in list_ideas(config.ideas_dir) if idea.status == "New"]
    if preferred_tag:
        preferred = [idea for idea in ideas if preferred_tag in idea.tags]
        others = [idea for idea in ideas if preferred_tag not in idea.tags]
        ideas = preferred + others
    return ideas[:top]


def find_idea_by_slug(config: Config, slug: str) -> IdeaRecord | None:
    for idea in list_ideas(config.ideas_dir):
        if idea.slug == slug:
            return idea
    return None


def incubate_ideas(
    config: Config,
    top: int = 3,
    preferred_tag: str | None = None,
    slug: str | None = None,
    create_task: bool = False,
    mark_done: bool = False,
) -> list[IncubationResult]:
    config.ensure_directories()
    if slug:
        target = find_idea_by_slug(config, slug)
        ideas = [target] if target and target.status == "New" else []
    else:
        ideas = select_new_ideas(config, top=top, preferred_tag=preferred_tag)

    results: list[IncubationResult] = []
    for idea in ideas:
        result = incubate_single_idea(
            config=config,
            idea=idea,
            create_task=create_task,
            mark_done=mark_done,
        )
        results.append(result)
    return results


def incubate_single_idea(
    config: Config,
    idea: IdeaRecord,
    create_task: bool = False,
    mark_done: bool = False,
) -> IncubationResult:
    sections = build_sections(idea)
    report_path = config.incubations_dir / f"{idea.slug}-incubation.md"
    front_matter = {
        "title": f"{idea.title} Incubation",
        "idea_slug": idea.slug,
        "generated_at": current_timestamp(config.vault_timezone),
        "status": "Done" if mark_done else "Incubating",
        "source_idea": str(idea.path) if idea.path else str(config.ideas_dir / f"{idea.slug}.md"),
        "tags": idea.tags,
    }
    report_body = build_markdown_report(idea, sections)
    write_markdown(report_path, front_matter, report_body)

    task_card_id: str | None = None
    task_card_location: str | None = None
    if create_task:
        task_card_id, task_card_location = create_task_card(
            config=config,
            idea=idea,
            report_path=report_path,
            action_items=sections["action_items"],
        )

    idea.status = "Done" if mark_done else "Incubating"
    idea.updated_at = current_timestamp(config.vault_timezone)
    idea.incubation_report = str(report_path)
    if task_card_id:
        idea.task_card_id = task_card_id
    save_idea(config.ideas_dir, idea)

    return IncubationResult(
        idea=idea,
        report_path=report_path,
        task_card_id=task_card_id,
        task_card_location=task_card_location,
    )


def build_markdown_report(idea: IdeaRecord, sections: dict[str, object]) -> str:
    return "\n".join(
        [
            f"# Idea Forge: {idea.title}",
            "",
            "## 1. Idea Restatement",
            "",
            str(sections["restatement"]),
            "",
            "## 2. Problem",
            "",
            format_bullets(sections["problem"]),
            "",
            "## 3. Target Users",
            "",
            format_bullets(sections["target_users"]),
            "",
            "## 4. Value",
            "",
            format_bullets(sections["value"]),
            "",
            "## 5. Feasibility",
            "",
            f"- Score: {sections['feasibility_score']}/10",
            f"- Rationale: {sections['feasibility_rationale']}",
            "",
            "## 6. Risks",
            "",
            format_bullets(sections["risks"]),
            "",
            "## 7. Resources",
            "",
            format_bullets(sections["resources"]),
            "",
            "## 8. Plan",
            "",
            "### Goals",
            "",
            format_bullets(sections["goals"]),
            "",
            "### Milestones",
            "",
            format_numbered(sections["milestones"]),
            "",
            "### Dependencies",
            "",
            format_bullets(sections["dependencies"]),
            "",
            "### Action Items",
            "",
            format_bullets(sections["action_items"]),
            "",
            "### Exit Conditions",
            "",
            format_bullets(sections["exit_conditions"]),
            "",
            "## 9. SCAMPER Variants",
            "",
            format_numbered(sections["scamper"]),
        ]
    ).strip()


def format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def format_numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def build_sections(idea: IdeaRecord) -> dict[str, object]:
    text = idea.description
    lowered = text.lower()
    tags = idea.tags

    problem = pick_problem_points(lowered)
    target_users = pick_target_users(lowered, tags)
    value = pick_value_points(lowered, tags)
    risks = pick_risks(lowered)
    resources = pick_resources(lowered)
    goals = [
        f"把“{idea.title}”从一句话想法转成可以在两周内验证的方案。",
        "建立可重复的捕捉、评估和执行闭环。",
        "优先保留本地数据与可回滚实现路径。",
    ]
    milestones = [
        "定义输入、状态流转和最小数据模型，时间估计 0.5 天。",
        "实现首版捕捉与持久化流程，时间估计 0.5 天。",
        "完成孵化模板、评估逻辑和 markdown 报告输出，时间估计 1 天。",
        "补任务板集成、提醒和失败重试，时间估计 0.5 天。",
        "拿 3 个真实 idea 做试运行并调参，时间估计 0.5 天。",
    ]
    dependencies = [
        "本地 Python 3 环境。",
        "Obsidian vault 或兼容 markdown 目录。",
        "如果要直连外部任务板，需要可用 webhook/API 凭证。",
    ]
    action_items = [
        "确认触发渠道与输入格式，避免 capture 前缀歧义。",
        "先用 3 个真实 idea 跑验证，检查标题、标签和状态更新是否符合预期。",
        "为最有价值的一个变体定义成功指标，并在任务板建卡跟踪。",
    ]
    exit_conditions = [
        "能稳定捕捉并写入 vault。",
        "至少一个 idea 生成可执行计划且状态更新成功。",
        "任务板或 outbox 中存在可追踪卡片。",
        "用户能在 5 分钟内理解下一步行动。",
    ]

    score = 7
    if any(keyword in lowered for keyword in ("telegram", "discord", "api", "webhook", "bot")):
        score -= 1
    if any(keyword in lowered for keyword in ("ai", "agent", "自动")):
        score -= 1
    if any(keyword in lowered for keyword in ("本地", "obsidian", "markdown", "脚本")):
        score += 1
    score = max(1, min(10, score))

    restatement = (
        f"这个 idea 的核心是：{idea.description}。"
        " 孵化目标不是一次做满，而是先找出最短闭环，把价值、风险和行动项显式化。"
    )

    scamper = build_scamper_variants(idea)

    return {
        "restatement": restatement,
        "problem": problem,
        "target_users": target_users,
        "value": value,
        "feasibility_score": score,
        "feasibility_rationale": feasibility_rationale(score),
        "risks": risks,
        "resources": resources,
        "goals": goals,
        "milestones": milestones,
        "dependencies": dependencies,
        "action_items": action_items,
        "exit_conditions": exit_conditions,
        "scamper": scamper,
    }


def pick_problem_points(lowered: str) -> list[str]:
    points = [
        "零散想法容易在上下文切换后丢失，导致有价值的方向无法累计。",
        "没有统一评估模板时，idea 很难快速判断先做什么、先不做什么。",
    ]
    if any(keyword in lowered for keyword in ("debug", "代码", "bug", "开发")):
        points.append("工程类问题往往卡在定位和复现，缺少结构化拆解会放大调试成本。")
    if any(keyword in lowered for keyword in ("ai", "agent", "自动")):
        points.append("自动化方案如果没有边界定义，容易在效果不稳定和维护成本之间失衡。")
    if any(keyword in lowered for keyword in ("obsidian", "notion", "知识", "vault")):
        points.append("知识库类工具的价值依赖持续回写，否则只会增加输入负担。")
    return points[:5]


def pick_target_users(lowered: str, tags: list[str]) -> list[str]:
    users = [
        "个人开发者，需要把临时想法快速沉淀成可执行项目。",
        "小团队中的 Builder，希望在不引入重流程的前提下做轻量验证。",
    ]
    if "AI工具" in tags or "开发效率" in tags:
        users.append("经常在编码、调试、自动化之间切换的技术型创作者。")
    if "知识管理" in tags:
        users.append("依赖 Obsidian/Notion 管理知识和待办的重度笔记用户。")
    if any(keyword in lowered for keyword in ("提醒", "任务", "heartbeat")):
        users.append("需要外部提醒才能保持执行节奏的自驱型个体。")
    return users[:4]


def pick_value_points(lowered: str, tags: list[str]) -> list[str]:
    value = [
        "把一句话想法转成结构化方案，缩短从灵感到执行的时间。",
        "让想法的优先级、风险和资源消耗可比较，而不是靠感觉排序。",
    ]
    if "开发效率" in tags:
        value.append("减少重复调试与重复思考，把精力用在验证真正有价值的部分。")
    if "AI工具" in tags:
        value.append("为后续接入智能代理留出统一入口，避免每次都重做工作流。")
    if any(keyword in lowered for keyword in ("本地", "obsidian", "markdown")):
        value.append("本地优先意味着数据更可控，也更容易回滚与审计。")
    return value[:5]


def pick_risks(lowered: str) -> list[str]:
    risks = [
        "标题、标签或优先级判断可能不准确，导致后续筛选偏差。",
        "如果孵化模板过于模板化，输出会看起来完整但不够可执行。",
    ]
    if any(keyword in lowered for keyword in ("telegram", "discord", "api", "webhook", "bot")):
        risks.append("外部 API 变更、凭证失效或限流会影响自动捕捉与追踪。")
    if any(keyword in lowered for keyword in ("ai", "agent", "自动")):
        risks.append("自动化建议可能出现幻觉或误判，需要保留人工确认点。")
    return risks[:5]


def pick_resources(lowered: str) -> list[str]:
    resources = [
        "Python 脚本与本地运行环境。",
        "Markdown vault 与状态字段约定。",
        "简单日志与失败重试机制。",
    ]
    if any(keyword in lowered for keyword in ("telegram", "discord", "api", "webhook", "bot")):
        resources.append("Bot token、webhook 地址或任务板 API 凭证。")
    if any(keyword in lowered for keyword in ("ai", "agent", "模型")):
        resources.append("后续如果接入模型，需要额外预算 token 成本与评估机制。")
    return resources[:5]


def feasibility_rationale(score: int) -> str:
    if score >= 8:
        return "本地闭环清晰、外部依赖少，适合先做 MVP 验证。"
    if score >= 6:
        return "方案可做，但要先控制范围，避免在集成细节上超支。"
    return "依赖和不确定性偏多，建议先砍掉外围功能再验证核心价值。"


def build_scamper_variants(idea: IdeaRecord) -> list[str]:
    return [
        f"Substitute：把人工整理阶段替换为自动标签和状态建议，仅保留最终确认给用户。",
        f"Combine：将“{idea.title}”和 NexusRhythm 的节奏追踪合并，让行动项自动进入每日执行流。",
        f"Adapt：把当前流程适配到团队共享 backlog，而不是只服务单人 idea vault。",
        f"Modify：缩小成只处理 top 1 高价值 idea 的轻量版本，先验证反馈速度。",
    ]
