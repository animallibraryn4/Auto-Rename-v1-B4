# Create a state_manager.py
class UserState:
    def __init__(self):
        self.info_mode = {}
        self.sequence_mode = {}
        self.verification = {}
        self.queues = {}
    
    async def get_user_state(self, user_id):
        """Return current user operation mode"""
        if user_id in self.info_mode:
            return "info"
        elif user_id in self.sequence_mode:
            return "sequence"
        else:
            return "auto_rename"
