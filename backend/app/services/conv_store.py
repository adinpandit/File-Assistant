from datetime import datetime,timezone
from uuid import UUID , uuid4
from app.models.history import ConversationResponse,MessageResponse
from app.core.db import get_connection

class ConversationStore:

    def create_conversation(self,user_id:str,title:str="New Conversation",)->ConversationResponse:

        conversation_id = uuid4()
        now = datetime.now(timezone.utc)

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO conversations(
                        conversation_id,
                        user_id,
                        title,
                        created_at,
                        updated_at
                    )
                    values(%s,%s,%s,%s,%s)
                    RETURNING
                        conversation_id,
                        user_id,
                        title,
                        created_at,
                        updated_at
                    ''',
                    (
                        conversation_id,
                        UUID(user_id),
                        title,
                        now,
                        now,
                    ),
                )

                row = cursor.fetchone()

                connection.commit()

        finally:
            connection.close()

        return self._conversation_from_row(row)

    def get_conversation(self,conversation_id:str,user_id:str,)->ConversationResponse|None:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        conversation_id,
                        user_id,
                        title,
                        created_at,
                        updated_at
                    FROM conversations
                    WHERE conversation_id = %s
                    AND user_id = %s
                    ''',
                    (
                        UUID(conversation_id),
                        UUID(user_id)
                    ),
                )

                row = cursor.fetchone()

        finally:
            connection.close()

        if row is None:
            return None

        return self._conversation_from_row(row)

    def list_conversations(self,user_id:str,)->list[ConversationResponse]:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        conversation_id,
                        user_id,
                        title,
                        created_at,
                        updated_at
                    FROM conversations
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    ''',
                    (
                        UUID(user_id),
                    ),
                )

                rows = cursor.fetchall()

        finally:
            connection.close()

        return [
            self._conversation_from_row(row)
            for row in rows
        ]

    def delete_conversation(self,conversation_id:str,user_id:str,)->bool:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    DELETE FROM conversations
                    WHERE conversation_id = %s
                    AND user_id = %s
                    ''',
                    (
                        UUID(conversation_id),
                        UUID(user_id),
                    ),
                )

                deleted = cursor.rowcount > 0

            connection.commit()

        finally:
            connection.close()

        return deleted

    def add_message(self,conversation_id:str,user_id:str,role:str,content:str,)->MessageResponse|None:

        message_id = uuid4()
        now = datetime.now(timezone.utc)

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT conversation_id
                    FROM conversations
                    WHERE conversation_id = %s
                    AND user_id = %s
                    ''',
                    (
                        UUID(conversation_id),
                        UUID(user_id),
                    ),
                )

                conversation = cursor.fetchone()

                if conversation is None:
                    return None

                cursor.execute(
                    '''
                    INSERT INTO messages (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING
                        message_id,
                        conversation_id,
                        role,
                        content,
                        created_at
                    ''',
                    (
                        message_id,
                        UUID(conversation_id),
                        role,
                        content,
                        now,
                    ),
                )

                row = cursor.fetchone()

                cursor.execute(
                    """
                    UPDATE conversations
                    SET updated_at = %s
                    WHERE conversation_id = %s
                    """,
                    (
                        now,
                        UUID(conversation_id),
                    ),
                )

                connection.commit()

        finally:
            connection.close()

        return self._message_from_row(row)

    def list_messages(self,conversation_id:str,user_id:str,)->list[MessageResponse]:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        message_id,
                        conversation_id,
                        role,
                        content,
                        created_at
                    FROM messages
                    WHERE conversation_id=%s
                    AND conversation_id IN(
                        SELECT conversation_id
                        FROM conversations
                        WHERE conversation_id = %s
                        AND user_id = %s
                    )
                    ORDER BY created_at ASC
                    ''',
                    (
                        UUID(conversation_id),
                        UUID(conversation_id),
                        UUID(user_id)
                    ),
                )

                rows = cursor.fetchall()
        finally:
            connection.close()

        return [
            self._message_from_row(row)
            for row in rows
        ]

    def get_recent_messages(self,conversation_id:str,user_id:str,limit:int=10,)->list[MessageResponse]:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        message_id,
                        conversation_id,
                        role,
                        content,
                        created_at
                    FROM messages
                    WHERE conversation_id = %s
                    AND conversation_id IN(
                        SELECT conversation_id
                        FROM conversations
                        WHERE conversation_id = %s
                        AND user_id = %s
                    )
                    ORDER BY created_at DESC
                    LIMIT %s
                    ''',
                    (
                        UUID(conversation_id),
                        UUID(conversation_id),
                        UUID(user_id),
                        limit,
                    ),
                )

                rows = cursor.fetchall()

        finally:
            connection.close()

        rows.reverse()

        return [
            self._message_from_row(row)
            for row in rows
        ]

    @staticmethod
    def _conversation_from_row(row) -> ConversationResponse:

        return ConversationResponse(
            conversation_id = str(row["conversation_id"]),
            user_id = str(row["user_id"]),
            title = row["title"],
            created_at = row["created_at"],
            updated_at = row["updated_at"],
        )
    
    @staticmethod
    def _message_from_row(row)->MessageResponse:

        return MessageResponse(
            message_id = str(row["message_id"]),
            conversation_id = str(row["conversation_id"]),
            role = row["role"],
            content = row["content"],
            created_at = row["created_at"]
        )

    
