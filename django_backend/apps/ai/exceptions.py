class AIError(Exception):
    detail = "AI provider error"
    status_code = 503

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class APIRateLimitError(AIError):
    detail = "AI provider rate limit exceeded"
    status_code = 429


class APIProviderError(AIError):
    detail = "AI provider unavailable"
    status_code = 503


class InvalidResponseError(AIError):
    detail = "AI response must be valid JSON"
    status_code = 422
