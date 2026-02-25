from repositories.feedback_repository import FeedbackRepository


class FeedbackService:
    def __init__(self, repo: FeedbackRepository):
        self.repo = repo

    def save_feedback(self, text: str, is_ad: bool):
        text = text.strip()
        if not text:
            raise ValueError("Empty text")
        return self.repo.add(text=text, is_ad=is_ad)
