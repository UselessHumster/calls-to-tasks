import argparse
from pathlib import Path

from calls.pipeline import process

parser = argparse.ArgumentParser(description="Видео → локальный Whisper → Codex → один Markdown")
parser.add_argument("file", type=Path)
parser.add_argument("--title", default="")
parser.add_argument("--context", default="", help="Участники, дата, термины")
parser.add_argument(
    "--whisper", choices=["tiny", "base", "small", "medium", "large-v3"], default="small"
)
parser.add_argument("--language", default="ru", choices=["ru", "en", "auto"])
parser.add_argument("--model", default="gpt-6-sol")
args = parser.parse_args()
try:
    print(
        process(
            args.file,
            title=args.title,
            context=args.context,
            whisper=args.whisper,
            language=args.language,
            model=args.model,
        )
    )
except Exception as exc:
    parser.exit(1, f"Ошибка: {exc}\n")
