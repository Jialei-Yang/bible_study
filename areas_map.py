# areas_map.py ──────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="地图区域合集", layout="wide")

import pandas as pd, pathlib, json, requests, plotly.express as px
from itertools import cycle
from typing import Dict, Optional, List, Any
import io

# ─── 常量 / 路径 ───────────────────────────────────────────
DB = pathlib.Path("database"); DB.mkdir(exist_ok=True)
XLSX  = DB / "areas_file.xlsx"
CITYC = DB / "city_cache.json"
COLOR_POOL = px.colors.qualitative.Plotly + px.colors.qualitative.D3

# ─── 读取表 ───────────────────────────────────────────────
@st.cache_data
def load_table(path: pathlib.Path) -> pd.DataFrame:
    return pd.read_excel(path, dtype=str)

def load_geo(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        st.error(f"❌ GeoJSON 文件不存在：{path}")
        st.stop()
    return json.loads(path.read_text())

df = load_table(XLSX)

# ─── UI：区域组选择 & Token ──────────────────────────────
groups = sorted(df["地理区域组"].unique())
sel_group = st.selectbox("选择『地理区域组』", groups)

token = st.text_input("Mapbox Access Token", type="password")
if not token:
    st.info("请输入有效 Mapbox Token")
    st.stop()

# ─── 当前区域组 & GeoJSON 文件 ──────────────────────────
view = df[df["地理区域组"] == sel_group].copy()
geo_files = view["geo文件"].unique().tolist()
if len(geo_files) != 1:
    st.error("同一『地理区域组』应指向唯一 geo文件，请检查 Excel")
    st.stop()

geo = load_geo(DB / geo_files[0])

# ─── 颜色映射（按“分组”） ──────────────────────────────
groups_in_df = sorted(view["分组"].unique())
color_cycle = cycle(COLOR_POOL)
color_map = {g: next(color_cycle) for g in groups_in_df}

# ─── 数据拆分 ───────────────────────────────────────────
states = view[view["地理类型"] == "州"].copy()
cities = view[view["地理类型"] == "城市"].copy()
states["颜色"] = states["分组"].map(color_map)
states["dummy"] = states["分组"]  # 着色列

# ─── 州层 ───────────────────────────────────────────────
fig = px.choropleth_mapbox(
    states,
    geojson=geo,
    locations="代码",
    featureidkey="id",
    color="dummy",
    color_discrete_map=color_map,
    hover_data={
        "名称(中文)": True,
        "名称(英文)": True,
        "分组": True,
        "描述": True,
        "dummy": False
    },
    opacity=0.35,
    mapbox_style="carto-positron",
    zoom=3, center=dict(lat=37.8, lon=-96)
)

# ─── 城市坐标（缓存 + Geocoding） ──────────────────────
cache = json.loads(CITYC.read_text()) if CITYC.exists() else {}
lat, lon, hovertext = [], [], []

for _, row in cities.iterrows():
    code, en_name = row["代码"], row["名称(英文)"]
    if code in cache:
        coord = cache[code]
    else:
        url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
               f"{en_name.replace(' ', '%20')}.json?limit=1&access_token={token}")
        try:
            res = requests.get(url, timeout=10).json()
            lon_, lat_ = res["features"][0]["center"]
            coord = {"lat": lat_, "lon": lon_}
            cache[code] = coord
        except Exception as e:
            st.warning(f"Geocoding '{en_name}' 失败：{e}")
            continue
    lat.append(coord["lat"])
    lon.append(coord["lon"])
    hovertext.append(
        f"<b>{row['名称(中文)']}</b><br>"
        f"{row['名称(英文)']}<br>"
        f"分组：{row['分组']}<br>"
        f"{row['描述']}"
    )

CITYC.write_text(json.dumps(cache, ensure_ascii=False, indent=2))

# ─── 城市散点（固定红色，不入图例） ──────────────────
fig.add_scattermapbox(
    lat=lat,
    lon=lon,
    mode="markers+text",
    text=[row["名称(中文)"] for _, row in cities.iterrows()],
    marker=dict(size=10, color="red"),
    hovertext=hovertext,
    hoverinfo="text",
    textposition="top right",
    showlegend=False           # ← 隐藏图例条目
)

fig.update_layout(mapbox_accesstoken=token, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)


st.markdown("### 当前区域组数据预览")
st.dataframe(view, hide_index=True)
