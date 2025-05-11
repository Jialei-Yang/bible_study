# app.py  —— 资源改为存放在  database/  目录
import streamlit as st
import pandas as pd
import plotly.express as px
import requests, json, pathlib
from typing import Dict, Optional

# ---------- 目录常量 ----------
DATA_DIR   = pathlib.Path("database")                # ← 改这里
DATA_DIR.mkdir(exist_ok=True)

CSV_FILE = DATA_DIR / "areas_file.csv"               # 主表
GEO_PATH   = DATA_DIR / "us_states_simple.geojson"   # 州轮廓
CACHE_FILE = DATA_DIR / "city_cache.json"            # 城市缓存

GEOJSON_SRC = (
    "https://cdn.jsdelivr.net/gh/PublicaMundi/MappingAPI@master/"
    "data/geojson/us-states.json"
)

# ---------- 1. 读 Excel ----------
@st.cache_data(show_spinner=False)
def load_regions(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"找不到 {path.name}，请先放入 database/ 目录。")
        st.stop()
    df = pd.read_csv(CSV_FILE, dtype=str)
    expected = {"id", "name", "type", "state_iso", "note"}
    missing  = expected - set(df.columns)
    if missing:
        st.error(f"Excel 缺少列：{', '.join(missing)}")
        st.stop()
    return df

regions_df = load_regions(EXCEL_FILE)

# ---------- 2. 获取州 GeoJSON ----------
@st.cache_resource(show_spinner=False)
def get_states_geo() -> Dict:
    if GEO_PATH.exists():
        return json.loads(GEO_PATH.read_text())
    with st.spinner("首次运行，正在下载州轮廓 …"):
        res = requests.get(GEOJSON_SRC, timeout=30)
        res.raise_for_status()
        GEO_PATH.write_text(res.text)
        return res.json()

states_geo = get_states_geo()

# ---------- 3. 城市坐标缓存 & Geocoding ----------
def geocode_city(city: str, state: str, token: str) -> Optional[Dict]:
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text())
    else:
        cache = {}

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
        st.warning(f"Geocoding '{key}' 失败: {e}")
    return None

# ---------- 4. 绘图 ----------
def render_map(token: str):
    state_df = regions_df[regions_df["type"].str.lower() == "state"]
    city_df  = regions_df[regions_df["type"].str.lower() == "city"].copy()

    for idx, row in city_df.iterrows():
        if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
            continue
        coord = geocode_city(row["name"], row["state_iso"], token)
        if coord:
            city_df.at[idx, "lat"] = coord["lat"]
            city_df.at[idx, "lon"] = coord["lon"]

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

    ok = city_df.dropna(subset=["lat", "lon"])
    fig.add_scattermapbox(
        lat=ok["lat"], lon=ok["lon"],
        text=ok["name"],
        mode="markers+text",
        marker=dict(size=10, color="red"),
        textposition="top right"
    )

    fig.update_layout(mapbox_accesstoken=token, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---------- 5. UI ----------
st.set_page_config(page_title="州 / 城市地图", layout="wide")
st.title("州 / 城市区块可视化 Demo")

st.markdown("""
**步骤**  
1. 将固定文件放入 **database/**：  
   • `regions_master.xlsx` • `us_states_simple.geojson`（首跑可自动下载）  
2. 运行 `streamlit run app.py`  
3. 浏览器填入 Mapbox Token，地图即加载
""")

token = st.text_input("Mapbox Token", type="password")
if token.strip():
    render_map(token.strip())
else:
    st.info("请先输入有效 Token")

st.markdown("### 数据预览")
st.dataframe(regions_df, hide_index=True)
