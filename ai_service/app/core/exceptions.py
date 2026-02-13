from fastapi import HTTPException,status

class APIProviderError(HTTPException):
    def __init__ (self,detail:str="AI provider error"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY,detail=detail)


class APIRateLimitError(HTTPException):
    def __init__(self,detail:str="AI provider rate limit exceeded"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=detail)


class InvalidResponseError(HTTPException):
    def __init__(self,detail:str="Invalid response from AI provider"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
