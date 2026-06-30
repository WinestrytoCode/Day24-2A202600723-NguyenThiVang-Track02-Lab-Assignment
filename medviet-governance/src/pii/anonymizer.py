# src/pii/anonymizer.py
import hashlib
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

def _fake_cccd() -> str:
    return fake.numerify(text="############")  # 12 chữ số ngẫu nhiên

def _fake_phone() -> str:
    prefixes = ["03", "05", "07", "08", "09"]
    prefix = fake.random_element(prefixes)
    return prefix + fake.numerify(text="########")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "replace" : thay bằng fake data (dùng Faker)
        - "mask"    : che ký tự giữa bằng *
        - "hash"    : SHA-256 one-way hash
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": _fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": _fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "PERSON": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 6, "from_end": False}),
                "EMAIL_ADDRESS": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 6, "from_end": False}),
                "VN_CCCD": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 8, "from_end": False}),
                "VN_PHONE": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 6, "from_end": False}),
            }
        elif strategy == "hash":
            operators = {
                entity: OperatorConfig("custom", {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()[:16]})
                for entity in ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
            }
        else:
            operators = {}

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - ho_ten, dia_chi, email: dùng anonymize_text()
        - cccd: replace trực tiếp bằng fake CCCD
        - so_dien_thoai: replace trực tiếp bằng fake phone
        - benh, ket_qua_xet_nghiem, patient_id: GIỮ NGUYÊN
        """
        df_anon = df.copy()

        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = df_anon["ho_ten"].astype(str).apply(
                lambda x: self.anonymize_text(x, strategy="replace")
            )
        if "email" in df_anon.columns:
            df_anon["email"] = df_anon["email"].astype(str).apply(
                lambda x: self.anonymize_text(x, strategy="replace")
            )
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = df_anon["dia_chi"].astype(str).apply(
                lambda x: self.anonymize_text(x, strategy="replace")
            )
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [_fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [_fake_phone() for _ in range(len(df_anon))]

        return df_anon

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
