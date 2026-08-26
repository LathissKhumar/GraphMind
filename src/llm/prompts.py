from __future__ import annotations

GRAPH_RAG_SYSTEM_PROMPT = (
    "You are a codebase reasoning assistant. Answer using graph relationships, "
    "entity links, and concise explanations. If graph evidence is weak, say so."
)

LLM_FULL_SYSTEM_PROMPT = (
    "You are a senior software engineer. Provide direct, accurate, and concise "
    "answers for open-ended code questions."
)


def build_graph_rag_prompt(question: str, context: str = "") -> str:
    parts = [GRAPH_RAG_SYSTEM_PROMPT, f"Question: {question}"]
    if context.strip():
        parts.append(f"Context: {context.strip()}")
    return "\n\n".join(parts)


def build_llm_full_prompt(question: str, context: str = "") -> str:
    parts = [LLM_FULL_SYSTEM_PROMPT, f"Question: {question}"]
    if context.strip():
        parts.append(f"Context: {context.strip()}")
    return "\n\n".join(parts)


def build_rag_prompt(question: str, graph_context: str = "") -> str:
    """Build RAG prompt for graph-enhanced queries."""
    parts = [GRAPH_RAG_SYSTEM_PROMPT, f"Question: {question}"]
    if graph_context.strip():
        parts.append(f"Graph Context: {graph_context.strip()}")
    return "\n\n".join(parts)


def build_full_prompt(question: str) -> str:
    """Build full prompt for LLM-only queries."""
    return f"{LLM_FULL_SYSTEM_PROMPT}\n\nQuestion: {question}"
