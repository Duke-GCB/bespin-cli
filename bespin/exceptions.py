
class UserInputException(Exception):
    pass


class IncompleteJobFileException(UserInputException):
    pass


class InvalidFilePathException(UserInputException):
    pass


class FileDoesNotExistException(UserInputException):
    pass


class ProjectDoesNotExistException(UserInputException):
    pass


class JobDoesNotExistException(UserInputException):
    pass

