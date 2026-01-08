from helper.database import N4BOTS
from plugins.sequence import user_sequences, user_mode, user_seq_mode

async def get_user_operation_mode(user_id):
    """
    Determine what operation mode the user is in
    Returns: "auto_rename", "sequence", or "info"
    """
    from plugins.auto_rename import info_mode_users
    
    if user_id in info_mode_users:
        return "info"
    elif user_id in user_sequences:
        return "sequence"
    else:
        return "auto_rename"

async def switch_to_sequence_mode(user_id):
    """Helper to switch user to sequence mode"""
    user_sequences[user_id] = []
    return True

async def exit_sequence_mode(user_id):
    """Helper to exit sequence mode"""
    from plugins.sequence import cleanup_user_data
    await cleanup_user_data(user_id)
    return True
