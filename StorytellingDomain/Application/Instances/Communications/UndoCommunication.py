"""
UndoCommunication.py

Communication that returns the state of the session to the last checkpoint.
"""
from StorytellingDomain.Application.Utils.OptionsGenerator import ync_option, yn_option, is_yes
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req


class UndoComm(BaseCommunication):
    tag = ["general"]

    def __init__(self):
        super(UndoComm, self).__init__()
        self.description = "Undo."

    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        return exp_manager.can_undo_state()

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = exp_manager.frontend.get_information(
            Req("Should I revert the last change?", info={"options": yn_option}))
        if is_yes(result):
            exp_manager.undo_state()
            exp_manager.frontend.send_information(
                Req("Done!"))
            return True
        else:
            exp_manager.frontend.send_information(
                Req("Sure."))
            return False
