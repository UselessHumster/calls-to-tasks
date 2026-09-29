import tempfile
from pathlib import Path

import streamlit as st
from filelock import Timeout

from calls.formatting import format_tasks
from calls.launcher import default_command
from calls.pipeline import DATA, process

st.set_page_config(page_title="После созвона", page_icon="✳️", layout="wide")
st.html((Path(__file__).parent / "style.css").read_text())
st.html("""
<div class="topbar">
  <div class="wordmark"><span class="brand-icon">✳</span> после созвона<span class="brand-dot">.</span></div>
  <div class="local-badge"><span></span> Твоё локальное пространство</div>
</div>
<section class="hero">
  <div class="eyebrow">МЕНЬШЕ ПЕРЕСЛУШИВАТЬ. БОЛЬШЕ ДЕЛАТЬ.</div>
  <h1>Созвон закончился.<br><span>Всё важное — осталось.</span></h1>
  <p>Преврати час разговоров в понятный план.<br>Саммари, решения и задачи — в одном файле.</p>
  <div class="hero-wave" aria-hidden="true">
    <i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i>
    <span>РАЗГОВОР → ЯСНОСТЬ</span>
  </div>
</section>
<div class="steps"><span><b>01</b> Добавь запись</span><em>→</em><span><b>02</b> Дополни контекст</span><em>→</em><span><b>03</b> Забери протокол</span></div>
""")

main, aside = st.columns([1.6, 1], gap="large")
with main:
    with st.container(border=True, key="recording"):
        st.html(
            '<div class="section-title"><span class="step-number">01</span><h2>Твой следующий план</h2></div>'
        )
        mode = st.radio(
            "Источник записи",
            ["Загрузить файл", "Файл на компьютере"],
            horizontal=True,
            label_visibility="collapsed",
        )
        uploaded = None
        source_path = ""
        if mode == "Загрузить файл":
            uploaded = st.file_uploader(
                "Перетащи сюда запись созвона",
                type=[
                    "mp4",
                    "mov",
                    "mkv",
                    "webm",
                    "m4v",
                    "mp3",
                    "wav",
                    "m4a",
                    "ogg",
                    "flac",
                    "aac",
                ],
            )
            st.caption(
                "Видео или аудио · до 2 ГБ. Большой файл можно открыть по пути с компьютера."
            )
        else:
            source_path = st.text_input("Полный путь к записи", placeholder="/Users/…/созвон.mp4")
            st.caption("Для больших файлов: запись читается с диска без загрузки в браузер.")
        st.html('<div class="form-divider"></div>')
        title = st.text_input(
            "Как назовём созвон?", placeholder="Например, планы на большую пятницу"
        )
        context = st.text_area(
            "Кто участвовал и что нужно знать?",
            placeholder="Анна — дизайн, Илья — разработка. Обсуждали запуск сайта. Можно добавить дату и термины проекта…",
            height=110,
        )
        st.caption("Необязательно, но помогает точнее понять имена и договорённости.")
        with st.expander("Тонкая настройка"):
            whisper = st.selectbox(
                "Локальная модель", ["small", "medium", "large-v3", "tiny", "base"]
            )
            st.caption(
                "small — стартовый вариант. medium / large-v3 требуют больше памяти и времени. При первом запуске модель скачивается."
            )
            language = st.selectbox("Язык записи", ["ru", "auto", "en"])
            model = st.text_input("Модель Codex", value="gpt-6-sol")
            command_name = st.text_input("Команда или рабочий алиас", value=default_command())
            st.caption(
                "По умолчанию codex. Для рабочего аккаунта можно указать, например, codex-s."
            )
        run = st.button(
            "Собрать протокол  ↗",
            type="primary",
            disabled=not (uploaded or source_path.strip()),
            width="stretch",
        )
        st.html('<div class="button-note">Одна запись. Один аккуратный Markdown.</div>')

with aside:
    st.html("""
    <div class="preview-heading"><span class="mini-star">✳</span> НА ВЫХОДЕ — ПОРЯДОК</div>
    <div class="document-preview">
      <div class="document-top"><span class="file-icon">↳</span><span>план-на-пятницу.md</span><span class="sample-badge">ПРИМЕР</span></div>
      <h3>Итак, договорились.</h3>
      <p class="preview-summary">Запускаем новую главную страницу.<br>Сначала макет, потом проверка оплаты.</p>
      <div class="document-rule"></div>
      <div class="tiny-label">ЗАДАЧИ ПО УЧАСТНИКАМ</div>
      <div class="task"><span class="fake-check"></span><div><strong>Подготовить макет</strong><div class="task-meta"><span class="avatar purple">А</span> Анна <span class="deadline">к пятнице</span></div></div></div>
      <div class="task"><span class="fake-check"></span><div><strong>Проверить интеграцию оплаты</strong><div class="task-meta"><span class="avatar orange">И</span> Илья <span class="deadline">в понедельник</span></div></div></div>
      <div class="quote"><span>00:07</span> «Илья проверит интеграцию с оплатой…»</div>
      <div class="document-bottom"><span>+ решения и открытые вопросы</span><span>+ полная транскрипция</span></div>
    </div>
    <div class="trust-note"><span>↗</span><div><strong>Каждая задача — с основанием</strong><p>Таймкоды и цитаты помогают вернуться к разговору. Если исполнитель неясен, пометим «Уточнить».</p></div></div>
    <div class="privacy-note"><span class="status-dot"></span><p>Аудио остаётся на компьютере.<br>Текст и контекст отправляются в Codex для саммари.</p></div>
    """)

if run:
    st.session_state.pop("result", None)
    with st.status("Обработка записи…", expanded=True) as status:
        stage = st.empty()
        try:
            if not model.strip():
                raise ValueError("Укажи модель Codex.")
            if not command_name.strip():
                raise ValueError("Укажи команду Codex.")
            options = dict(
                title=title,
                context=context,
                whisper=whisper,
                language=language,
                model=model.strip(),
                command_name=command_name.strip(),
                progress=stage.write,
            )
            if uploaded is not None:
                DATA.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix="upload-", dir=DATA) as temporary:
                    source = Path(temporary) / Path(uploaded.name).name
                    with source.open("wb") as f:
                        f.write(uploaded.getbuffer())
                    result = process(source, **options)
            else:
                result = process(Path(source_path.strip()), **options)
            st.session_state["result"] = str(result)
            status.update(label="Протокол готов", state="complete", expanded=False)
        except Timeout:
            status.update(label="Эта запись уже обрабатывается в другой вкладке", state="error")
        except Exception as exc:
            status.update(label="Не удалось завершить обработку", state="error")
            st.error(str(exc))
            st.info("Повтори запуск: сохранённая транскрипция будет использована автоматически.")

if st.session_state.get("result"):
    result = Path(st.session_state["result"])
    if result.exists():
        markdown = format_tasks(result.read_text(encoding="utf-8"))
        st.divider()
        st.subheader("Готово. Можно действовать ✳")
        st.download_button(
            "Забрать протокол .md  ↓",
            markdown,
            file_name=result.name,
            mime="text/markdown",
            type="primary",
        )
        st.caption(f"Сохранено: {result}")
        st.markdown(markdown)
