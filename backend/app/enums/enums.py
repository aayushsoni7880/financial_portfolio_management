from enum import Enum


class AdminDetails(Enum):
    EMAIL_ADDRESS = "soniaayush0044@gmail.com"
    USER_NAME = "Aayush Soni"
    SECRET_KEY = "bpwy exxc nkkn eofg"

class AuthTokenConfig(Enum):
    SECRET_KEY = "default-token-key"  # use env in prod
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 5
    REFRESH_TOKEN_EXPIRE_MINUTES = 10