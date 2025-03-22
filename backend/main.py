import logging
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from starlette.middleware.cors import CORSMiddleware


REPORTS_ROLE = os.environ.get('REPORTS_ROLE', 'prothetic_user')
AUTH_SERVER_URL = os.environ.get('AUTH_SERVER_URL', 'http://keycloak:8080/')
KC_CLIENT_ID = os.environ.get('KC_CLIENT_ID', 'reports-api')
KC_REALM_NAME = os.environ.get('KC_REALM_NAME', 'reports-realm')
SECRET = os.environ.get('SECRET', 'oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq')


keycloak_openid = KeycloakOpenID(
    server_url=AUTH_SERVER_URL,
    client_id=KC_CLIENT_ID,
    realm_name=KC_REALM_NAME,
    client_secret_key=SECRET
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_info = keycloak_openid.decode_token(token)
        return user_info
    except Exception as e:
        logging.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail='Invalid token')


def check_user_role(required_role: str):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        logging.warning(current_user)
        user_roles = current_user.get('realm_access', {}).get('roles', [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=f'User does not have the required role: {required_role}'
            )
        return current_user

    return role_dependency


@app.get('/reports/')
async def protected_route(
    current_user: dict = Depends(check_user_role(REPORTS_ROLE))
):
    return {
        'user': current_user,
        'report': 'report data 12345'
    }
