from calls.formatting import format_tasks


def test_compact_tasks_preserve_content_and_other_sections():
    source = (
        "## Саммари\n\nОбсудили сайт.\n\n## Задачи по участникам\n\n### Анна\n\n"
        "- [ ] **Действие:** Подготовить макет. **Результат:** Макет. **Срок:** Пятница. "
        "**Таймкод:** 00:01:04. **Цитата:** «Анна подготовит макет».\n"
        "- [x] Проверить оплату. Результат: Проверка. Срок: Не указан.\n\n"
        "## Полная транскрипция\n\n- [ ] Действие: Не изменять. Срок: Сегодня.\n"
    )
    result = format_tasks(source)
    assert "- [ ] **Задача 1**\n\n  **Действие:** Подготовить макет." in result
    assert "\n\n  **Результат:** Макет.\n\n  **Срок:** Пятница." in result
    assert "  > **Цитата:** «Анна подготовит макет»." in result
    assert "- [x] **Задача 2**" in result
    assert result.split("## Полная транскрипция")[1] == source.split("## Полная транскрипция")[1]
    assert format_tasks(result) == result


def test_new_format_and_plain_tasks_are_unchanged():
    source = "## Задачи по участникам\n\n### Анна\n\n- [ ] **Задача 1**\n\n  **Действие:** Макет.\n\n  **Срок:** Сегодня.\n"
    assert format_tasks(source) == source
