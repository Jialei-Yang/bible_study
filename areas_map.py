# areas_map.py
# ────────────────────────────────────────────────────────────
# 功能：读取 database/areas_file.csv   (State / City 清单)
#      - 自动下载并缓存美国州 GeoJSON
#      - 自动用 Mapbox Geocoding 获取城市中心点并缓存
#      - Streamlit + Plotly 渲染：州 = 轮廓面，城市 = 红色中心点
# 依赖：streamlit, pandas, plotly, requests
# 运行：streamlit run areas_map.py
# ────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import requests, json, pathlib
from typing import Dict, Optional

# ───────── ① 路径常量 ─────────
DATA_DIR    = pathlib.Path("database")
DATA_DIR.mkdir(exist_ok=True)

CSV_FILE    = DATA_DIR / "areas_file.csv"            # <— 数据源
GEO_PATH    = DATA_DIR / "us_states_simple.geojson"  # 州轮廓缓存
CACHE_FILE  = DATA_DIR / "city_cache.json"           # 城市坐标缓存

GEOJSON_SRC = (
    "https://cdn.jsdelivr.net/gh/PublicaMundi/MappingAPI@master/"
    "data/geojson/us-states.json"                    # ≈300 KB 精简州界
)

# ───────── ② 读取 CSV ─────────
@st.cache_data(show_spinner=False)
def load_regions(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"❌ 未找到 {path.name}，请先放入 database/ 目录")
        st.stop()
    df = pd.read_csv(path, dtype=str)
    exp_cols = {"id", "name", "type", "state_iso", "note"}
    missing  = exp_cols - set(df.columns)
    if missing:
        st.error(f"CSV 缺少列：{', '.join(missing)}")
        st.stop()
    return df

regions_df = load_regions(CSV_FILE)

# ───────── ③ 获取州 GeoJSON ─────────
@st.cache_resource(show_spinner=False)
def get_states_geo() -> Dict:
    if GEO_PATH.exists():
        return json.loads(GEO_PATH.read_text())
    with st.spinner("首次运行：下载州轮廓 GeoJSON …"):
        r = requests.get(GEOJSON_SRC, timeout=30)
        r.raise_for_status()
        GEO_PATH.write_text(r.text)
        return r.json()

states_geo = get_states_geo()

# ───────── ④ 城市坐标获取与缓存 ─────────
def geocode_city(city: str, state: str, token: str) -> Optional[Dict]:
    """返回 {'lat': .., 'lon': ..}；失败返回 None"""
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text())

    key = f"{city},{state}"
    if key in cache:
        return cache[key]

    url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
           f"{city}%2C%20{state}.json?limit=1&access_token={token}")
    try:
        res = requests.get(url, timeout=10).json()
        feats = res.get("features")
        if feats:
            lon, lat = feats[0]["center"]
            cache[key] = {"lat": lat, "lon": lon}
            CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
            return cache[key]
    except Exception as e:
        st.warning(f"Geocoding '{key}' 失败：{e}")
    return None

# ───────── ⑤ 绘图函数 ─────────
def render_map(token: str):
    state_df = regions_df[regions_df["type"].str.lower() == "state"]
    city_df  = regions_df[regions_df["type"].str.lower() == "city"].copy()

    # 给城市补经纬度
    for idx, row in city_df.iterrows():
        if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
            continue   # Excel 里已手填
        coord = geocode_city(row["name"], row["state_iso"], token)
        if coord:
            city_df.at[idx, "lat"] = coord["lat"]
            city_df.at[idx, "lon"] = coord["lon"]

    # 州轮廓
    fig = px.choropleth_mapbox(
        state_df,
        geojson=states_geo,
        locations="id",
        color_discrete_sequence=["#8ecae6"],
        hover_name="name",
        opacity=0.35,
        mapbox_style="carto-positron",
        zoom=3, center=dict(lat=37.8, lon=-96),
    )

    # 城市点
    ok = city_df.dropna(subset=["lat", "lon"])
    fig.add_scattermapbox(
        lat=ok["lat"], lon=ok["lon"],
        text=ok["name"],
        mode="markers+text",
        marker=dict(size=10, color="red"),
        textposition="top right"
    )

    fig.update_layout(
        mapbox_accesstoken=token,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

# ───────── ⑥ Streamlit 页面 ─────────
st.set_page_config(page_title="areas_map", layout="wide")
st.title("areas_map — 州 / 城市区块可视化")

st.markdown("""
**使用说明**  
1. 将 **areas_file.csv** 放入 `database/` 目录，包含列：`id`, `name`, `type`, `state_iso`, `note`  
2. 执行 `streamlit run areas_map.py`  
3. 在网页输入 *Mapbox Token*，地图即加载
""")

token = st.text_input("Mapbox Token", type="password")
if token.strip():
    render_map(token.strip())
else:
    st.info("请先输入有效 Mapbox Token")

st.markdown("### 数据预览")
st.dataframe(regions_df, hide_index=True)
