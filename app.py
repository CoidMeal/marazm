import streamlit as st
import pandas as pd
import datetime
import altair as alt
from supabase import create_client

# ---------- SUPABASE ----------
url = "https://wthspnkihisgbteoweva.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0aHNwbmtpaGlzZ2J0ZW93ZXZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxMDgyMDksImV4cCI6MjA5MTY4NDIwOX0.13cxHk1mXrG3eRnIpnQFeGOulynEp4JiQJxg84rPZlo"
supabase = create_client(url, key)
st.set_page_config(page_title="stressctrl", layout="wide")
# ================= ВХОД =================
if "user" not in st.session_state:
    st.title("Анализ вашего самочувствия")

    name = st.text_input("Введите имя")

    if st.button("🚀 Начать", use_container_width=True):
        if name:
            st.session_state.user = name
            st.rerun()
        else:
            st.warning("Введите имя")

    st.stop()

user = st.session_state.user

# ================= ВКЛАДКИ =================
tab1, tab2, tab3 = st.tabs(["📋 Тесты", "📊 График", "🎯 Сегодня"])

# ================= ТЕСТЫ =================

    # ---------- SAN ----------
with tab1:
    sub1, sub2 = st.tabs(["📅 Ежедневный тест", "🧠 САН"])

    # ================= DAILY =================
    with sub1:
        st.header("Ежедневный тест")

        def question(title, options):
            return st.radio(
                title,
                list(options.keys()),
                format_func=lambda x: f"{x} — {options[x]}"
            )

        q1 = question("Усталость", {
            5: "полностью отдохнувший",
            4: "отдохнувший",
            3: "нормально",
            2: "более уставший, чем обычно",
            1: "всегда уставший"
        })

        q2 = question("Качество сна", {
            5: "полностью выспался",
            4: "хороший сон",
            3: "трудности с засыпанием",
            2: "прерывистый сон",
            1: "бессонница"
        })

        q3 = question("Мышечная боль", {
            5: "отличное самочувствие",
            4: "хорошее самочувствие",
            3: "нормально",
            2: "напряжение и скованность",
            1: "сильная боль"
        })

        q4 = question("Уровень стресса", {
            5: "полностью расслаблен",
            4: "расслаблен",
            3: "нормальный уровень",
            2: "стресс",
            1: "сильный стресс"
        })

        q5 = question("Настроение", {
            5: "отличное настроение",
            4: "хорошее",
            3: "меньше интереса",
            2: "раздражён",
            1: "сильно раздражён"
        })

        score = q1 + q2 + q3 + q4 + q5

        # ---------- ОЦЕНКА ----------
        if score < 14 or 1 in [q1,q2,q3,q4,q5]:
            color = "purple"
            text = "Высокий риск"
        elif score <= 17 or 2 in [q1,q2,q3,q4,q5]:
            color = "blue"
            text = "Повышенный риск"
        else:
            color = "lightblue"
            text = "Нормальное состояние"

        st.markdown(f"""
        <div style="
            width:200px;height:200px;border-radius:50%;
            border:12px solid {color};
            display:flex;align-items:center;justify-content:center;
            font-size:35px;margin:auto;">
            {score}
        </div>
        """, unsafe_allow_html=True)

        st.subheader(text)

        if st.button("💾 Сохранить ежедневный", use_container_width=True):
            try:
                supabase.table("stress").insert({
                    "user": user,
                    "time": str(datetime.datetime.now()),
                    "stress": float(100 - score*4),
                    "type": "daily"
                }).execute()

                st.success("Сохранено")

            except Exception as e:
                st.error(e)

    # ================= SAN =================
    with sub2:
        st.header("САН")

        scale = [-3,-2,-1,0,1,2,3]

        def san(q, left, right, key):
            return st.select_slider(
                q,
                options=scale,
                value=0,
                key=key,
                format_func=lambda x: f"{left} ← {x} → {right}"
            )

        S = [
            san("Самочувствие", "хорошее", "плохое", "s1"),
            san("Чувствую себя", "сильным", "слабым", "s2"),
            san("Состояние", "активный", "пассивный", "s3"),
            san("Подвижность", "подвижный", "малоподвижный", "s4"),
            san("Настроение", "весёлый", "грустный", "s5"),
            san("Настроение 2", "хорошее", "плохое", "s6"),
            san("Работоспособность", "работоспособный", "разбитый", "s7"),
            san("Энергия", "полный сил", "обессиленный", "s8"),
            san("Скорость", "быстрый", "медлительный", "s9"),
            san("Активность", "деятельный", "бездеятельный", "s10"),
        ]

        def norm(x):
            return (sum(x)/len(x)+3)/6*100

        stress = 100 - norm(S)

        st.subheader(f"Стресс: {int(stress)}")

        if st.button("💾 Сохранить САН", use_container_width=True):
            try:
                supabase.table("stress").insert({
                    "user": user,
                    "time": str(datetime.datetime.now()),
                    "stress": float(stress),
                    "type": "san"
                }).execute()

                st.success("Сохранено")

            except Exception as e:
                st.error(e)

# ================= ГРАФИК =================
with tab2:
    st.header("График")

    data = supabase.table("stress").select("*").eq("user", user).execute()
    df = pd.DataFrame(data.data)

    if not df.empty:
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date

        # группируем отдельно
        df_day = df.groupby(["date", "type"])["stress"].mean().reset_index()

        chart = alt.Chart(df_day).mark_line(point=True).encode(
            x=alt.X("date:N", title="День"),
            y=alt.Y("stress:Q", scale=alt.Scale(domain=[0,100])),
            color="type:N",
            tooltip=["date", "stress", "type"]
        )

        st.altair_chart(chart, use_container_width=True)

# ================= СЕГОДНЯ =================
with tab3:
    st.header("Сегодня")

    data = supabase.table("stress").select("*").eq("user", user).execute()
    df = pd.DataFrame(data.data)

    if not df.empty:
        df["time"] = pd.to_datetime(df["time"])
        today = datetime.date.today()

        df_today = df[df["time"].dt.date == today]

        # ---------- 1. СРЕДНИЙ ЗА ДЕНЬ ----------
        if not df_today.empty:
            avg = df_today["stress"].mean()

            if avg >= 70:
                color = "red"
            elif avg >= 50:
                color = "orange"
            else:
                color = "green"

            st.subheader("Средний за день")

            st.markdown(f"""
            <div style="
                width:200px;height:200px;border-radius:50%;
                border:12px solid {color};
                display:flex;align-items:center;justify-content:center;
                font-size:35px;margin:auto;">
                {int(avg)}
            </div>
            """, unsafe_allow_html=True)

        # ---------- 2. ПОСЛЕДНИЙ САН ----------
        df_san = df[df["type"] == "san"]

        if not df_san.empty:
            last_san = df_san.sort_values("time").iloc[-1]["stress"]

            if last_san >= 70:
                color = "red"
            elif last_san >= 50:
                color = "orange"
            else:
                color = "green"

            st.subheader("Последний САН")

            st.markdown(f"""
            <div style="
                width:200px;height:200px;border-radius:50%;
                border:12px solid {color};
                display:flex;align-items:center;justify-content:center;
                font-size:35px;margin:auto;">
                {int(last_san)}
            </div>
            """, unsafe_allow_html=True)
