import streamlit as st
import kings_story
import toml

st.set_page_config(layout="wide")

# 初始化 session_state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_permissions'] = []

# 读取 TOML 文件
def load_credentials(file_path='credentials.toml'):
    """从 TOML 文件加载用户凭证和权限"""
    try:
        return toml.load(file_path)
    except Exception as e:
        st.error(f"无法加载凭证文件: {e}")
        return {}

USER_CREDENTIALS = load_credentials()

def login(user, pwd):
    """验证用户登录凭证，并根据权限存储信息"""
    if user in USER_CREDENTIALS and USER_CREDENTIALS[user]['password'] == pwd:
        st.session_state['logged_in'] = True
        st.session_state['user_permissions'] = USER_CREDENTIALS[user]['permissions']
        st.success("登录成功!")
    else:
        st.error("用户名或密码错误，请重试。")

def login_form():
    """显示登录表单"""
    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        submitted = st.form_submit_button("登录")
        if submitted:
            login(username, password)

# 若用户未登录，显示登录表单；否则显示应用选择器
if not st.session_state['logged_in']:
    st.title("请登录")
    login_form()
else:
    # 定义子应用与权限的映射
    app_permissions = {
        '以色列王国时期诸王': 'kings_story'
    }

    # 根据用户权限展示可用的子应用
    available_apps = [app for app, perm in app_permissions.items() if perm in st.session_state['user_permissions']]

    # 在侧边栏添加选择器
    app_selector = st.sidebar.selectbox(
        '选择一个应用',
        available_apps
    )

    # 根据选择加载不同的应用
    if app_selector == '以色列王国时期诸王':
        kings_story.run()
