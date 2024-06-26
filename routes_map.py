import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def load_data(file_path):
    data = pd.read_csv(file_path)
    data[['latitude', 'longitude']] = data['位置信息(经纬度)'].str.split(',', expand=True)
    data['latitude'] = pd.to_numeric(data['latitude'].str.strip(), errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'].str.strip(), errors='coerce')
    data['信仰状态打分'] = pd.to_numeric(data['信仰状态打分'], errors='coerce').astype(int)
    return data

def jitter_coordinates(data, jitter_amount=0.0001):
    """Add a small jitter to coordinates that are identical to avoid overlap."""
    coords = data[['latitude', 'longitude']].values
    unique_coords, counts = np.unique(coords, axis=0, return_counts=True)
    
    for coord, count in zip(unique_coords, counts):
        if count > 1:
            indices = np.where((coords == coord).all(axis=1))[0]
            jitter = np.random.uniform(-jitter_amount, jitter_amount, size=(count, 2))
            coords[indices] += jitter
    
    data['latitude'], data['longitude'] = coords[:, 0], coords[:, 1]
    return data

def plot_route(data, token):
    colorscale = px.colors.diverging.Earth

    fig = go.Figure(go.Scattermapbox(
        mode="markers+text+lines",
        lon=data['longitude'],
        lat=data['latitude'],
        text=data['地点名称'],
        marker=dict(size=15, 
                    color=data['信仰状态打分'], 
                    colorscale=colorscale,
                    cmin=-5, 
                    cmax=5, 
                    colorbar=dict(title="信仰状态打分", tickvals=[-5, 0, 5])),
        line=dict(width=1, color='black'),
        hoverinfo='text',
        textposition='top right',
        textfont=dict(size=20, color='black'),
        customdata=data[['序号', '主要人物', '主要历史事件', '短评', '信仰状态打分', '停留开始日期', '停留结束日期', '停留时间(天/年)', '相关经文']],
        hovertemplate=(
            "<b>%{text}</b><br><br>" +
            "序号: %{customdata[0]}<br>" +
            "主要人物: %{customdata[1]}<br>" +
            "主要历史事件: %{customdata[2]}<br>" +
            "短评: %{customdata[3]}<br>" +
            "信仰状态打分: %{customdata[4]}<br>" +
            "停留开始日期: %{customdata[5]}<br>" +
            "停留结束日期: %{customdata[6]}<br>" +
            "停留时间(天/年): %{customdata[7]}<br>" +
            "相关经文: %{customdata[8]}<br>" 
        )
    ))

    fig.update_layout(
        mapbox=dict(
            style="mapbox://styles/mapbox/streets-v11",
            accesstoken=token,
            zoom=6,
            center=dict(lat=data['latitude'].mean(), lon=data['longitude'].mean())
        ),
        height=600,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    st.plotly_chart(fig)

def run():
    st.title("历史路线展示")
    st.markdown("""
    这个应用展示了不同历史线路的相关信息。
    您可以选择一个线路名称，并在地图上查看相关的历史路线。
    """)

    file = st.file_uploader("上传 CSV 文件", type=["csv"])
    if file:
        data = load_data(file)
        data = jitter_coordinates(data)
        series_names = data['线路名称'].unique()

        selected_series = st.selectbox("请选择线路名称:", series_names)
        filtered_data = data[data['线路名称'] == selected_series]

        mapbox_token = st.text_input("请输入您的 Mapbox 访问令牌:")

        if mapbox_token:
            plot_route(filtered_data, mapbox_token)

        st.dataframe(filtered_data, hide_index=True)

if __name__ == "__main__":
    run()
