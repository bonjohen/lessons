"""Prompt builder — constructs grounded prompts from retrieved context."""

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using a lessons-learned library. "
    "Your answers must be grounded in the provided lesson context.\n\n"
    "Rules:\n"
    "1. Only use information from the provided lesson excerpts to answer.\n"
    "2. Cite lessons by title when referencing their content.\n"
    "3. If the provided context does not contain enough information to answer well, say so clearly.\n"
    "4. Keep answers concise and actionable.\n"
    "5. At the end of your answer, list the relevant lessons with their URLs in this format:\n"
    "   **Sources:**\n"
    "   - [Lesson Title](/lessons/lesson-id)\n"
)


def build_chat_messages(query: str, chunks: list[dict]) -> list[dict]:
    """Build chat messages with retrieved context.

    Args:
        query: The user's question.
        chunks: Retrieved chunks with chunk_text, title, lesson_url, heading_path.

    Returns:
        List of message dicts for the LLM.
    """
    context_parts = []
    seen_lessons = set()

    for chunk in chunks:
        lesson_id = chunk.get("lesson_id", "")
        title = chunk.get("title", "Unknown")
        heading = chunk.get("heading_path", "")
        text = chunk.get("chunk_text", "")
        url = chunk.get("lesson_url", "")

        if lesson_id not in seen_lessons:
            seen_lessons.add(lesson_id)

        context_parts.append(f"--- Lesson: {title} | Section: {heading} | URL: {url} ---\n{text}")

    context_block = "\n\n".join(context_parts)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here are relevant lesson excerpts:\n\n{context_block}\n\n---\n\nQuestion: {query}",
        },
    ]
