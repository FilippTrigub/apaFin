
class RequestCounter:
    def __init__(self):
        self.i = 0

    def count(self, request):
        self.i += 1
        return True
