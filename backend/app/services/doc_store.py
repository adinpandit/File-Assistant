from datetime import datetime, timezone
from uuid import UUID

from app.core.doc_store_initialize import get_connection
from app.models.document import DocumentResponse


class DocumentStore:

    def create_document(self,document_id: str,user_id: str,filename: str,file_type: str,page_count: int,chunk_count: int,) -> DocumentResponse:

        upload_time = datetime.now(timezone.utc,)

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        document_id,
                        user_id,
                        filename,
                        file_type,
                        upload_time,
                        page_count,
                        chunk_count
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        document_id,
                        user_id,
                        filename,
                        file_type,
                        upload_time,
                        page_count,
                        chunk_count
                    """,
                    (
                        UUID(document_id),
                        UUID(user_id),
                        filename,
                        file_type,
                        upload_time,
                        page_count,
                        chunk_count,
                    ),
                )

                row = cursor.fetchone()

            connection.commit()

        finally:
            connection.close()

        return self._row_to_document(row)

    def get_document(self,document_id: str,user_id: str,) -> DocumentResponse | None:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        document_id,
                        user_id,
                        filename,
                        file_type,
                        upload_time,
                        page_count,
                        chunk_count
                    FROM documents
                    WHERE document_id = %s
                    AND user_id = %s
                    """,
                    (
                        UUID(document_id),
                        UUID(user_id),
                    ),
                )

                row = cursor.fetchone()

        finally:
            connection.close()

        if row is None:
            return None

        return self._row_to_document(row)

    def list_documents(self,user_id: str,) -> list[DocumentResponse]:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        document_id,
                        user_id,
                        filename,
                        file_type,
                        upload_time,
                        page_count,
                        chunk_count
                    FROM documents
                    WHERE user_id = %s
                    ORDER BY upload_time DESC
                    """,
                    (UUID(user_id),),
                )

                rows = cursor.fetchall()

        finally:
            connection.close()

        return [
            self._row_to_document(row)
            for row in rows
        ]

    def delete_document(self,document_id: str,user_id: str,) -> bool:

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM documents
                    WHERE document_id = %s
                    AND user_id = %s
                    """,
                    (
                        UUID(document_id),
                        UUID(user_id),
                    ),
                )

                deleted = cursor.rowcount > 0

            connection.commit()

        finally:
            connection.close()

        return deleted

    @staticmethod
    def _row_to_document(row) -> DocumentResponse:
        return DocumentResponse(
            document_id=str(
                row["document_id"]
            ),
            user_id=str(
                row["user_id"]
            ),
            filename=row["filename"],
            file_type=row["file_type"],
            upload_time=row["upload_time"],
            page_count=row["page_count"],
            chunk_count=row["chunk_count"],
        )