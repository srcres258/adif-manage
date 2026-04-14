class AdifManageError(Exception):
    pass


class AdifParseError(AdifManageError):
    pass


class CommandError(AdifManageError):
    pass


class WriteError(AdifManageError):
    pass
