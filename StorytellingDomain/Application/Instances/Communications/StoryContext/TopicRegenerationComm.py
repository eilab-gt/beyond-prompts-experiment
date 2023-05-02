"""
TopicRegeneration.py

Communication that gives a topic to the user and asks for a range of sentences to change the topics.
"""

import random

from StorytellingDomain.Application.Instances.Communications.StoryBaseCommunication import StoryBaseComm
from StorytellingDomain.Application.Utils.OptionsGenerator import ync_option, c_option
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery


def is_yes(reply: str) -> bool:
    """
    Check if a string means "yes".
    :param reply: user reply.
    :return: Is it "yes".
    """

    if "y" in reply or "Y" in reply:
        return True
    return False


class TopicRegenerationComm(StoryBaseComm):
    tag = ["agent", "elaboration", "global"]

    def __init__(self):
        super(TopicRegenerationComm, self).__init__()
        self.description = "Get a topic suggestion."
        self.first_time_intro = "By doing this, you will initiate the Wand to provide a topic suggestion." \
                                "\nOnce you are good with the topic you can then apply it to the story," \
                                " so that if you ask the Wand to write the story it will write towards that topic."

    def can_activate(self) -> bool:
        return True
        # # can activate if there is an existing sketch with at least two topics
        # exp_manager = self.get_experience_manager()
        # topics = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="topic_weights"))
        # return len(topics) >= 2

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        # topics = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="topic_weights"))
        topics = {"Business": 1, "Sports": 1}
        # choose a random topic (TODO: eventually, do something smarter that can suggest entirely new topics)
        topic, weights = random.choice(list(topics.items()))
        exp_manager.frontend.send_information(Req("Let's use the topic '%s' somewhere." % topic))

        # ask for a start and end sentence
        start = exp_manager.frontend.get_information(
            Req("Where (line number) should I phase this topic in? ", cast_to=int, info={"options": c_option}))
        end = exp_manager.frontend.get_information(
            Req("Where (line number) should I phase this topic out? ", cast_to=int, info={"options": c_option}))

        result = exp_manager.frontend.get_information(
            Req("%s from %s to %s. Should I work on that?" % (topic, start, end), info={"options": ync_option}))
        if is_yes(str(result)):

            # update the sketch
            exp_manager.creative_context.execute_query(
                StoryContextQuery(
                    q_type="sketch",
                    range_start=int(start),
                    range_end=int(end),
                    content=topic,
                )
            )
            topic_weights = exp_manager.creative_context.execute_query(
                StoryContextQuery(
                    q_type="topic_weights"
                )
            )
            exp_manager.frontend.send_information(Req("Done!"))
        else:
            exp_manager.frontend.send_information(Req("Never mind."))
        # exp_manager.frontend.send_information(Req("New topic weights: %s" % topic_weights))
        return True
