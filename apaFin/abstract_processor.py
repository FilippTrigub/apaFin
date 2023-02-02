"""Abstract class defining the 'Processor' interface"""

class Processor:
    """Processor interface. Flathunter runs sequences of exposes through
       a set of processors that stack on each other"""

    def process_expose(self, expose):
        """Mutate the expose. Should be implemented in the subclass"""

    def process_exposes(self, exposes):
        """Apply the processor to every expose in the sequence"""
        return map(self.process_expose, exposes)
