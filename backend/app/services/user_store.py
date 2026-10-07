from datetime import datetime,timezone
from uuid import uuid4
from app.core.db import get_connection
from app.core.security import hash_password
from app.models.auth import UserResponse

class UserStore:

    def create_user(self , email:str , password:str , role:str="USER",)->UserResponse:

        user_id = uuid4()

        password_hash = hash_password(password,)

        created_at = datetime.now(timezone.utc,)

        connection = get_connection()

        try:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO users (
                        user_id,
                        email,
                        password_hash,
                        role,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        user_id,
                        email,
                        password_hash,
                        role,
                        created_at,
                    ),
                )

                connection.commit()

        finally:
            connection.close()

        return UserResponse(
            user_id=str(user_id),
            email=email,
            role=role,
        )

    def get_user_by_email(self , email:str):

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        user_id,
                        email,
                        password_hash,
                        role,
                        created_at
                    FROM users
                    WHERE email = %s
                    """,
                    (email,),
                )

                return cursor.fetchone()

        finally:

            connection.close()

    def get_user_by_id(self , user_id:str):

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        user_id,
                        email,
                        password_hash,
                        role,
                        created_at
                    FROM users
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )

                return cursor.fetchone()

        finally:
            connection.close()

