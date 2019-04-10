
class UserInputException(Exception):
    pass


class IncompleteJobTemplateException(UserInputException):
    pass


class InvalidFilePathException(UserInputException):
    pass


class FileDoesNotExistException(UserInputException):
    pass


class ProjectDoesNotExistException(UserInputException):
    pass


class JobDoesNotExistException(UserInputException):
    pass


class WorkflowConfigurationNotFoundException(UserInputException):
    pass


class WorkflowNotFound(UserInputException):
    pass


class InvalidWorkflowFileException(UserInputException):
    pass


class ShareGroupNotFound(UserInputException):
    pass


class JobStrategyNotFound(UserInputException):
    pass
