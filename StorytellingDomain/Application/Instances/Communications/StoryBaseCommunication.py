"""
StoryBaseCommunication.py
Contains universal helper functions used in the story domain.
If this class is used in the place of BaseCommunication, these methods will become available.
"""
from abc import ABC

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from StorytellingDomain.Application.Utils.OptionsGenerator import is_yes, yn_option


class StoryBaseComm(BaseCommunication, ABC):
    def __init__(self, description="", info: dict = None):

        super(StoryBaseComm, self).__init__(description=description,info=info)

        if info is not None and 'first_time_intro' in info:
            self.first_time_intro = info['first_time_intro']
        else:
            self.first_time_intro = None

    def do_first_time_introduction(self, message: str = None) -> bool:
        """
        Display an introduction message, only once, when this function is called.
        If no message is supplied
        :param message: If not None, Message to display as introduction.
        """
        exp_manager = self.get_experience_manager()

        if message is None:
            if self.first_time_intro is None:
                self.first_time_intro = "Intro message missing - Report this, thanks."
                #raise ValueError("No message specified both in the function call and the class variable.")
            message = self.first_time_intro

        state_string = f"flag_first_time_[{self.description}]"

        if exp_manager.get_state(state_string) is None:
            exp_manager.set_state(state_string, True)
            exp_manager.frontend.send_information(
                Req("As you are using this entry for the first time, let me explain."))
            exp_manager.frontend.send_information(Req(message))
            result = exp_manager.frontend.get_information(
                Req("Should I go ahead?",
                    info={"options": yn_option}))
            if not is_yes(result):
                exp_manager.frontend.send_information(Req("Got it."))
                return False
            else:
                return True
        else:
            # Always treat this as a go ahead.
            return True
