import inspect

class Logger:
    LEVEL_DEBUG = 0
    LEVEL_INFO = 1
    LEVEL_WARNING = 2
    LEVEL_ERROR = 3
    LEVEL_CRITICAL = 4

    MODE_VERBOSE = 0
    MODE_COMPACT = 1

    def __init__(self, mode=MODE_VERBOSE):
        self.mode = mode

    def log(self, msg, level=LEVEL_INFO):
        self.output(msg, level)

    def output(self, msg, level):
        # print(msg)
        if self.mode == self.MODE_VERBOSE:
            stack = inspect.stack()[2]
            msg = f"[{stack.filename}:{stack.lineno} on {stack.function}] | " + msg

        if level == Logger.LEVEL_DEBUG:
            self.debug(msg)
        elif level == Logger.LEVEL_INFO:
            self.info(msg)
        elif level == Logger.LEVEL_WARNING:
            self.warning(msg)
        elif level == Logger.LEVEL_ERROR:
            self.error(msg)
        elif level == Logger.LEVEL_CRITICAL:
            self.critical(msg)

    def debug(self, msg):
        print("[DEBUG] " + msg)

    def info(self, msg):
        print("[INFO] " + msg)

    def warning(self, msg):
        print("[WARNING] " + msg)

    def error(self, msg):
        print("[ERROR] " + msg)

    def critical(self, msg):
        print("[CRITICAL] " + msg)

