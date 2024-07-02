import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def run():
    # Load the CSV file
    df = pd.read_csv('database/characters_file.csv')

    # Streamlit 应用
    st.title("以色列人物时期")

    st.subheader('1.编年史', divider='rainbow')

    # 创建一个多选菜单来选择人物类型
    character_types = df['人物类型'].unique()
    selected_character_types = st.multiselect('选择一个或多个人物类型', character_types, default=character_types)

    # 根据选择的人物类型过滤数据
    filtered_data = df[df['人物类型'].isin(selected_character_types)]

    # 准备可视化数据
    fig = go.Figure()

    for _, row in filtered_data.iterrows():
        line_dash = 'solid' if row['人物类型排序'] == 1 else 'dash'
        hover_text = f"{row['中文名称']}<br>重要度评分: {row['重要度评分']}<br>评分原因: {row['重要度评分原因']}<br>在位时间: {row['任期时长']}<br>相关书卷: {row['相关书卷']}<br>被提到的次数: {row['被提及次数']}"
        fig.add_trace(go.Scatter(
            x=[row['任期开始年份'], row['任期结束年份']],
            y=[row['重要度评分'], row['重要度评分']],
            mode='lines+markers+text',
            name=row['中文名称'],
            text=[row['中文名称'], ''],
            textposition="top center",
            line=dict(dash=line_dash),
            hovertext=hover_text,
            hoverinfo='text+name'
        ))

    # 更新布局
    fig.update_layout(
        xaxis_title="年份",
        yaxis_title="重要度评分",
        xaxis=dict(range=[-4000, 0], dtick=500),
        yaxis=dict(range=[0, 11], dtick=1),
        showlegend=False
    )

    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('2.人物志', divider='rainbow')

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
            '信仰状态评分': st.column_config.ProgressColumn(
                '信仰状态评分',
                help="信仰状态评分[0,10]",
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
