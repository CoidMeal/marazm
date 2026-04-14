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
    st.title("Контроль стресса")

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
    sub1, sub2 = st.tabs(["📅 Ежедневный", "🧠 САН"])

    # ================= DAILY =================
    with sub1:
        st.header("Ежедневный тест")

        labels = {
            5: "Отлично",
            4: "Хорошо",
            3: "Нормально",
            2: "Плохо",
            1: "Очень плохо"
        }

        def ask(q):
            return st.radio(q, [5,4,3,2,1],
                format_func=lambda x: f"{x} - {labels[x]}")

        q1 = ask("Усталость")
        q2 = ask("Сон")
        q3 = ask("Боль")
        q4 = ask("Стресс")
        q5 = ask("Настроение")

        score = (q1*0.25 + q2*0.25 + q3*0.2 + q4*0.2 + q5*0.1)
        stress = (5 - score) / 4 * 100

        if q2 <= 2: stress += 10
        if q1 <= 2: stress += 10
        if q4 <= 2: stress += 10

        if min(q1,q2,q3,q4,q5) == 1:
            stress = max(stress, 80)

        stress = min(stress, 100)

        st.subheader(f"Стресс: {int(stress)}")

        if st.button("💾 Сохранить", use_container_width=True):
            try:
                supabase.table("stress").insert({
                    "user": user,
                    "time": str(datetime.datetime.now()),
                    "stress": float(stress),
                    "type": "daily"
                }).execute()

                st.success("Сохранено")

            except Exception as e:
                st.error(e)

    # ================= SAN =================
    with sub2:
        st.header("САН")

        scale = [-3,-2,-1,0,1,2,3]

        def ask(q, key):
            return st.select_slider(q, options=scale, value=0, key=key)

        st.subheader("Самочувствие")
        S = [ask(f"S{i+1}", f"s_{i}") for i in range(10)]

        st.subheader("Активность")
        A = [ask(f"A{i+1}", f"a_{i}") for i in range(10)]

        st.subheader("Настроение")
        M = [ask(f"M{i+1}", f"m_{i}") for i in range(10)]

        def norm(x):
            return (sum(x)/len(x)+3)/6*100

        stress = 100 - (norm(S)+norm(A)+norm(M))/3

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
