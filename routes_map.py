import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def load_data():
    # 读取上传的CSV文件
    data = pd.read_csv('database/route_data.csv')
    # 分割位置信息列为经纬度两列
    data[['latitude', 'longitude']] = data['位置信息(经纬度)'].str.split(',', expand=True)
    data['latitude'] = pd.to_numeric(data['latitude'].str.strip(), errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'].str.strip(), errors='coerce')
    data['信仰状态打分'] = pd.to_numeric(data['信仰状态打分'], errors='coerce').astype(int)
    return data

def run():

    data = load_data()
    
    # 获取所有系列名称
    series_names = data['系列名称'].unique()
    
    # 设置颜色刻度
    colorscale = px.colors.diverging.Earth
    
    # 设置Streamlit页面
    st.title("历史路线展示")
    st.markdown("""
    这个应用展示了不同历史线路的相关信息。
    您可以选择一个系列名称，并在地图上查看相关的历史路线。
    """)
    
    # 添加一个选择框让用户选择系列名称
    selected_series = st.selectbox("请选择系列名称:", series_names)
    
    # 过滤数据以显示选定系列的路线
    filtered_data = data[data['系列名称'] == selected_series]
    
    # 添加一个输入框让用户输入Mapbox访问令牌
    mapbox_token = st.text_input("请输入您的 Mapbox 访问令牌:")
    
    if mapbox_token:
        # 创建地图图形
        fig = go.Figure(go.Scattermapbox(
            mode="markers+text+lines",
            lon=filtered_data['longitude'],
            lat=filtered_data['latitude'],
            text=filtered_data['地点名称'],
            marker=dict(size=15, 
                        color=filtered_data['信仰状态打分'], 
                        colorscale=colorscale,
                        cmin=-5, 
                        cmax=5, 
                        colorbar=dict(title="信仰状态打分", tickvals=[-5, 0, 5])),
            line=dict(width=1, color='black'),
            hoverinfo='text',
            textposition='top right',
            textfont=dict(size=20, color='black'),
            customdata=filtered_data[['序号', '主要人物', '主要事件', '短评', '信仰状态打分', '停留开始日期', '停留结束日期', '停留时间(天/年)']],
            hovertemplate=(
                "<b>%{text}</b><br><br>" +
                "序号: %{customdata[0]}<br>" +
                "主要人物: %{customdata[1]}<br>" +
                "主要事件: %{customdata[2]}<br>" +
                "短评: %{customdata[3]}<br>" +
                "信仰状态打分: %{customdata[4]}<br>" +
                "停留开始日期: %{customdata[5]}<br>" +
                "停留结束日期: %{customdata[6]}<br>" +
                "停留时间(天/年): %{customdata[7]}<br>"
            )
        ))
    
        fig.update_layout(
            mapbox=dict(
                style="mapbox://styles/mapbox/streets-v11",
                accesstoken=mapbox_token,
                zoom=6,
                center=dict(lat=filtered_data['latitude'].mean(), lon=filtered_data['longitude'].mean())
            ),
            height=600,
            margin={"r":0,"t":0,"l":0,"b":0}
        )
    
        # 显示地图
        st.plotly_chart(fig)
    
    # 显示过滤后的数据表格
    st.dataframe(filtered_data)
    
if __name__ == "__main__":
    run()
