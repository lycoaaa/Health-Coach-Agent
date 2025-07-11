WHO_GUIDE = """
- 每周中等强度运动 ≥ 150 分钟
- 每日步数 ≥ 8 000
- 每日蔬果 ≥ 5 份
- 每日饮水 ≥ 1 500 ml
- 良好睡眠 7 – 9 小时
- 情绪评分 ≥ 4 / 5
"""

SYSTEM_INSTRUCT = """
你是一名充满活力的私人健康教练。请基于【个人档案】和【本周统计】给出反馈，
并 **只回复一段合法 JSON**（开头 { 结尾 }，不要 ```json 或多余文字）。

JSON 结构：
{
  "summary": "≤ 80 字，用第二人称，总结亮点与改进点，并插入 1 个贴切 emoji",
  "action_items": [
    {
      "goal":   "目标名称（≤ 6 字）",
      "target": "建议目标值",
      "period_weeks": 1-8,            # 完成周期，整数，单位=周
      "motivation": "一句激励（≤ 20 字，结尾带 💪 或 🔥 等 emoji）"
    },
    ...  # 共 3 条
  ]
}
禁止输出除 JSON 之外的任何文字！
"""

def build_prompt(stat_table_md: str, personal_md: str | None = None) -> str:
    personal_block = (
        f"## 个人档案\n{personal_md}\n\n" if personal_md else ""
    )
    return (
        f"{SYSTEM_INSTRUCT}\n\n"
        f"{personal_block}"
        "## 本周统计\n"
        f"{stat_table_md}\n\n"
        "## WHO 指南\n"
        f"{WHO_GUIDE}\n"
    )
