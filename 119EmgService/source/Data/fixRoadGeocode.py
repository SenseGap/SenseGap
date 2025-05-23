import pandas as pd

def fix_and_export_csv_for_excel(input_csv: str, output_csv: str):
    """
    1) UTF-8로 CSV 읽기
    2) Unnamed 컬럼 제거
    3) 컬럼명 재부여 (필요 시)
    4) UTF-8 BOM을 포함해 CSV 저장 (Excel 호환)
    """
    # 1) 읽기
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    # 2) Unnamed 컬럼 제거
    df = df.loc[:, ~df.columns.str.contains(r'^Unnamed')]
    
    # 3) 필요 시 컬럼명 재정의
    expected_cols = [
        "i", "j", "center_lon", "center_lat", "grid_id", "district",
        "service_name", "service_lon", "service_lat", "area_ratio",
        "center_road_lon", "center_road_lat"
    ]
    if len(df.columns) == len(expected_cols):
        df.columns = expected_cols
    
    # 4) UTF-8 BOM 포함하여 저장
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"✔️ 저장 완료: {output_csv}")

if __name__ == "__main__":
    fix_and_export_csv_for_excel(
        input_csv="gridNearest119Center_snapped_filtered.csv",
        output_csv="gridNearest119CenterRoadFixed.csv"
    )
