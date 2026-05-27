import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="F1 Painel de Estratégia", layout="wide")

COMPOUND_MAP = {
    'SOFT': "#f10f0f",
    'MEDIUM': "#f1ff33",
    'HARD': '#ffffff',
    'INTERMEDIATE': '#00d200',
    'WET': '#0000ff'
}

st.title("F1 🏎️ Painel de Estratégia")

@st.cache_data
def get_event_list(year):
    return fastf1.get_event_schedule(year)

@st.cache_data
def load_session(year, round_num):
    session = fastf1.get_session(year, round_num, 'R')
    session.load()
    return session

year = st.sidebar.selectbox("Ano", range(2026, 2018, -1))
schedule = get_event_list(year)
selected_gp = st.sidebar.selectbox("Grande Prêmio", schedule['EventName'].tolist())
round_number = schedule[schedule['EventName'] == selected_gp].iloc[0]['RoundNumber']

if st.button("Gerar Análise"):
    with st.spinner(f"Processando dados de {selected_gp}..."):
        session = load_session(year, round_number)
        laps = session.laps.copy()
        
        tab1, tab2, tab3 = st.tabs(["Estratégias", "Evolução de Posição", "Análise de Performance"])
        
        with tab1:
            st.subheader("Estratégias de Stint")
            stints = laps.groupby(["Driver", "Stint", "Compound"])["LapNumber"].count().reset_index()
            fig1 = px.bar(stints, x="LapNumber", y="Driver", color="Compound", orientation='h',
                          color_discrete_map=COMPOUND_MAP,
                          labels={'LapNumber': 'Volta', 'Driver': 'Piloto'})

            fig1.update_traces(
                marker_line_color='gray', 
                marker_line_width=1.5      
            )

            fig1.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            st.subheader("Evolução das Posições")

            color_map = {}
            for driver in laps['Driver'].unique():
                drv_info = session.get_driver(driver)
                color_map[driver] = f"#{drv_info['TeamColor']}"
            
            fig2 = px.line(
                laps, 
                x="LapNumber", 
                y="Position", 
                color="Driver", 
                markers=True,
                color_discrete_map=color_map,
                title="Evolução das Posições por Equipe",
                labels={'LapNumber': 'Volta', 'Position': 'Posição'}
            )
            fig2.update_yaxes(autorange="reversed")
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            st.subheader("Métricas de Performance")
            
            df_perf = laps[laps['LapTime'] < pd.Timedelta(seconds=120)].copy()
            df_perf['LapTimeSeconds'] = df_perf['LapTime'].dt.total_seconds()
            
            color_map = {driver: f"#{session.get_driver(driver)['TeamColor']}" for driver in laps['Driver'].unique()}
            
            consistency = df_perf.groupby('Driver')['LapTimeSeconds'].std().reset_index().sort_values(by='LapTimeSeconds', ascending=True)
            
            top_speeds = laps.dropna(subset=['SpeedST']).groupby('Driver')['SpeedST'].max().reset_index().sort_values(by='SpeedST', ascending=False)
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.write("#### Consistência")
                fig_cons = px.bar(
                    consistency, x='Driver', y='LapTimeSeconds', 
                    color='Driver', color_discrete_map=color_map,
                    labels={'LapTimeSeconds': 'Desvio Padrão (s)', 'Driver': 'Piloto'}
                )
                st.plotly_chart(fig_cons, use_container_width=True)
            
            with c2:
                st.write("#### Velocidade Máxima (km/h)")
                fig_speed = px.bar(
                    top_speeds, x='Driver', y='SpeedST', 
                    color='Driver', color_discrete_map=color_map,
                    labels={'SpeedST': 'Velocidade (km/h)', 'Driver': 'Piloto'}
                )
                st.plotly_chart(fig_speed, use_container_width=True)
        
        
