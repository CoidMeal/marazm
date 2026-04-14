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
# ================= ГЛАВНАЯ СТРУКТУРА =================

st.header("📊 История")

# ---------- данные ----------
data = supabase.table("stress").select("*").eq("user", user).execute()
df = pd.DataFrame(data.data)

# ---------- фильтр периода ----------
period = st.selectbox("Период", ["День", "Неделя", "Месяц", "Год", "Все"])

if not df.empty:
    df["time"] = pd.to_datetime(df["time"])
    df["date"] = df["time"].dt.date

    today = datetime.date.today()

    if period == "День":
        df = df[df["date"] >= today - datetime.timedelta(days=1)]
    elif period == "Неделя":
        df = df[df["date"] >= today - datetime.timedelta(days=7)]
    elif period == "Месяц":
        df = df[df["date"] >= today - datetime.timedelta(days=30)]
    elif period == "Год":
        df = df[df["date"] >= today - datetime.timedelta(days=365)]

    df = df[df["type"].isin(["daily", "san"])]

    df_group = df.groupby(["date", "type"])["stress"].mean().reset_index()

    chart = alt.Chart(df_group).mark_line(point=True).encode(
        x=alt.X("date:N", title="Дата"),
        y=alt.Y("stress:Q", scale=alt.Scale(domain=[0,100])),
        color="type:N"
    )

    st.altair_chart(chart, use_container_width=True)

else:
    st.warning("Нет данных")

st.divider()

# ================= НИЖНИЕ ВКЛАДКИ =================
sub1, sub2 = st.tabs(["📅 Актуальное самочувствие", "🧠 Общее настроение"])

# ================= DAILY =================
with sub1:
    st.subheader("Актуальное состояние")

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
        2: "более уставший",
        1: "очень уставший"
    })

    q2 = question("Сон", {
        5: "отличный",
        4: "хороший",
        3: "нормальный",
        2: "плохой",
        1: "очень плохой"
    })

    q3 = question("Боль", {
        5: "нет",
        4: "слабая",
        3: "умеренная",
        2: "сильная",
        1: "очень сильная"
    })

    q4 = question("Стресс", {
        5: "спокоен",
        4: "норм",
        3: "напряжен",
        2: "стресс",
        1: "сильный стресс"
    })

    q5 = question("Настроение", {
        5: "отличное",
        4: "хорошее",
        3: "нормальное",
        2: "плохое",
        1: "очень плохое"
    })

    score = q1 + q2 + q3 + q4 + q5

    if score < 14 or 1 in [q1,q2,q3,q4,q5]:
        color = "purple"
        text = "Высокий риск"
    elif score <= 17 or 2 in [q1,q2,q3,q4,q5]:
        color = "blue"
        text = "Повышенный риск"
    else:
        color = "lightblue"
        text = "Норма"

    st.markdown(f"""
    <div style="
        width:180px;height:180px;border-radius:50%;
        border:10px solid {color};
        display:flex;align-items:center;justify-content:center;
        font-size:30px;margin:auto;">
        {score}
    </div>
    """, unsafe_allow_html=True)

    st.write(text)

    if st.button("💾 Сохранить"):
        supabase.table("stress").insert({
            "user": user,
            "time": str(datetime.datetime.now()),
            "stress": float(100 - score*4),
            "type": "daily"
        }).execute()

        st.success("Сохранено")

# ================= SAN =================
with sub2:
    st.subheader("Общее настроение")

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
        san("Сила", "сильный", "слабый", "s2"),
        san("Активность", "активный", "пассивный", "s3"),
        san("Настроение", "весёлый", "грустный", "s4"),
        san("Энергия", "полный сил", "обессиленный", "s5"),
    ]

    def norm(x):
        return (sum(x)/len(x)+3)/6*100

    stress = 100 - norm(S)

    st.subheader(f"Стресс: {int(stress)}")

    if st.button("💾 Сохранить САН"):
        supabase.table("stress").insert({
            "user": user,
            "time": str(datetime.datetime.now()),
            "stress": float(stress),
            "type": "san"
        }).execute()

        st.success("Сохранено")
