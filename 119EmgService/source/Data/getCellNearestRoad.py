import math
import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Polygon

# — 상수 정의 — 
HALF_SIDE_M = 125  # 250m 격자 반변
MARGIN_DEG = 0.01  # bbox 여유 (≈1km)
CRS = "EPSG:4326"

def meter_to_deg(meters, lat, is_lon=False):
    deg = meters / 111_111
    return deg / math.cos(math.radians(lat)) if is_lon else deg

# 1) 원본 CSV 로드
df = pd.read_csv("gridNearest119Center.csv")

# 2) 전체 bbox 폴리곤 (OSMnx 로드용)
minx, maxx = df.center_lon.min(), df.center_lon.max()
miny, maxy = df.center_lat.min(), df.center_lat.max()
west, east = minx - MARGIN_DEG, maxx + MARGIN_DEG
south, north = miny - MARGIN_DEG, maxy + MARGIN_DEG
bbox_poly = Polygon([
    (west, south), (east, south),
    (east, north),(west, north)
])

# 3) 도로망 불러오기 (한 번)
G = ox.graph_from_polygon(bbox_poly, network_type="drive")
# 노드·엣지 GeoDataFrame 추출
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(CRS)
edges_sindex = edges.sindex

# 4) 격자 셀 GeoDataFrame 생성
cells = []
for idx, row in df.iterrows():
    lon, lat = row.center_lon, row.center_lat
    dx = meter_to_deg(HALF_SIDE_M, lat, is_lon=True)
    dy = meter_to_deg(HALF_SIDE_M, lat)
    poly = Polygon([
        (lon-dx, lat-dy),(lon+dx, lat-dy),
        (lon+dx, lat+dy),(lon-dx, lat+dy)
    ])
    cells.append(poly)

gdf_cells = gpd.GeoDataFrame(df, geometry=cells, crs=CRS)

# 5) Spatial join 으로 “도로 교차하는 격자” 한 번에 필터링
joined = gpd.sjoin(gdf_cells, edges[["geometry"]], how="inner", predicate="intersects")
valid_idxs = joined.index.unique()

filtered = gdf_cells.loc[valid_idxs].copy()

# 6) 가장 가까운 노드로 스냅 (벡터화 or apply)
#    → ox.distance.nearest_nodes 내부에 KD-Tree 최적화돼 있음
filtered["snap_node"] = filtered.apply(
    lambda r: ox.distance.nearest_nodes(G, r.center_lon, r.center_lat),
    axis=1
)

# 7) 노드 좌표로 컬럼 추가
filtered["center_road_lon"] = filtered["snap_node"].map(lambda nid: G.nodes[nid]["x"])
filtered["center_road_lat"] = filtered["snap_node"].map(lambda nid: G.nodes[nid]["y"])
filtered = filtered.drop(columns=["geometry","snap_node"])

# 8) 결과 저장
out_csv = "gridNearest119Center_snapped_filtered.csv"
filtered.to_csv(out_csv, index=False)
print(f"✔️ 완료: {len(filtered)}개 격자 저장 → {out_csv}")
