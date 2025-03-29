import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import os
from dotenv import load_dotenv
import numpy as np

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="StatFutBR - Estatísticas de Futebol",
    page_icon="⚽",
    layout="wide"
)

# Configuração do estilo
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header {
        background-color: #1f77b4;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)

# Configuração da API
API_URL = os.getenv('API_URL', 'http://localhost:5001')

def fetch_jogadores():
    """Busca todos os jogadores da API"""
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:8501'
        }
        response = requests.get(f"{API_URL}/jogadores", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao buscar jogadores: {str(e)}")
        return []

def fetch_jogador_detalhes(id_jogador):
    """Busca detalhes de um jogador específico"""
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:8501'
        }
        response = requests.get(f"{API_URL}/jogadores/{id_jogador}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao buscar detalhes do jogador: {str(e)}")
        return None

def criar_grafico_radar(estatisticas, jogador_nome):
    """Cria um gráfico radar com as estatísticas principais"""
    if not estatisticas:
        return None
    
    # Selecionar métricas principais
    metrics = {
        'Gols/90': float(estatisticas.get('golsper90', 0)),
        'Assist/90': float(estatisticas.get('assistper90', 0)),
        'xG': float(estatisticas.get('xg', 0)),
        'xAG': float(estatisticas.get('xag', 0)),
        'PRGC': float(estatisticas.get('prgc', 0)),
        'PRGP': float(estatisticas.get('prgp', 0))
    }
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=list(metrics.values()),
        theta=list(metrics.keys()),
        fill='toself',
        name=jogador_nome
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(metrics.values()) * 1.2]
            )),
        showlegend=True,
        title=f"Estatísticas Principais - {jogador_nome}",
        height=500
    )
    
    return fig

def criar_grafico_comparativo(jogador_atual, jogadores, metricas):
    """Cria um gráfico de barras comparativo"""
    if not jogador_atual or not jogadores:
        return None
    
    dados = []
    for jogador in jogadores:
        if jogador['id'] != jogador_atual['id']:
            stats = jogador['estatisticas']
            dados.append({
                'Jogador': jogador['nome'],
                'Time': jogador['time'],
                'Posição': jogador['posicao'],
                **{metrica: float(stats.get(metrica, 0)) for metrica in metricas}
            })
    
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    fig = px.bar(df, x='Jogador', y=metricas, barmode='group',
                 title=f"Comparação com Outros Jogadores - {jogador_atual['nome']}")
    
    fig.update_layout(height=500)
    return fig

def main():
    # Header personalizado
    st.markdown("""
        <div class="header">
            <h1 style="margin: 0; text-align: center;">⚽ StatFutBR - Estatísticas de Futebol</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para filtros
    with st.sidebar:
        st.header("Filtros")
        
        # Busca por nome
        search_term = st.text_input("Buscar por nome", "")
        
        # Filtro por time
        times = sorted(list(set(j['time'] for j in fetch_jogadores())))
        time_selecionado = st.selectbox("Filtrar por time", ["Todos"] + times)
        
        # Filtro por posição
        posicoes = sorted(list(set(j['posicao'] for j in fetch_jogadores())))
        posicao_selecionada = st.selectbox("Filtrar por posição", ["Todas"] + posicoes)
        
        # Ordenação
        ordenacao = st.selectbox(
            "Ordenar por",
            ["Nome", "Time", "Posição", "Gols", "Assistências", "Partidas"]
        )
    
    # Buscar todos os jogadores
    jogadores = fetch_jogadores()
    
    if not jogadores:
        st.warning("Nenhum jogador encontrado.")
        return
    
    # Aplicar filtros
    if search_term:
        jogadores = [j for j in jogadores if search_term.lower() in j['nome'].lower()]
    
    if time_selecionado != "Todos":
        jogadores = [j for j in jogadores if j['time'] == time_selecionado]
    
    if posicao_selecionada != "Todas":
        jogadores = [j for j in jogadores if j['posicao'] == posicao_selecionada]
    
    # Ordenar jogadores
    if ordenacao == "Nome":
        jogadores.sort(key=lambda x: x['nome'])
    elif ordenacao == "Time":
        jogadores.sort(key=lambda x: (x['time'], x['nome']))
    elif ordenacao == "Posição":
        jogadores.sort(key=lambda x: (x['posicao'], x['nome']))
    elif ordenacao == "Gols":
        jogadores.sort(key=lambda x: float(x['estatisticas'].get('golsper90', 0)), reverse=True)
    elif ordenacao == "Assistências":
        jogadores.sort(key=lambda x: float(x['estatisticas'].get('assistper90', 0)), reverse=True)
    elif ordenacao == "Partidas":
        jogadores.sort(key=lambda x: float(x['estatisticas'].get('partidas', 0)), reverse=True)
    
    # Criar DataFrame para exibição
    df = pd.DataFrame(jogadores)
    if not df.empty:
        # Configurar grid
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(selection_mode='single', use_checkbox=True)
        gb.configure_column("nome", headerName="Nome", pinned='left')
        gb.configure_column("time", headerName="Time")
        gb.configure_column("posicao", headerName="Posição")
        gb.configure_column("estatisticas", headerName="Estatísticas", hide=True)
        
        grid_options = gb.build()
        
        # Exibir grid
        grid_response = AgGrid(
            df,
            grid_options=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            theme='streamlit'
        )
        
        # Verificar se um jogador foi selecionado
        if grid_response['selected_rows']:
            jogador_selecionado = grid_response['selected_rows'][0]
            st.markdown("---")
            
            # Exibir detalhes do jogador
            st.header(f"📊 Detalhes do Jogador: {jogador_selecionado['nome']}")
            
            # Informações básicas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Time", jogador_selecionado['time'])
                st.metric("Posição", jogador_selecionado['posicao'])
                st.metric("Idade", jogador_selecionado['idade'])
            
            with col2:
                st.metric("Nacionalidade", jogador_selecionado['nacionalidade'])
                st.metric("Pé Dominante", jogador_selecionado['pedominante'])
                st.metric("Altura", jogador_selecionado['altura'])
            
            with col3:
                st.metric("Peso", jogador_selecionado['peso'])
                st.metric("Agência", jogador_selecionado['agencia'])
                st.metric("Gols", jogador_selecionado['gols'])
            
            with col4:
                st.metric("Assistências", jogador_selecionado['assistencias'])
                st.metric("Partidas", jogador_selecionado['estatisticas'].get('partidas', 0))
                st.metric("Minutos Jogados", jogador_selecionado['estatisticas'].get('minutos_jogados', 0))
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico radar
                if jogador_selecionado['estatisticas']:
                    fig = criar_grafico_radar(jogador_selecionado['estatisticas'], jogador_selecionado['nome'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gráfico comparativo
                if jogador_selecionado['estatisticas']:
                    metricas = ['golsper90', 'assistper90', 'xg', 'xag']
                    fig = criar_grafico_comparativo(jogador_selecionado, jogadores, metricas)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas detalhadas
            st.subheader("Estatísticas Detalhadas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Cartões Amarelos", jogador_selecionado['estatisticas'].get('cartoes_amarelos', 0))
                st.metric("Cartões Vermelhos", jogador_selecionado['estatisticas'].get('cartoes_vermelhos', 0))
                st.metric("Chutes a Gol", jogador_selecionado['estatisticas'].get('chutesagol', 0))
            
            with col2:
                st.metric("Precisão de Chutes", f"{jogador_selecionado['estatisticas'].get('percchutesagol', 0):.1f}%")
                st.metric("Gols por Chute", f"{jogador_selecionado['estatisticas'].get('golsporchute', 0):.2f}")
                st.metric("PRGR", f"{jogador_selecionado['estatisticas'].get('prgr', 0):.2f}")
            
            with col3:
                st.metric("PRGC", f"{jogador_selecionado['estatisticas'].get('prgc', 0):.2f}")
                st.metric("PRGP", f"{jogador_selecionado['estatisticas'].get('prgp', 0):.2f}")
                st.metric("Total de Chutes", jogador_selecionado['estatisticas'].get('totaldechutes', 0))

if __name__ == "__main__":
    main() 