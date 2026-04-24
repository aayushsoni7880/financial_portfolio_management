from app.services.auth_services import AuthService
from fastapi import Depends

from app.schemas.schemas import SignUpDetails, LoginDetails, \
    ResetPasswordDetails, RefreshToken


class AuthServiceEndpoint:

    @staticmethod
    def login(request: LoginDetails):
        auth_service = AuthService()
        response = auth_service.login(user_name=request.user_name, password=request.password)
        return response

    @staticmethod
    def signup(request: SignUpDetails):
        auth_service = AuthService()
        response = auth_service.sign_up(user_name=request.user_name, password=request.password, email_address=request.email_address)
        return response


    @staticmethod
    def reset_password(request: ResetPasswordDetails):
        auth_service = AuthService()
        response = auth_service.reset_password(email_address=request.email_address)
        return response

    @staticmethod
    def refresh_token(request: RefreshToken):
        auth_service = AuthService()
        response = auth_service.refresh_access_token(refresh_token=request.refresh_token)
        return response

    @staticmethod
    def logout(request: RefreshToken, user = Depends(AuthService.get_current_user)):
        auth_service = AuthService()
        response = auth_service.logout(refresh_token=request.refresh_token)
        return response
