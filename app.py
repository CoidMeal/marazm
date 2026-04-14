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

# ================= ПЕРЕКЛЮЧАТЕЛЬ =================
mode = st.segmented_control(
    "Раздел",
    ["📊 История", "🧪 Тесты"],
    default="🧪 Тесты"
)

# ================= ФУНКЦИИ =================

def weighted_avg(x):
    if len(x) == 0:
        return None
    weights = list(range(1, len(x)+1))
    return sum(v*w for v, w in zip(x, weights)) / sum(weights)

def color_daily(stress):
    # голубой → фиолетовый
    r = int(100 + stress * 1.5)
    g = int(200 - stress * 1.5)
    b = int(255 - stress * 0.5)
    return f"rgb({r},{g},{b})"

def color_san(stress):
    # оранжевый → коричневый
    r = int(255 - stress * 0.8)
    g = int(180 - stress * 1.2)
    b = int(50 - stress * 0.3)
    return f"rgb({r},{g},{b})"

def draw_circle(value, color):
    st.markdown(f"""
    <div style="
        width:180px;height:180px;border-radius:50%;
        border:12px solid {color};
        display:flex;align-items:center;justify-content:center;
        font-size:35px;margin:auto;">
        {int(value)}
    </div>
    """, unsafe_allow_html=True)

# ================= ИСТОРИЯ =================
if mode == "📊 История":

    st.header("📊 История")

    data = supabase.table("stress").select("*").eq("user", user).execute()
    df = pd.DataFrame(data.data)

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

        df_group = df.groupby(["date", "type"])["stress"].mean().reset_index()
        df_group["date"] = pd.to_datetime(df_group["date"])

        chart = alt.Chart(df_group).mark_line(point=True).encode(
            x=alt.X("date:T"),
            y=alt.Y("stress:Q", scale=alt.Scale(domain=[0,100])),
            color="type:N"
        )

        st.altair_chart(chart, use_container_width=True)

# ================= ТЕСТЫ =================
if mode == "🧪 Тесты":

    sub1, sub2 = st.tabs(["📅 Актуальное самочувствие", "🧠 Общее настроение"])

    # ---------- DAILY ----------
    with sub1:

        st.subheader("Актуальное состояние")

        def q(title):
            return st.radio(title, [5,4,3,2,1])

        q1 = q("Усталость")
        q2 = q("Сон")
        q3 = q("Боль")
        q4 = q("Стресс")
        q5 = q("Настроение")

        score = q1 + q2 + q3 + q4 + q5

        stress = (25 - score) / 20 * 100

        st.subheader(f"Стресс: {int(stress)}")

        if st.button("💾 Сохранить daily"):
            supabase.table("stress").insert({
                "user": user,
                "time": str(datetime.datetime.now()),
                "stress": float(stress),
                "type": "daily"
            }).execute()

        # ===== среднее за день =====
        data = supabase.table("stress").select("*").eq("user", user).eq("type", "daily").execute()
        df = pd.DataFrame(data.data)

        if not df.empty:
            df["time"] = pd.to_datetime(df["time"])
            today = datetime.date.today()

            df_today = df[df["time"].dt.date == today]

            avg = weighted_avg(df_today["stress"].tolist())

            if avg:
                draw_circle(avg, color_daily(avg))

    # ---------- SAN ----------
    with sub2:

        st.subheader("Общее настроение")

        scale = [-3,-2,-1,0,1,2,3]

        def san(q, key):
            return st.select_slider(q, options=scale, value=0, key=key)

        values = [san(f"Q{i}", f"s{i}") for i in range(10)]

        def norm(x):
            return (sum(x)/len(x)+3)/6*100

        stress = 100 - norm(values)

        st.subheader(f"Стресс: {int(stress)}")

        if st.button("💾 Сохранить san"):
            supabase.table("stress").insert({
                "user": user,
                "time": str(datetime.datetime.now()),
                "stress": float(stress),
                "type": "san"
            }).execute()

        # ===== среднее =====
        data = supabase.table("stress").select("*").eq("user", user).eq("type", "san").execute()
        df = pd.DataFrame(data.data)

        if not df.empty:
            df["time"] = pd.to_datetime(df["time"])
            today = datetime.date.today()

            df_today = df[df["time"].dt.date == today]

            avg = weighted_avg(df_today["stress"].tolist())

            if avg:
                draw_circle(avg, color_san(avg))
