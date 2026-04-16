import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
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

        

        fig = px.line(
            df_group,
            x="date",
            y="stress",
            color="type",
            markers=True
)

        fig.update_layout(
            yaxis=dict(range=[0,100]),
            xaxis_title="Дата",
            yaxis_title="Стресс",
            hovermode="x unified"
) 

        st.plotly_chart(fig, use_container_width=True)
# ================= ТЕСТЫ =================
if mode == "🧪 Тесты":

    sub1, sub2 = st.tabs(["📅 Актуальное самочувствие", "🧠 Общее настроение"])

    # ---------- DAILY ----------
    with sub1:
        st.subheader("Актуальное состояние")

        def q(title, options, key):
            return st.radio(
                title,
                [5,4,3,2,1],
                key=key,
                format_func=lambda x: f"{x} — {options[x]}"
        )

        q1 = q("Усталость", {
            5: "полностью отдохнувший",
            4: "отдохнувший",
            3: "нормально",
            2: "более уставший, чем обычно",
            1: "всегда уставший"
         }, "d1")

        q2 = q("Качество сна", {
            5: "полностью выспался",
            4: "хороший сон",
            3: "трудности с засыпанием",
            2: "прерывистый сон",
            1: "бессонница"
        }, "d2")

        q3 = q("Мышечная боль", {
            5: "отличное самочувствие",
            4: "хорошее самочувствие",
            3: "нормально",
            2: "напряжение и скованность",
            1: "сильная боль"
        }, "d3")

        q4 = q("Уровень стресса", {
            5: "полностью расслаблен",
            4: "расслаблен",
            3: "нормальный уровень",
            2: "стресс",
            1: "сильный стресс"
        }, "d4")

        q5 = q("Настроение", {
            5: "отличное настроение",
            4: "хорошее",
            3: "меньше интереса",
            2: "раздражён",
            1: "сильно раздражён"
        }, "d5")

        score = q1 + q2 + q3 + q4 + q5
        stress = (25 - score) / 20 * 100

        st.subheader(f"Стресс: {int(stress)}")


        if st.button("💾 Сохранить", use_container_width=True):

            supabase.table("stress").insert({
            "user": user,
            "time": str(datetime.datetime.now()),
            "stress": float(stress),
            "type": "daily"
            }).execute()

        st.success("Сохранено")

    # ---------- СООБЩЕНИЕ ----------
        if stress < 30:
            st.success("Отличное состояние - можно тренироваться на максимум")
        elif stress < 50:
            st.info("Нормальное состояние - хорошая форма")
        elif stress < 70:
            st.warning("Есть усталость - лучше снизить нагрузку")
        else:
            st.error("Высокий стресс - нужен отдых")

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
        st.subheader("Общее настроение (САН)")

        scale = [-3,-2,-1,0,1,2,3]

        def san(left, right, key):
            return st.select_slider(
                f"{left} ← → {right}",
                options=scale,
                value=0,
                key=key
        )

        questions = [
            ("Самочувствие хорошее","самочувствие плохое"),
            ("Чувствую себя сильным","чувствую себя слабым"),
            ("Пассивный","активный"),
            ("Малоподвижный","подвижный"),
            ("Весёлый","грустный"),
            ("Хорошее настроение","плохое настроение"),
            ("Работоспособный","разбитый"),
            ("Полный сил","обессиленный"),
            ("Медлительный","быстрый"),
            ("Бездеятельный","деятельный"),
            ("Счастливый","несчастный"),
            ("Жизнерадостный","мрачный"),
            ("Напряжённый","расслабленный"),
            ("Здоровый","больной"),
            ("Безучастный","увлеченный"),
            ("Равнодушный","взволнованный"),
            ("Восторженный","унылый"),
            ("Радостный","печальный"),
            ("Отдохнувший","усталый"),
            ("Свежий","изнуренный"),
            ("Сонливый","возбуждённый"),
            ("Желание отдохнуть","желание работать"),
            ("Спокойный","озабоченный"),
            ("Оптимистичный","пессимистичный"),
            ("Выносливый","утомленный"),
            ("Бодрый","вялый"),
            ("Соображать трудно","соображать легко"),
            ("Рассеянный","внимательный"),
            ("Полный надежд","разочарованный"),
            ("Довольный","недовольный")
    ]

        values = []
        for i, (l, r) in enumerate(questions):
            values.append(san(l, r, f"s{i}"))

        def norm(x):
            return (sum(x)/len(x)+3)/6*100

        stress = 100 - norm(values)

        st.subheader(f"Стресс: {int(stress)}")

        if st.button("💾 Сохранить САН", use_container_width=True):

            supabase.table("stress").insert({
                "user": user,
                "time": str(datetime.datetime.now()),
                "stress": float(stress),
                "type": "san"
                }).execute()

        st.success("Сохранено")

    # ---------- СООБЩЕНИЕ ----------
        if stress < 30:
            st.success("Общее состояние отличное")
        elif stress < 50:
            st.info("Есть небольшая усталость")
        elif stress < 70:
            st.warning("Состояние ухудшается - стоит отдохнуть")
        else:
            st.error("Плохое состояние - возможен перегруз")

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
