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

    # 创建一个单选按钮来选择评分类型
    score_type = st.radio(
        "选择要展示的评分类型",
        ('重要度评分', '信仰状态评分')
    )

    # 根据选择的人物类型过滤数据
    filtered_data = df[df['人物类型'].isin(selected_character_types)]

    # 准备可视化数据
    fig = go.Figure()

    for _, row in filtered_data.iterrows():
        if score_type == '重要度评分':
            y_value = row['重要度评分']
            hover_text = (f"{row['中文名称']}<br>任期开始年份: {row['任期开始年份']}<br>任期结束年份: {row['任期结束年份']}<br>主要故事: {row['主要故事']}<br>"
                          f"重要度评分: {row['重要度评分']}<br>评分原因: {row['重要度评分原因']}<br>在位时间: {row['任期时长']}<br>相关书卷: {row['相关书卷']}<br>被提到的次数: {row['被提及次数']}")
        else:
            y_value = row['信仰状态评分']
            hover_text = (f"{row['中文名称']}<br>任期开始年份: {row['任期开始年份']}<br>任期结束年份: {row['任期结束年份']}<br>主要故事: {row['主要故事']}<br>"
                          f"信仰状态评分: {row['信仰状态评分']}<br>评分原因: {row['信仰状态评分原因']}<br>在位时间: {row['任期时长']}<br>相关书卷: {row['相关书卷']}<br>被提到的次数: {row['被提及次数']}")

        fig.add_trace(go.Scatter(
            x=[row['任期开始年份'], row['任期结束年份']],
            y=[y_value, y_value],
            mode='lines+markers+text',
            name=row['中文名称'],
            text=[row['中文名称'], ''],
            textposition="top center",
            line=dict(dash='solid'),
            hovertext=hover_text,
            hoverinfo='text+name'
        ))

    # 更新布局
    yaxis_range = [0, 11] if score_type == '重要度评分' else [-6, 6]
    fig.update_layout(
        xaxis_title="年份",
        yaxis_title=score_type,
        yaxis=dict(range=yaxis_range, dtick=1),
        showlegend=False
    )

    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('2.人物志', divider='rainbow')

    st.dataframe(
        filtered_data,
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
