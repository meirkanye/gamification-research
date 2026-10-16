import json
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from google import genai

st.set_page_config(
    page_title="Gamification EduResearch",
    page_icon="🎮",
    layout="wide"
)

# 1. Подключение к облачной БД и ИИ (ключи безопасно хранятся на сервере)
@st.cache_resource
def init_connections():
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        gemini_key = st.secrets["GEMINI_API_KEY"]
        db: Client = create_client(supabase_url, supabase_key)
        ai_client = genai.Client(api_key=gemini_key)
        return db, ai_client, None
    except Exception as e:
        return None, None, str(e)

db, ai_client, conn_error = init_connections()

st.title("🎮 Облачная платформа педагогического исследования: Геймификация в образовании")
st.caption("Сбор данных, геймифицированное тестирование и ИИ-аналитика через API")

if conn_error:
    st.error(
        f"⚠️ Ключи API еще не настроены в Secrets! Ошибка: {conn_error}. "
        "Добавьте SUPABASE_URL, SUPABASE_KEY и GEMINI_API_KEY в настройки Streamlit Cloud."
    )
    st.stop()

tab1, tab2 = st.tabs([
    "🕹️ Квест для обучающегося (Анкета + Тест + Практика)",
    "📊 Кабинет исследователя-педагога (Таблица + ИИ-аналитика + CSV)"
])

# =====================================================================
# ВКЛАДКА 1: ОБУЧАЮЩИЙСЯ (САУАЛНАМА + ТЕСТ + ПРАКТИКАЛЫҚ ТАПСЫРМА)
# =====================================================================
with tab1:
    st.subheader("Прохождение образовательного квеста")

    with st.form("quest_form"):
        student_name = st.text_input("👤 Введите ваше имя или игровой никнейм:")

        st.markdown("### 📋 Часть 1. Анкета (Сауалнама)")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            motivation_type = st.selectbox(
                "Какой игровой элемент мотивирует вас учиться лучше всего?",
                [
                    "Очки опыта (XP) и уровни",
                    "Бейджи, награды и достижения",
                    "Сюжетные квесты и истории",
                    "Рейтинг и соревнование с одногруппниками",
                    "Командное прохождение (кооператив)"
                ]
            )
        with col_a2:
            motivation_score = st.slider(
                "Оцените от 1 до 5, насколько игровые форматы повышают ваш интерес к предмету:",
                min_value=1, max_value=5, value=5
            )

        st.markdown("### 🧠 Часть 2. Тест по основам геймификации (макс. 60 XP)")
        q1 = st.radio(
            "1. Что означает термин «геймификация» в образовании?",
            [
                "Применение игровых механик и элементов в неигровом учебном процессе",
                "Полная замена школьных уроков киберспортом",
                "Изучение языков программирования для создания видеоигр"
            ]
        )
        q2 = st.radio(
            "2. Какая аббревиатура обозначает классическую триаду геймификации?",
            [
                "PBL (Points, Badges, Leaderboards — Очки, Бейджи, Рейтинги)",
                "HTML (HyperText Markup Language)",
                "NPC (Non-Player Character)"
            ]
        )
        q3 = st.radio(
            "3. Какова главная педагогическая цель мгновенной обратной связи в учебных играх?",
            [
                "Поддержание вовлеченности и понимание учеником своих точек роста",
                "Усложнение интерфейса программы",
                "Снижение количества домашних заданий"
            ]
        )

        st.markdown("### 🏆 Часть 3. Практическое задание Босс-уровня (макс. 100 XP от ИИ)")
        open_answer = st.text_area(
            "Опишите свою идею: как превратить обычную тему урока или домашнее задание в увлекательный игровой квест? (Напишите 2–5 предложений на русском или казахском языке)",
            height=120
        )

        submitted = st.form_submit_button("🚀 Отправить ответы и получить разбор от ИИ")

    if submitted:
        if not student_name.strip() or not open_answer.strip():
            st.warning("Пожалуйста, укажите ваше имя и напишите ответ на практическое задание.")
        else:
            # Подсчет баллов за тест (по 20 XP за каждый верный ответ)
            quiz_xp = 0
            if q1.startswith("Применение игровых"):
                quiz_xp += 20
            if q2.startswith("PBL"):
                quiz_xp += 20
            if q3.startswith("Поддержание вовлеченности"):
                quiz_xp += 20

            # Запрос к Gemini API (выполняет сразу 3 функции ИИ из задания)
            prompt = f"""
            Ты — ИИ-ассистент педагогического исследования по теме «Геймификация в образовании».
            Проанализируй открытый ответ обучающегося.
            Любимая механика ученика: {motivation_type}.
            Балл за тест: {quiz_xp} из 60.
            Открытый ответ ученика: "{open_answer}"

            Ответь СТРОГО в формате JSON без markdown-обертки со следующими ключами (на том же языке, на котором написал ученик — русском или казахском):
            {{
              "ai_score": <целое число от 10 до 100 за креативность и педагогическую пользу идеи>,
              "ai_topic": "<краткая категория/тема идеи из 2-3 слов, например: Сюжетный квест / Система наград / Командное соревнование / Викторина>",
              "ai_feedback": "<развернутая поддерживающая обратная связь по открытому ответу ученика (2-3 предложения)>",
              "ai_next_task": "<индивидуальное уровневое задание следующего шага (Базовый, Продвинутый или Экспертный уровень) для развития его идеи>"
            }}
            """

            with st.spinner("🤖 ИИ анализирует ваш ответ, определяет тему и подбирает уровневое задание..."):
                try:
                    response = ai_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config={"response_mime_type": "application/json"}
                    )
                    ai_data = json.loads(response.text)
                    ai_score = int(ai_data.get("ai_score", 80))
                    ai_topic = ai_data.get("ai_topic", "Игровая механика")
                    ai_feedback = ai_data.get("ai_feedback", "Отличная идея для геймификации урока!")
                    ai_next_task = ai_data.get("ai_next_task", "Разработайте правила начисления баллов для вашей игры.")
                except Exception as e:
                    ai_score = 75
                    ai_topic = "Практическая геймификация"
                    ai_feedback = f"Ваш ответ принят! (ИИ временно вернул стандартный разбор: {e})"
                    ai_next_task = "Уровень 2: Придумайте 3 бейджа для награждения участников вашего квеста."

            total_xp = quiz_xp + ai_score
            if total_xp >= 130:
                rank = "👑 Грандмастер Геймификации (Уровень 3)"
            elif total_xp >= 90:
                rank = "⚔️ Архитектор Квестов (Уровень 2)"
            else:
                rank = "🛡️ Искатель Знаний (Уровень 1)"

            # Отображение ответа ИИ в интерфейсе приложения
            st.success(f"🎉 Квест завершен! Набрано: **{total_xp} XP** (Тест: {quiz_xp} XP + ИИ-оценка: {ai_score} XP) | Ваш ранг: **{rank}**")
            
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"🏷️ **Тема вашего ответа (классификация ИИ):** {ai_topic}\n\n💬 **Обратная связь от ИИ:**\n{ai_feedback}")
            with c2:
                st.warning(f"🎯 **Ваше персональное уровневое задание от ИИ:**\n{ai_next_task}")

            # Сохранение результатов в облачную базу данных Supabase
            record = {
                "student_name": student_name.strip(),
                "motivation_type": motivation_type,
                "motivation_score": motivation_score,
                "quiz_xp": quiz_xp,
                "open_answer": open_answer.strip(),
                "ai_topic": ai_topic,
                "ai_score": ai_score,
                "total_xp": total_xp,
                "rank": rank,
                "ai_feedback": ai_feedback,
                "ai_next_task": ai_next_task,
                "teacher_verified": False
            }
            db.table("gamification_results").insert(record).execute()
            st.toast("Данные успешно сохранены в облачной БД Supabase!", icon="☁️")

# =====================================================================
# ВКЛАДКА 2: ПАНЕЛЬ ИССЛЕДОВАТЕЛЯ И ПЕДАГОГА
# =====================================================================
with tab2:
    st.subheader("📊 Управление базой данных исследования, проверка оценок ИИ и экспорт в CSV")

    col_top1, col_top2 = st.columns([3, 1])
    with col_top2:
        if st.button("➕ Загрузить 3 демо-ответа (для показа)"):
            demo_rows = [
                {
                    "student_name": "Алихан С.",
                    "motivation_type": "Сюжетные квесты и истории",
                    "motivation_score": 5,
                    "quiz_xp": 60,
                    "open_answer": "Разделить курс информатики на главы космической одиссеи, где каждая лабораторная работа открывает новую планету.",
                    "ai_topic": "Сюжетный сторителлинг",
                    "ai_score": 95,
                    "total_xp": 155,
                    "rank": "👑 Грандмастер Геймификации (Уровень 3)",
                    "ai_feedback": "Превосходная концепция нарративной геймификации! Сюжет удерживает долгосрочный интерес.",
                    "ai_next_task": "Уровень Эксперт: Опишите финального «Босса» (итоговый проект) для вашей космической карты.",
                    "teacher_verified": True
                },
                {
                    "student_name": "Аружан К.",
                    "motivation_type": "Бейджи, награды и достижения",
                    "motivation_score": 4,
                    "quiz_xp": 40,
                    "open_answer": "Давать цифровые значки за решение задач без ошибок и за помощь одноклассникам на уроке.",
                    "ai_topic": "Система наград и бейджей",
                    "ai_score": 85,
                    "total_xp": 125,
                    "rank": "⚔️ Архитектор Квестов (Уровень 2)",
                    "ai_feedback": "Отличная идея сочетания индивидуальных и социальных достижений.",
                    "ai_next_task": "Уровень Продвинутый: Придумайте условия получения 3 редких секретных бейджей.",
                    "teacher_verified": False
                },
                {
                    "student_name": "Диас М.",
                    "motivation_type": "Рейтинг и соревнование с одногруппниками",
                    "motivation_score": 5,
                    "quiz_xp": 60,
                    "open_answer": "Устраивать в конце каждой недели командный блиц-турнир с таблицей лидеров класса.",
                    "ai_topic": "Командное соревнование",
                    "ai_score": 88,
                    "total_xp": 148,
                    "rank": "👑 Грандмастер Геймификации (Уровень 3)",
                    "ai_feedback": "Командный рейтинг снижает стресс для отдельных учеников и развивает сотрудничество.",
                    "ai_next_task": "Уровень Эксперт: Разработайте механику бонусных очков для отстающих команд.",
                    "teacher_verified": True
                }
            ]
            db.table("gamification_results").insert(demo_rows).execute()
            st.success("Демо-данные успешно добавлены!")
            st.rerun()

    # Чтение данных из облачной БД
    res = db.table("gamification_results").select("*").order("id", desc=True).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # Метрики исследования
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Всего респондентов", len(df))
        m2.metric("Средний интерес (1-5)", f"{df['motivation_score'].mean():.2f}")
        m3.metric("Средний балл ИИ", f"{df['ai_score'].mean():.1f} XP")
        m4.metric("Проверено педагогом", f"{int(df['teacher_verified'].sum())} из {len(df)}")

        st.markdown("#### ✏️ Проверка и корректировка оценок и комментариев ИИ педагогом")
        st.caption("Вы можете прямо в таблице изменить балл ИИ (`ai_score`), тему (`ai_topic`), комментарий (`ai_feedback`), уровневое задание (`ai_next_task`) и поставить галочку проверки (`teacher_verified`).")

        edited_df = st.data_editor(
            df,
            disabled=["id", "created_at", "student_name", "motivation_type", "motivation_score", "quiz_xp", "open_answer", "total_xp"],
            use_container_width=True,
            num_rows="fixed"
        )

        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            if st.button("💾 Сохранить исправления педагога в БД"):
                for _, row in edited_df.iterrows():
                    new_total = int(row["quiz_xp"]) + int(row["ai_score"])
                    db.table("gamification_results").update({
                        "ai_topic": str(row["ai_topic"]),
                        "ai_score": int(row["ai_score"]),
                        "total_xp": new_total,
                        "ai_feedback": str(row["ai_feedback"]),
                        "ai_next_task": str(row["ai_next_task"]),
                        "teacher_verified": bool(row["teacher_verified"])
                    }).eq("id", row["id"]).execute()
                st.success("✅ Все исправления педагога сохранены в облачной базе данных!")
                st.rerun()

        with btn_col2:
            csv_bytes = edited_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Скачать таблицу результатов (CSV)",
                data=csv_bytes,
                file_name="gamification_research_data.csv",
                mime="text/csv"
            )

        with btn_col3:
            # 4-я функция ИИ: объяснение сводных результатов исследования
            if st.button("🤖 ИИ-интерпретация сводных результатов"):
                summary_prompt = f"""
                Ты — научный консультант по педагогическим исследованиям.
                Проанализируй сводные результаты опроса и тестирования по теме «Геймификация в образовании»:
                - Количество участников: {len(df)}
                - Средняя оценка мотивации (из 5): {df['motivation_score'].mean():.2f}
                - Распределение предпочитаемых механик: {df['motivation_type'].value_counts().to_dict()}
                - Темы предложенных учениками идей (классификация ИИ): {df['ai_topic'].value_counts().to_dict()}
                - Средний итоговый балл XP: {df['total_xp'].mean():.1f}

                Напиши краткое аналитическое заключение (на русском и казахском языках) для научного отчета:
                1. Главные выводы по мотивации обучающихся.
                2. Какие игровые механики и темы лидируют.
                3. Педагогические рекомендации.
                """
                with st.spinner("ИИ формирует сводный научный вывод по выборке..."):
                    summary_resp = ai_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=summary_prompt
                    )
                    st.session_state["ai_summary_report"] = summary_resp.text

        if "ai_summary_report" in st.session_state:
            st.markdown("---")
            st.markdown("### 🧠 Сводная интерпретация результатов от ИИ (Жиынтық нәтижелерді түсіндіру)")
            st.info(st.session_state["ai_summary_report"])
    else:
        st.info("База данных пока пуста. Пройдите квест на первой вкладке или нажмите кнопку «➕ Загрузить 3 демо-ответа» выше.")
