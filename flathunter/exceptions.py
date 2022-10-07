class BotBlockedException(Exception):
    """
    A small class that defines a Bot Blocked Exception.
    """
    def __init__(self, message):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value

class UserDeactivatedException(Exception):
    """
    A small class that defines a UserDeactivated Exception.
    """
    def __init__(self, message):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value
