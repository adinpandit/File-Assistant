import psycopg
from psycopg.rows import dict_row
from app.config import settings

def get_connection():
    return psycopg.connect(settings.database_url , row_factory=dict_row)

def initialize_database()->None:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                '''
                CREATE TABLE If NOT EXISTS users (
                    user_id UUID PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                '''
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS documents (
                    document_id UUID PRIMARY KEY,
                    user_id UUID NOT NULL
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,
                    filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(20) NOT NULL,
                    upload_time TIMESTAMPTZ NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL
                )
                '''
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_documents_user_id
                ON documents(user_id)
                """
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS conversations(
                    conversation_id UUID PRIMARY KEY,
                    user_id UUID NOT NULL
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                '''
            )

            cursor.execute(
                '''
                CREATE INDEX IF NOT EXISTS 
                idx_conversations_user_id
                ON conversations(user_id)
                '''
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS messages(
                message_id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL
                    REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
                )
                '''
            )

            cursor.execute(
                '''
                CREATE INDEX IF NOT EXISTS
                idx_messages_conversation_id
                ON messages(conversation_id)
                '''
            )

        connection.commit()

    finally:
        connection.close()