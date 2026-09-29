"""Make legacy compact task lists readable without rewriting their contents."""

import re

FIELD = re.compile(r"(?:\*\*)?(Действие|Результат|Срок|Таймкод|Цитата):(?:\*\*)?\s*")


def format_tasks(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    output = []
    in_tasks = False
    number = 0
    for line in lines:
        if line.startswith("## "):
            in_tasks = line.strip() == "## Задачи по участникам"
            number = 0
        if in_tasks and line.startswith("### "):
            number = 0
        task = re.match(r"^- \[([ xX])\] (.+?)\s*$", line) if in_tasks else None
        if not task:
            output.append(line)
            continue
        number += 1
        body = task[2]
        fields = list(FIELD.finditer(body))
        # Only convert the old one-line format; leave already formatted tasks alone.
        if len(fields) < 2:
            output.append(line)
            continue
        paragraphs = [f"- [{task[1]}] **Задача {number}**"]
        action = body[: fields[0].start()].strip()
        if action:
            paragraphs.append(f"  **Действие:** {action}")
        for index, field in enumerate(fields):
            end = fields[index + 1].start() if index + 1 < len(fields) else len(body)
            value = body[field.end() : end].strip()
            prefix = "  > " if field[1] in {"Таймкод", "Цитата"} else "  "
            paragraphs.append(f"{prefix}**{field[1]}:** {value}")
        output.append("\n\n".join(paragraphs) + "\n\n")
    return "".join(output)
