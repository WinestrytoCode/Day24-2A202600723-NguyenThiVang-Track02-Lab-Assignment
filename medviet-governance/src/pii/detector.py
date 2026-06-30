# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

_VN_NAME_REGEX = (
    r"(?:(?:Ông|Bà|Cô|Anh|Chị|Em|Thầy|Quý\s+(?:ông|bà|cô))\s+)?"
    r"[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯ"
    r"ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ]"
    r"[a-zàáâãèéêìíòóôõùúăđĩũơư"
    r"ạảấầẩẫậắằẳẵặẹẻẽềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+"
    r"(?:\s+"
    r"[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯ"
    r"ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ]"
    r"[a-zàáâãèéêìíòóôõùúăđĩũơư"
    r"ạảấầẩẫậắằẳẵặẹẻẽềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+"
    r"){0,3}"
)

_CCCD_PATTERNS = [
    Pattern(name="cccd_12", regex=r"(?<!\d)\d{12}(?!\d)", score=0.9),
    Pattern(name="cccd_11", regex=r"(?<!\d)\d{11}(?!\d)", score=0.85),
]

_PHONE_PATTERNS = [
    Pattern(name="vn_phone_full",    regex=r"(?<!\d)0[35789]\d{8}(?!\d)", score=0.9),
    Pattern(name="vn_phone_no_zero", regex=r"(?<!\d)[35789]\d{8}(?!\d)",  score=0.85),
]

_NAME_PATTERNS = [Pattern(name="vn_name", regex=_VN_NAME_REGEX, score=0.6)]


def _make_recognizers(lang: str):
    return [
        PatternRecognizer(supported_entity="VN_CCCD",  supported_language=lang,
                          patterns=_CCCD_PATTERNS,
                          context=["cccd", "căn cước", "chứng minh", "cmnd"]),
        PatternRecognizer(supported_entity="VN_PHONE", supported_language=lang,
                          patterns=_PHONE_PATTERNS),
        PatternRecognizer(supported_entity="PERSON",   supported_language=lang,
                          patterns=_NAME_PATTERNS),
    ]


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    Dùng model đa ngôn ngữ xx_ent_wiki_sm vì spaCy chưa có model vi chính thức.
    Hỗ trợ cả language="xx" và language="vi" để tương thích với test.
    """
    # --- TASK 2.2.3 ---
    # Đăng ký xx_ent_wiki_sm cho cả lang_code "xx" và "vi" để analyze(language="vi") hoạt động
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "xx", "model_name": "xx_ent_wiki_sm"},
            {"lang_code": "vi", "model_name": "xx_ent_wiki_sm"},
        ]
    })
    nlp_engine = provider.create_engine()

    # --- TASK 2.2.4 ---
    # Đăng ký recognizer cho cả "xx" và "vi" để analyze() hoạt động với cả hai
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["xx", "vi"])
    for lang in ["xx", "vi"]:
        for rec in _make_recognizers(lang):
            analyzer.registry.add_recognizer(rec)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities: PERSON, EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    return analyzer.analyze(
        text=text,
        language="xx",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
