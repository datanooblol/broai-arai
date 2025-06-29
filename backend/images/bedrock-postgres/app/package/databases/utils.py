from datetime import datetime, timezone

def now_utc():
    return datetime.now(timezone.utc)

class BadRequestError(Exception):
    def __init__(self, detail: str):
        self.detail = detail