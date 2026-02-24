from sqlalchemy.orm import Session
from backend_server.models import Feedback


class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, text: str, is_ad: bool) -> Feedback:
        fb = Feedback(text=text, is_ad=is_ad)
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb
