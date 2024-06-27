import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def run():
    # Load the CSV file
    df = pd.read_csv('database/prophets_file.csv')

    # Streamlit 应用
    st.title("以色列先知时期")

    st.subheader('1.编年史', divider='rainbow')

    # 创建一个多选菜单来选择先知类型
    prophet_types = df['先知类型'].unique()
    selected_prophet_types = st.multiselect('选择一个或多个先知类型', prophet_types, default=prophet_types)

    # 根据选择的先知类型过滤数据
    filtered_data = df[df['先知类型'].isin(selected_prophet_types)]

    # 准备可视化数据
    fig = go.Figure()

    for _, row in filtered_data.iterrows():
        line_dash = 'solid' if row['先知类型'] == '主要' else 'dash'
        hover_text = f"{row['先知名称']}<br>重要度评分: {row['重要度评分']}<br>评分原因: {row['评分原因']}<br>在位时间: {row['先知时长']}<br>相关书卷: {row['相关书卷']}<br>被提到的次数: {row['被提及次数']}"
        fig.add_trace(go.Scatter(
            x=[row['开始年份'], row['结束年份']],
            y=[row['重要度评分'], row['重要度评分']],
            mode='lines+markers+text',
            name=row['先知名称'],
            text=[row['先知名称'], ''],
            textposition="top center",
            line=dict(dash=line_dash),
            hovertext=hover_text,
            hoverinfo='text+name'
        ))

    # 更新布局
    fig.update_layout(
        xaxis_title="年份",
        yaxis_title="重要度评分",
        xaxis=dict(range=[-1500, -400], dtick=100),
        yaxis=dict(range=[0, 11], dtick=1),
        showlegend=False
    )

    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('2.先知志', divider='rainbow')

    st.dataframe(
        df,
        column_config={
            '重要度评分': st.column_config.ProgressColumn(
                '重要度评分',
                help="重要度评分[0,10]",
                format="%d⭐",
                min_value=0,
                max_value=10,
                width='small'
            ),
            '牧师评分': st.column_config.ProgressColumn(
                '牧师评分',
                help="牧师评分[0,10]",
                format="%d⭐",
                min_value=0,
                max_value=10,
                width='small'
            )
        },
        hide_index=True,
        use_container_width=True
    )

# 运行应用
if __name__ == "__main__":
    run()
