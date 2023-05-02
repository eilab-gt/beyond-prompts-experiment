"""
Echo.py

A simple sample communication.
Repeats what the user says.
"""
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req


class EchoComm(BaseCommunication):
    def __init__(self):
        super(EchoComm, self).__init__()
        self.description = "Let Creative Wand repeat what you tell them."

    def can_activate(self) -> bool:
        return True

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = exp_manager.frontend.get_information(Req("Say something:"))
        exp_manager.frontend.send_information(Req("You said: %s" % result))
