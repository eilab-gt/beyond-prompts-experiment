"""
OpeningMessage.py

Communication that sends kick-off messages.

This message only display once at the beginning of the session.
"""
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req
from CreativeWand.Utils.Misc.Tag import tag

opening_message = "I'm your Creative Wand, here to work together on writing a story with you." \
                  "\n\nYou will see a list of actions available to you." \
                  "\n\nTell me what you wish to do by typing in the word in the bracket." \
                  "\n\nOnce you selected an action, I will further guide you through each of it." \
                  "\n\nEnjoy the collaborative experience!" \
                  "" \
                  ""


class OpeningMessageComm(BaseCommunication):
    tag = ["general"]

    def __init__(self, message=None, do_interrupt=True):
        """
        Initialize this instance.
        If do_interrupt is set to True, then this comm will attempt to
        interrupt (provide introduction) once.

        :param message: Message displayed.
        :param do_interrupt: Enable the interruption behaviour.
        """
        super(OpeningMessageComm, self).__init__()
        self.description = "Let the Wand introduce themself."
        self.opening_message = message

        if self.opening_message is None:
            self.opening_message = opening_message

        # Suppress interrupt by default if do_interrupt is False
        self.interrupt_suppressed = not do_interrupt

    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        if exp_manager.get_state("did_opening") is None:
            return True
        return False

    def confidence_to_interrupt_activate(self) -> float:
        return 1.0 if not self.interrupt_suppressed else 0.0

    def suppress_interrupt(self):
        self.interrupt_suppressed = True

    def activate(self) -> bool:
        self.interrupt_suppressed = True
        exp_manager = self.get_experience_manager()
        exp_manager.frontend.send_information(Req(opening_message))
        exp_manager.set_state("did_opening", "yes")
