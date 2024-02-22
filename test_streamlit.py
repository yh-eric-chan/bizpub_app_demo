import streamlit as st
import pandas as pd
import plotly.express as px

# 加载数据
@st.cache_data
def load_data():
    return pd.read_csv('bizpub_clean.csv')

data = load_data()

# 页面标题
st.title('期刊文章长度探索')

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
fig = px.histogram(journal_data, x='PageLength', title=f'{journal} 文章页数分布', nbins=30)
fig.update_layout(xaxis_title="文章页数", yaxis_title="文章数量")
st.plotly_chart(fig)
