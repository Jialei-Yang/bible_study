import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Load the Excel file

def run():
    df = pd.read_csv('database/kings_file.csv')
    
    # Streamlit 应用
    st.title("以色列王国时期诸王信息")
    
    st.subheader('1.编年史', divider='rainbow')
    
    # 创建一个多选菜单来选择王国
    kingdom_options = df['kingdom'].unique()
    selected_kingdoms = st.multiselect('选择一个或多个王国时期', kingdom_options, default=kingdom_options)
    
    # 根据选择的王国过滤数据
    filtered_data = df[df['kingdom'].isin(selected_kingdoms)]
    
    # 准备可视化数据
    fig = go.Figure()
    
    for _, row in filtered_data.iterrows():
        line_dash = 'solid' if row['kingdom'] in ['南国犹大', '统一王国'] else 'dash'
        hover_text = f"{row['king_name_cn']}<br>评分: {row['score']}<br>评价原因: {row['score_reason']}<br>在位时间: {row['duration']}<br>相关书卷: {row['book']}<br>被提到的次数: {row['mentioned_times']}"
        fig.add_trace(go.Scatter(
            x=[row['start_year'], row['end_year']],
            y=[row['score'], row['score']],
            mode='lines+markers+text',
            name=row['king_name_cn'],
            text=[row['king_name_cn'], ''],
            textposition="top center",
            line=dict(dash=line_dash),
            hovertext=hover_text,
            hoverinfo='text+name'
        ))
    
    # 更新布局
    fig.update_layout(
        xaxis_title="年份",
        yaxis_title="评价",
        xaxis=dict(range=[-1100, -550], dtick=50),
        yaxis=dict(range=[-3, 3], dtick=1),
        showlegend=False
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader('2.诸王志', divider='rainbow')
    
    df = df.rename(columns={'kingdom':          '王国', 
                            'king_rank':        '在位顺序', 
                            'king_name_cn':     '国王中文名称', 
                            'king_name_en':     '国王英文名称', 
                            'start_year':       '开始在位年份', 
                            'end_year':         '结束在位年份', 
                            'score':            '评分', 
                            'dp_score':         '大卫鲍森评分', 
                            'duration':         '在位时长', 
                            'book':             '相关书卷', 
                            'mentioned_times':  '被提到的次数', 
                            'score_reason':     '评分原因', 
                            'main_story':       '主要事迹'})
    
    st.dataframe(
        df,
        column_config={
            '评分': st.column_config.ProgressColumn(
                '评分', 
                help="GPT4所给出的评分[-2,2]",
                format="%f⭐",
                min_value = -2,
                max_value = 2,
                width = 'small'
            ),
            '大卫鲍森评分': st.column_config.ProgressColumn(
                '大卫鲍森评分', 
                help="大卫鲍森牧师所给出的评分[-2,2]",
                format="%f⭐",
                min_value = -2,
                max_value = 2,
                width = 'small'
            )
        },
        hide_index=True,
        use_container_width=True
    )

# 运行应用
if __name__ == "__main__":
    run()
