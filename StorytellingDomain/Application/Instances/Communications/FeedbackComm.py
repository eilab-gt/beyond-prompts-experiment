"""
FeedbackComm.py

A base class for communications capturing experiment data.
"""

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req


class FeedbackComm(BaseCommunication):
    """
    Get free text response on specific questions.
    """

    tag = ["general"]

    def __init__(self, description, question_to_ask="", options: list = None):
        super(FeedbackComm, self).__init__(description=description)
        self.question_to_ask = question_to_ask
        self.options = options
        if "[cancel]" not in self.options:
            self.options.append("[cancel]")

        self.parsed_options = []
        for item in self.options:
            self.parsed_options.append({"label":item,"value":item})

    def can_activate(self) -> bool:
        return True

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        question = "The creative wand is wondering: %s" % self.question_to_ask
        if self.options is None: # Free text
            result = exp_manager.frontend.get_information(
                Req(question))
        else:
            result = exp_manager.frontend.get_information(
                Req(question, info={"options": self.parsed_options}))

        exp_manager.frontend.send_information(Req("You answered\"%s\". Thank you!" % result))
        return False # To signify that nothing in-the-loop successfully happened