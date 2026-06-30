# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValueLengthsToEqual,
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnValuesToBeUnique,
)

_VALID_CONDITIONS = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
_REQUIRED_COLUMNS = ["patient_id", "ho_ten", "cccd", "email", "benh", "ket_qua_xet_nghiem"]


def build_patient_expectation_suite():
    """
    Tạo expectation suite cho patient data dùng GX 1.x API.
    Trả về (suite, validation_definition) để có thể run validate sau.
    """
    ctx = gx.get_context()
    df = pd.read_csv("data/raw/patients_raw.csv")

    # Setup datasource và batch
    ds = ctx.data_sources.add_pandas("patient_ds")
    asset = ds.add_dataframe_asset("patient_asset")
    batch_def = asset.add_batch_definition_whole_dataframe("patient_batch")

    suite = ctx.suites.add(gx.ExpectationSuite(name="patient_data_suite"))

    # 1. patient_id không được null
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="patient_id"))

    # 2. cccd phải có 11 hoặc 12 ký tự (CSV lưu int nên mất số 0 đầu → 11 chữ số)
    suite.add_expectation(ExpectColumnValueLengthsToBeBetween(column="cccd", min_value=11, max_value=12))

    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    suite.add_expectation(ExpectColumnValuesToBeBetween(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    ))

    # 4. benh phải thuộc danh sách hợp lệ
    suite.add_expectation(ExpectColumnValuesToBeInSet(
        column="benh",
        value_set=_VALID_CONDITIONS
    ))

    # 5. email phải match regex pattern
    suite.add_expectation(ExpectColumnValuesToMatchRegex(
        column="email",
        regex=r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    ))

    # 6. patient_id phải unique
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="patient_id"))

    vd = ctx.validation_definitions.add(
        gx.ValidationDefinition(name="patient_vd", data=batch_def, suite=suite)
    )

    return suite, vd, batch_def


def validate_anonymized_data(filepath: str, original_filepath: str = "data/raw/patients_raw.csv") -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    df_original = pd.read_csv(original_filepath)

    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: CCCD không còn trùng với original (đã được thay bằng fake)
    original_cccds = set(df_original["cccd"].astype(str))
    anon_cccds = set(df["cccd"].astype(str))
    overlap = original_cccds & anon_cccds
    if overlap:
        results["success"] = False
        results["failed_checks"].append(
            f"CCCD still contains {len(overlap)} original value(s): {list(overlap)[:3]}"
        )

    # Check 2: Không có null trong các cột quan trọng
    for col in _REQUIRED_COLUMNS:
        if col in df.columns and df[col].isnull().any():
            null_count = df[col].isnull().sum()
            results["success"] = False
            results["failed_checks"].append(f"Column '{col}' has {null_count} null value(s)")

    # Check 3: Số rows phải bằng original
    if len(df) != len(df_original):
        results["success"] = False
        results["failed_checks"].append(
            f"Row count mismatch: anonymized={len(df)}, original={len(df_original)}"
        )

    return results
