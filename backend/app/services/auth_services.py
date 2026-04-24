import uuid
from os import access

from fastapi import Depends, FastAPI, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.enums.enums import AuthTokenConfig, AdminDetails
from app.schemas.schemas import AuthServiceResponseModel, TokenData, MailHandlerRequest

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from app.core.config import settings
from app.core.database import SqlDatabase
from app.services.gmail_mail_sent import GmailMailSent
import logging
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class AuthService():

    def __init__(self):
        self.db = SqlDatabase(db_path=settings.sqlite_path)
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto",  bcrypt__rounds=12)

    @staticmethod
    async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            db = SqlDatabase(db_path=settings.sqlite_path)
            print("Verifying the token")
            payload = jwt.decode(token, AuthTokenConfig.SECRET_KEY.value, algorithms=[AuthTokenConfig.ALGORITHM.value])
            logger.info(f"Payload: {payload}")
            username = payload.get("sub")
            userid = payload.get('id')
            jti = payload.get("jti")
            if username is None:
                raise credentials_exception
            _ , is_revoked = db.get_token_from_db(jti)
            if is_revoked:
                raise JWTError
            token_data = TokenData(username=username, userid=userid)
            print("Token Verified")
        except JWTError:
            print("Token Not verified")
            raise credentials_exception

        user = db.get_user_by_id(user_id=token_data.userid)
        if user is None:
            raise credentials_exception
        return user


    def _hash_password(self, password: str):
        return self.pwd_context.hash(password + settings.PEPPER)

    def _verify_password(self, plain, hashed):
        return self.pwd_context.verify(plain + settings.PEPPER, hashed)

    def _create_access_token(self, data: dict):
        to_encode = data.copy()
        to_encode.update({"type": "access"})
        expire = datetime.utcnow() + timedelta(minutes=AuthTokenConfig.ACCESS_TOKEN_EXPIRE_MINUTES.value)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, AuthTokenConfig.SECRET_KEY.value, algorithm=AuthTokenConfig.ALGORITHM.value)

    def _create_refresh_token(self, data: dict):
        to_encode = data.copy()
        to_encode.update({"type": "refresh"})
        expire = datetime.utcnow() + timedelta(minutes=AuthTokenConfig.REFRESH_TOKEN_EXPIRE_MINUTES.value)
        to_encode.update({"exp": expire})

        # Save refresh token database
        self.db.save_refresh_token(to_encode)
        return jwt.encode(to_encode, AuthTokenConfig.SECRET_KEY.value, algorithm=AuthTokenConfig.ALGORITHM.value)

    def refresh_access_token(self, refresh_token: str):

        try:
            payload = jwt.decode(refresh_token, AuthTokenConfig.SECRET_KEY.value, algorithms=[AuthTokenConfig.ALGORITHM.value])

            if payload["type"] != "refresh":
                return AuthServiceResponseModel(success=False, message="Invalid Token")

            jti = payload["jti"]

            token_in_db, is_revoked = self.db.get_token_from_db(jti)

            if not token_in_db or is_revoked:
                raise HTTPException(status_code=401, detail="Token Revoked")

            access_token =  self._create_access_token(data = {"sub": payload["sub"], "id": payload["id"],
                                "jti": payload["jti"]})
            logger.info("Refresh Token Generate new access token")
            return AuthServiceResponseModel(success=True, message="New access token created.",
                                            access_token=access_token)
        except Exception as err:
            raise HTTPException(status_code=401, detail="Token Revoked")

    def login(self, user_name: str, password: str):
        try:
            user_details = self.db.get_user_by_name(user_name)
            if user_details and user_details.id:
                if self._verify_password(password, user_details.password):
                    jti = str(uuid.uuid4())  # Json Token Identifier (JTI)
                    access_token = self._create_access_token(
                        data = {"sub": user_details.user_name,
                                "id": user_details.id,
                                "jti": jti
                                }
                    )
                    refresh_token = self._create_refresh_token(data = {"sub": user_details.user_name, "id": user_details.id, "jti": jti})
                    return AuthServiceResponseModel(success=True, message="Login Successfully.", id=user_details.id, access_token=access_token, refresh_token=refresh_token)
                return AuthServiceResponseModel(success=False, message="Invalid Password")
            else:
                return AuthServiceResponseModel(success=False, message="User does not exist")
        except Exception as err:
            return AuthServiceResponseModel(success=False, message=f"{str(err)}")

    def sign_up(self, user_name:str, password: str, email_address: str):
        try:
            user_details = self.db.get_user_by_name(user_name)
            logger.info(user_details)
            if user_details:
                return AuthServiceResponseModel(success=False, message="User already exist")

            hashed_password = self._hash_password(password)
            user_id = self.db.insert_user(user_name, hashed_password, email_address)
            return AuthServiceResponseModel(success=True, message="Signup successfull.", id=user_id)
        except Exception as err:
            print(f"Err: {err}")
            return AuthServiceResponseModel(success=False, message=f"{str(err)}")

    def reset_password(self, email_address):
        try:
            user_details = self.db.get_user_by_email(email_address)

            if user_details is None:
                return AuthServiceResponseModel(success=False, message="Invalid email address")

            new_password = str(uuid.uuid4())
            hashed_new_password = self._hash_password(new_password)
            self.db.reset_password(email_address, hashed_new_password)
            mail = GmailMailSent(AdminDetails.USER_NAME.value, AdminDetails.EMAIL_ADDRESS.value)
            mail_data = MailHandlerRequest(message=f"Password reset, your new password is {new_password}, please login with this password.", receiver_email_address=user_details.email_address)
            mail.sent_mail(mail_data)
            return AuthServiceResponseModel(success=False, message="we have reset your password, please check your mail for new password")
        except Exception as err:
            return AuthServiceResponseModel(success=False, message=f"{str(err)}")

    def logout(self, refresh_token):
        try:
            payload = jwt.decode(refresh_token, AuthTokenConfig.SECRET_KEY.value,
                                 algorithms=[AuthTokenConfig.ALGORITHM.value])

            if payload["type"] != "refresh":
                return AuthServiceResponseModel(success=False, message="Invalid Token")

            jti = payload["jti"]

            self.db.revoke_refresh_token(jti)
            return AuthServiceResponseModel(success=True, message=f"Logout Successfully.")

        except Exception as err:
            return AuthServiceResponseModel(success=False, message=f"{str(err)}")
