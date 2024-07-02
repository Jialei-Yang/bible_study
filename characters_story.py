import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def run():
    # Load the CSV file
    df = pd.read_csv('database/characters_file.csv')

    # Streamlit 应用
    st.title("以色列各历史时期领袖")

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
            hover_text = (f"{row['中文名称']}<br>任期时长: {row['任期时长']}<br>任期开始年份: {row['任期开始年份']}<br>任期结束年份: {row['任期结束年份']}<br>主要故事: {row['主要故事']}<br>"
                          f"重要度评分: {row['重要度评分']}<br>评分原因: {row['重要度评分原因']}<br>相关书卷: {row['相关书卷']}<br>被提到的次数: {row['被提及次数']}")
        else:
            y_value = row['信仰状态评分']
            hover_text = (f"{row['中文名称']}<br>任期时长: {row['任期时长']}<br>任期开始年份: {row['任期开始年份']}<br>任期结束年份: {row['任期结束年份']}<br>主要故事: {row['主要故事']}<br>"
                          f"信仰状态评分: {row['信仰状态评分']}<br>评分原因: {row['信仰状态评分原因']}<br>相关书卷: {row['相关书卷']}<br>被提到的次数: {row['被提及次数']}")

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
            )
        },
        hide_index=True,
        use_container_width=True
    )

    st.subheader('3.评分标准', divider='rainbow')

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ## 评分依据
    
        ### 重要度评分依据
    
        1. **历史影响力**：该人物在以色列历史上的作用和影响力，例如是否带领了重大事件、改革或战争。
        2. **圣经记载的详细程度**：圣经中对该人物的详细记载和篇幅。篇幅越大，重要性通常越高。
        3. **对后世的影响**：该人物的行动和决定对后世以色列的历史和信仰产生的影响。
        4. **神的介入和呼召**：神是否亲自呼召或干预该人物的生命和行动。
        5. **政治成就**：在政治、军事、经济等方面的成就和贡献。
    
        ### 信仰状态评分依据
    
        1. **对神的忠诚度**：该人物是否对神保持忠诚，是否遵守神的律法和诫命。
        2. **宗教改革**：是否进行过宗教改革，清除偶像崇拜，恢复对神的敬拜。
        3. **悔改与顺服**：面对错误时，是否真心悔改，回归神的道路。
        4. **信仰的实际行动**：在实际行动中表现出的信仰，比如祈祷、献祭、宣讲神的旨意等。
        5. **圣经评价**：圣经中的直接评价，比如被称为“合神心意的人”或被批评为“行恶”。
        """)
    
    with col2:
        st.markdown("""
        ### 重要度评分标准
    
        | 评分 | 解释                                                           |
        |------|---------------------------------------------------------------|
        | 9-10 | 在圣经历史中具有极高影响力，扮演关键角色，重大事件的主导者。   |
        | 7-8  | 重要角色，参与或主导重大事件，对历史有显著影响。             |
        | 5-6  | 角色较为重要，有一定影响力，参与重要事件。                   |
        | 3-4  | 角色影响力有限，记载较少，但仍有一定历史价值。               |
        | 1-2  | 角色影响力较小，记载较少，对历史影响有限。                   |
    
        ### 信仰状态评分标准
    
        | 评分 | 解释                                                           |
        |------|---------------------------------------------------------------|
        | 4-5  | 对神极其忠诚，进行重大宗教改革或行为表现出极高信仰。           |
        | 3-4  | 对神忠诚，有明显信仰行为或宗教改革，但有一些不足。             |
        | 1-2  | 信仰不坚定，偶像崇拜严重，行为违背神的教导。                   |
        | -1-0 | 明显背离神的教导，偶像崇拜严重，导致重大负面影响。             |
        | -2至-5 | 严重背离神的教导，导致国家或信仰重大灾难或变故。               |
        """)
        
# 运行应用
if __name__ == "__main__":
    run()
