import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point

# CSV 불러오기
df = pd.read_csv("gridRoadTimeFixed.csv")

# 이상치 보정
q1 = df["road_travel_time_s"].quantile(0.25)
q3 = df["road_travel_time_s"].quantile(0.75)
iqr = q3 - q1
upper_bound = q3 + 1.5 * iqr
df["road_travel_time_clipped"] = df["road_travel_time_s"].clip(upper=upper_bound)

# 좌표 정리
df['service_lon_clean'] = df['service_lon'].astype(str).str.split(";").str[0].astype(float)
df['service_lat_clean'] = df['service_lat'].astype(str).str.split(";").str[0].astype(float)

# GeoDataFrame 변환 및 Web Mercator로
gdf_grid = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.center_road_lon, df.center_road_lat),
    crs="EPSG:4326"
).to_crs(epsg=3857)

gdf_service = gpd.GeoDataFrame(
    df.drop_duplicates(subset=["service_name"]),
    geometry=gpd.points_from_xy(df.drop_duplicates(subset=["service_name"])['service_lon_clean'],
                                df.drop_duplicates(subset=["service_name"])['service_lat_clean']),
    crs="EPSG:4326"
).to_crs(epsg=3857)

# 시각화 및 저장
fig, ax = plt.subplots(figsize=(16, 16), dpi=300)

gdf_grid.plot(
    column="road_travel_time_clipped",
    cmap="RdYlBu_r",
    legend=True,
    markersize=10,
    ax=ax,
    alpha=0.7,
    label="Grid Center"
)

gdf_service.plot(
    ax=ax,
    color="black",
    marker="^",
    markersize=50,
    label="Fire Station / 119 Center"
)

ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

ax.set_title("서울시 고해상도 주행시간 지도 및 소방기관 위치", fontsize=20)
ax.set_axis_off()
plt.legend()

plt.tight_layout()
plt.savefig("seoul_travel_time_highres.png")
