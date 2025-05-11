# areas_map.py ──────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="地图区域合集", layout="wide")

import pandas as pd
import plotly.express as px
import requests, json, pathlib, numpy as np
from itertools import cycle
from typing import Dict, Any, List

def run():

    # ───── 路径 / 文件 ─────────────────────────────────────────
    DB = pathlib.Path("database"); DB.mkdir(exist_ok=True)
    XLSX  = DB / "areas_file.xlsx"      # 主数据表
    CITYC = DB / "city_cache.json"      # 城市坐标缓存

    # 颜色池
    COLOR_POOL = px.colors.qualitative.Plotly + px.colors.qualitative.D3

    # ───── 数据加载 ──────────────────────────────────────────
    @st.cache_data
    def load_table(path: pathlib.Path) -> pd.DataFrame:
        if not path.exists():
            st.error(f"缺少数据表：{path}")
            st.stop()
        return pd.read_excel(path, dtype=str)

    def load_geo(path: pathlib.Path) -> Dict[str, Any]:
        if not path.exists():
            st.error(f"GeoJSON 文件不存在：{path}")
            st.stop()
        return json.loads(path.read_text())

    df = load_table(XLSX)

    # ───── UI：区域组 & Token ────────────────────────────────
    groups = sorted(df["地理区域组"].unique())
    sel_group = st.selectbox("选择『地理区域组』", groups)

    token = st.text_input("Mapbox Access Token", type="password")
    if not token:
        st.info("请输入有效 Mapbox Token")
        st.stop()

    # ───── 当前区域组 & GeoJSON ──────────────────────────────
    view = df[df["地理区域组"] == sel_group].copy()
    geo_files = view["geo文件"].unique().tolist()
    if len(geo_files) != 1:
        st.error("同一『地理区域组』应指向唯一 geo文件，请检查 Excel")
        st.stop()

    geo = load_geo(DB / geo_files[0])

    # ───── 颜色映射（按“分组”） ─────────────────────────────
    grp_vals = sorted(view["分组"].unique())
    color_cycle = cycle(COLOR_POOL)
    color_map = {g: next(color_cycle) for g in grp_vals}

    # ───── 拆分州 / 城市 ────────────────────────────────────
    states = view[view["地理类型"] == "州"].copy()
    cities = view[view["地理类型"] == "城市"].copy()

    states["颜色"] = states["分组"].map(color_map)
    states["dummy"] = states["分组"]        # 着色列

    # ───── 州多边形质心（用于中文标签） ───────────────────────
    def poly_centroid(coords: List[List[float]]) -> (float, float):
        lon, lat = zip(*coords)
        return np.mean(lat), np.mean(lon)

    state_centers = {}
    for feat in geo["features"]:
        sid = feat.get("id")
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            lat, lon = poly_centroid(geom["coordinates"][0])
        else:  # MultiPolygon -> 取点最多的环
            biggest = max(geom["coordinates"], key=lambda poly: len(poly[0]))
            lat, lon = poly_centroid(biggest[0])
        state_centers[sid] = {"lat": lat, "lon": lon}

    # ───── 州图层 ────────────────────────────────────────────
    fig = px.choropleth_mapbox(
        states,
        geojson=geo,
        locations="代码",              # 与 feature.id 对齐
        featureidkey="id",
        color="dummy",
        color_discrete_map=color_map,
        opacity=0.35,
        mapbox_style="carto-positron",
        zoom=3, center=dict(lat=37.8, lon=-96),
        hover_data={
            "名称(中文)": True,
            "名称(英文)": True,
            "分组": True,
            "描述": True,
            "dummy": False
        }
    )

    # ───── 城市坐标（缓存 + Geocoding） ──────────────────────
    cache = json.loads(CITYC.read_text()) if CITYC.exists() else {}
    lat, lon, text, hover = [], [], [], []

    for _, row in cities.iterrows():
        code, en = row["代码"], row["名称(英文)"]
        if code in cache:
            coord = cache[code]
        else:
            url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
                   f"{en.replace(' ', '%20')}.json?limit=1&access_token={token}")
            try:
                res = requests.get(url, timeout=10).json()
                lon_, lat_ = res["features"][0]["center"]
                coord = {"lat": lat_, "lon": lon_}
                cache[code] = coord
            except Exception as e:
                st.warning(f"Geocoding '{en}' 失败：{e}")
                continue
        lat.append(coord["lat"]); lon.append(coord["lon"])
        text.append(row["名称(中文)"])
        hover.append(
            f"<b>{row['名称(中文)']}</b><br>"
            f"{row['名称(英文)']}<br>分组：{row['分组']}<br>{row['描述']}"
        )

    CITYC.write_text(json.dumps(cache, ensure_ascii=False, indent=2))

    # ───── 城市散点（固定红色，不入图例） ──────────────────
    fig.add_scattermapbox(
        lat=lat, lon=lon,
        text=text,
        mode="markers+text",
        marker=dict(size=10, color="red"),
        textfont=dict(color="red"),
        hovertext=hover, hoverinfo="text",
        textposition="top right",
        showlegend=False
    )

    # ───── 州中文标签（文本层，无点） ───────────────────────
    state_lat, state_lon, state_txt = [], [], []
    for _, row in states.iterrows():
        center = state_centers.get(row["代码"])
        if center:
            state_lat.append(center["lat"])
            state_lon.append(center["lon"])
            state_txt.append(row["名称(中文)"])

    fig.add_scattermapbox(
        lat=state_lat, lon=state_lon,
        mode="text",
        text=state_txt,
        textfont=dict(size=14, color="black"),
        showlegend=False
    )

    fig.update_layout(mapbox_accesstoken=token, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # ───── 下载按钮 ─────────────────────────────────────────
    csv_bytes = view.to_csv(index=False, encoding="utf-8-sig").encode()
    st.download_button(
        "下载当前区域组数据 (CSV)",
        data=csv_bytes,
        file_name=f"{sel_group}.csv",
        mime="text/csv"
    )

    st.markdown("### 当前区域组数据预览")
    st.dataframe(view, hide_index=True)

# 运行应用
if __name__ == "__main__":
    run()
