class StartTimeValueError(ValueError):
    def __init__(self, msg: str):
        self.__msg: str = msg
        return

    def __str__(self):
        return f"StartTimeValueError: {str(self.__msg)}"


class EndTimeValueError(ValueError):
    def __init__(self, msg: str):
        self.__msg: str = msg
        return

    def __str__(self):
        return f"EndTimeValueError: {str(self.__msg)}"


class DFAInitializationError(RuntimeError):
    def __init__(self, msg: str):
        self.__msg: str = msg
        return

    def __str__(self):
        return f"DFAInitializationError: {str(self.__msg)}"
