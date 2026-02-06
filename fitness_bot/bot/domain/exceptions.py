
class DomainError(Exception):
    pass

class ValidationError(DomainError):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class EntityNotFoundError(DomainError):
    pass

class BusinessRuleViolationError(DomainError):
    pass