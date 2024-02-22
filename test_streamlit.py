import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations
import networkx as nx

# 加载数据
@st.cache_data
def load_data():
    return pd.read_csv('bizpub_clean.csv')

data = load_data()

# 页面标题
st.title('期刊文章探索应用')

# 选择探索类型
explore_type = st.sidebar.selectbox('选择探索类型', ['文章长度', '作者合作关系'])

if explore_type == '文章长度':
    # 选择期刊
    journal = st.selectbox('选择期刊', options=data['Journal'].unique())
    
    # 根据期刊筛选数据
    journal_data = data[data['Journal'] == journal]
    
    # 计算文章页数
    def calculate_page_length(pages):
        try:
            start, end = pages.split('-')
            return int(end) - int(start) + 1
        except ValueError:  # 捕获值错误，例如如果`pages`无法被分割或转换为整数
            return None  # 返回None或者你可以选择返回一个默认值，比如0
    
    journal_data['PageLength'] = journal_data['Pages'].apply(calculate_page_length)
    
    # 文章长度的直方图
    fig = px.histogram(journal_data, x='PageLength', title=f'{journal}文章页数分布')
    st.plotly_chart(fig)

elif explore_type == '作者合作关系':
    # 用户输入作者名
    author_name = st.text_input('输入作者名查看合作关系', '')

    # 构建作者合作网络
    def build_coauthor_network(data):
        G = nx.Graph()
        for authors in data['Authors'].dropna():
            authors_list = authors.split('; ')
            for author_pair in combinations(authors_list, 2):
                if G.has_edge(*author_pair):
                    G[author_pair[0]][author_pair[1]]['weight'] += 1
                else:
                    G.add_edge(author_pair[0], author_pair[1], weight=1)
        return G
    
    G = build_coauthor_network(data)
    
    # 如果输入了作者名，只显示该作者的合作网络
    if author_name:
        G = nx.ego_graph(G, author_name, radius=1)
    
    pos = nx.spring_layout(G, seed=42)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            color=[],
            line_width=2))

    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(f'{adjacencies[0]} (# of connections: {len(adjacencies[1])})')

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='<br>作者合作网络图',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[dict(
                        text="网络图展示作者之间的合作关系，节点大小表示合作数量",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002)],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

    st.plotly_chart(fig)

elif explore_type == '期刊年度文章平均长度':
    # 让用户选择年份
    year_selected = st.selectbox('选择年份', options=sorted(data['Year'].unique(), reverse=True))
    
    # 筛选出所选年份的数据
    data_filtered_by_year = data[data['Year'] == year_selected]
    
    # 计算文章页数函数
    def calculate_page_length(pages):
        try:
            start, end = pages.split('-')
            return int(end) - int(start) + 1
        except ValueError:
            return None
    
    # 应用文章页数计算函数
    data_filtered_by_year['PageLength'] = data_filtered_by_year['Pages'].apply(calculate_page_length)
    
    # 计算每个期刊的平均文章长度
    avg_length_by_journal = data_filtered_by_year.groupby('Journal')['PageLength'].mean().dropna().reset_index()
    
    # 如果有数据则绘图，否则提示无数据
    if not avg_length_by_journal.empty:
        fig = px.bar(avg_length_by_journal, x='Journal', y='PageLength',
                     title=f'{year_selected}年各期刊平均文章页数', labels={'PageLength': '平均页数'})
        st.plotly_chart(fig)
    else:
        st.write(f'{year_selected}年没有可用的期刊数据。')