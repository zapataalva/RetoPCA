# Manejo de errores y excepciones de la aplicación


class BusinessException(Exception):
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR") -> None:
        super().__init__(message)
        self.error_code = error_code


class InvalidFileTypeException(BusinessException):
    def __init__(self, filename: str) -> None:
        super().__init__(
            f"Tipo de archivo no válido: {filename}",
            error_code="INVALID_FILE_TYPE",
        )
        self.filename = filename


class InvalidJsonException(BusinessException):
    def __init__(self) -> None:
        super().__init__("JSON inválido", error_code="INVALID_JSON")


class InvalidOverridesException(BusinessException):
    def __init__(self) -> None:
        super().__init__("Overrides inválido (debe ser JSON)", error_code="INVALID_OVERRIDES")


class SwaggerBaseUrlMissingException(BusinessException):
    def __init__(self) -> None:
        super().__init__("Swagger sin base_url", error_code="SWAGGER_BASE_URL_MISSING")


class ScanNotFoundException(BusinessException):
    def __init__(self, scan_id: str) -> None:
        super().__init__(f"Scan con ID {scan_id} no encontrado", error_code="SCAN_NOT_FOUND")
        self.scan_id = scan_id


class ScanPersistenceException(BusinessException):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="SCAN_PERSISTENCE_ERROR")


class ScannerExecutionException(BusinessException):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="SCANNER_EXECUTION_ERROR")
