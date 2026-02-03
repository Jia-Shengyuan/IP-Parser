
class Debug:
    ENABLED = True
	
    _YELLOW = "\033[33m"
    _RED = "\033[31m"
    _RESET = "\033[0m"

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        cls.ENABLED = bool(enabled)

    @classmethod
    def log(cls, message: str) -> None:
        if not cls.ENABLED:
            return
        print(message)

    @classmethod
    def log_warning(cls, message: str) -> None:
        if not cls.ENABLED:
            return
        prefix = f"{cls._YELLOW}WARNING{cls._RESET} "
        print(prefix + message)

    @classmethod
    def log_error(cls, message: str) -> None:
        if not cls.ENABLED:
            return
        prefix = f"{cls._RED}ERROR{cls._RESET} "
        print(prefix + message)
    
