"""
Database-related infrastructure exceptions.

These are internal exceptions that should be caught at middleware
and converted to generic error responses (not exposed to clients).
"""


class DatabaseException(Exception):
    """Base exception for database operations."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class DatabaseConnectionError(DatabaseException):
    """Raised when database connection fails."""

    def __init__(self, host: str, original_error: Exception | None = None) -> None:
        super().__init__(
            message=f"Failed to connect to database at {host}",
            original_error=original_error,
        )
        self.host = host


class QueryExecutionError(DatabaseException):
    """Raised when a database query fails."""

    def __init__(self, query: str, original_error: Exception | None = None) -> None:
        super().__init__(
            message="Database query execution failed",
            original_error=original_error,
        )
        self.query = query


class DocumentNotFoundError(DatabaseException):
    """Raised when a document is not found in the database."""

    def __init__(self, collection: str, key: str) -> None:
        super().__init__(message=f"Document not found: {collection}/{key}")
        self.collection = collection
        self.key = key


class DuplicateDocumentError(DatabaseException):
    """Raised when attempting to insert a duplicate document."""

    def __init__(self, collection: str, key: str) -> None:
        super().__init__(message=f"Duplicate document: {collection}/{key}")
        self.collection = collection
        self.key = key
