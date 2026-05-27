import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt


plt.style.use('seaborn-v0_8-darkgrid')

st.set_page_config(page_title="F1 Painel de Estratégia", layout="wide")
fastf1.plotting.setup_mpl(mpl_timedelta_support=False, color_scheme='fastf1')

st.title("F1 🏎️ Painel de Estratégia")

col1, col2 = st.columns(2)

with col1:
    year = st.selectbox("Selecione o Ano", range(2026, 2018, -1))

@st.cache_data
def get_season_schedule(year):
    return fastf1.get_event_schedule(year)

schedule = get_season_schedule(year)
gp_list = schedule['EventName'].tolist()

with col2:
    selected_gp = st.selectbox("Selecione o GP", gp_list, index=0)

event_data = schedule[schedule['EventName'] == selected_gp].iloc[0]
round_number = event_data['RoundNumber']

@st.cache_data
def load_data(year, round_num):
    session = fastf1.get_session(year, round_num, 'R')
    session.load()
    return session

if st.button("Gerar Análise"):
    with st.spinner(f"Baixando dados do {selected_gp}..."):
        try:
            session = load_data(year, round_number)
            
            # --- GRÁFICO 1: ESTRATÉGIAS ---
            st.subheader(f"Estratégias de Stint - {selected_gp} {year}")
            laps = session.laps
            stints = laps[["Driver", "Stint", "Compound", "LapNumber"]].groupby(["Driver", "Stint", "Compound"]).count().reset_index()
            stints = stints.rename(columns={"LapNumber": "StintLength"})
            
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            for driver in session.drivers:
                drv_data = stints.loc[stints["Driver"] == session.get_driver(driver)["Abbreviation"]]
                prev_end = 0
                for _, row in drv_data.iterrows():
                    color = fastf1.plotting.get_compound_color(row["Compound"], session=session)
                    ax1.barh(y=session.get_driver(driver)["Abbreviation"], width=row["StintLength"], left=prev_end, color=color, edgecolor="black", linewidth=0.5, height=0.6)
                    prev_end += row["StintLength"]
            
            
            ax1.invert_yaxis()
            st.pyplot(fig1)

            # --- GRÁFICO 2: POSIÇÃO ---
            st.subheader("Evolução das Posições")
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            for drv in session.drivers:
                d_laps = session.laps.pick_drivers(drv)
                abb = d_laps['Driver'].iloc[0]
                style = fastf1.plotting.get_driver_style(identifier=abb, style=['color', 'linestyle'], session=session)
                ax2.plot(d_laps['LapNumber'], d_laps['Position'], label=abb, **style)
            
            ax2.set_ylim([20.5, 0.5])
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig2)

        except Exception as e:
            st.error(f"Erro ao carregar sessão: {e}. Verifique o nome do GP.")