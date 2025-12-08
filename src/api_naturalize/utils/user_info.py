from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='users/login')


def get_user_info(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get(
            "user_id")

        if email is None or role is None or user_id is None:
            raise credentials_exception

    except JWTError:

        raise credentials_exception

    return {"role": role, "email": email, "user_id": user_id}