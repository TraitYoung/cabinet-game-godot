"""将 Hindsight 记忆、最近对话与本轮输入拼装为 Bina 的上下文。"""


def compose_user_message(
    base_user_status: str,
    *,
    recent_history: list[str] | None = None,
    long_term_context: str = "",
) -> str:
    parts = [long_term_context.strip()]
    # ChatHistory.format_for_prompt budgets each speaker before joining the turn.
    history = "\n".join((recent_history or [])[-5:])
    if history:
        parts.append("【最近对话】\n" + history)
    parts.append(base_user_status.strip())
    return "\n\n".join(part for part in parts if part)
