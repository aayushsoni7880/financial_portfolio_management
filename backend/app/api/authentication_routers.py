from fastapi import APIRouter

from backend.app.services.auth_service_endpoints import AuthServiceEndpoint
from backend.app.schemas.schemas import AuthServiceResponseModel

auth_router = APIRouter()

auth_router.add_api_route("/login", AuthServiceEndpoint.login,
                     methods=["POST"],
                     response_model=AuthServiceResponseModel)

auth_router.add_api_route("/signup", AuthServiceEndpoint.signup,
                     methods=["POST"],
                     response_model=AuthServiceResponseModel)

auth_router.add_api_route("/reset_password", AuthServiceEndpoint.reset_password,
                     methods=["POST"],
                     response_model=AuthServiceResponseModel)

auth_router.add_api_route("/refresh_token", AuthServiceEndpoint.refresh_token,
                     methods=["POST"],
                     response_model=AuthServiceResponseModel)

auth_router.add_api_route("/logout", AuthServiceEndpoint.logout,
                     methods=["POST"],
                     response_model=AuthServiceResponseModel)