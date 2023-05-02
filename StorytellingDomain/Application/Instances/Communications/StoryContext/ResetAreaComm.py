"""
ResetAreaComm.py

User asks for previously provided information on an area to be removed.

Contains a start range, an end range, and a topic.
"""

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from StorytellingDomain.Application.Instances.Communications.StoryBaseCommunication import StoryBaseComm
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery
from StorytellingDomain.Application.Utils.OptionsGenerator import c_option


class ResetAreaComm(StoryBaseComm):
    tag = ["global"]

    def __init__(self):
        super(ResetAreaComm, self).__init__()
        self.description = "Clear remembered controls."
        self.first_time_intro = "As the wand will write based on the topics applied " \
                                "" \
                                "\nYou can tell the wand that you no longer need these controls." \

    def can_activate(self) -> bool:
        # This can not be used when nothing is generated.
        if self.get_experience_manager().get_state("have_generated_once"):
            return True
        return False

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        exp_manager.frontend.send_information(Req("You can let me start fresh on part of the story."
                                                  "Specify an area and I will reset everything there for you."))

        while True:
            start = exp_manager.frontend.get_information(
                Req("Where (line number) should I start to clean up? ", cast_to=int, info={"options": c_option}))
            end = exp_manager.frontend.get_information(
                Req("Where (line number) should I stop cleaning up? ", cast_to=int, info={"options": c_option}))
            if start <= end:
                break
            else:
                exp_manager.frontend.send_information(
                    Req("Starting line number should be smaller than ending line number."))
        exp_manager.frontend.send_information(Req("OK."))
        exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="reset_area",
                range_start=int(start),
                range_end=int(end),
                content=None,
            )
        )
        topic_weights = exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="topic_weights"
            )
        )
        # exp_manager.frontend.send_information(Req("New topic weights: %s" % topic_weights))
        exp_manager.frontend.send_information(
            Req("Done! You can add things back to continue working."))

        return True
