class WhatsAppError(Exception):
    """Base exception for WhatsApp related errors"""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class WhatsAppAPIError(WhatsAppError):
    """Exception for WhatsApp API related errors"""
    pass

class WhatsAppTemplateError(WhatsAppError):
    """Exception for WhatsApp template related errors"""
    pass

class WhatsAppMessageError(WhatsAppError):
    """Exception for WhatsApp message related errors"""
    pass

class FirebaseError(Exception):
    """Base exception for Firebase related errors"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class FirebaseAuthError(FirebaseError):
    """Exception for Firebase authentication errors"""
    pass

class FirebaseDataError(FirebaseError):
    """Exception for Firebase data operation errors"""
    pass

class ValidationError(Exception):
    """Exception for data validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)
