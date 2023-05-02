"""
UserProvideSketch.py

User provides a sketch so as to influence the geneerated stories.

Sketches contain a start range, an end range, and a topic.
"""
from StorytellingDomain.Application.Utils.OptionsGenerator import c_option, generate_option_list
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery


class UserSketchComm(BaseCommunication):
    """
    The communication that asks user information on a sketch, and then apply it to the Story creative context.
    """

    tag = ["human", "elaboration", "global"]

    def __init__(self):
        super(UserSketchComm, self).__init__()
        self.description = "Apply topic control."

    def can_activate(self) -> bool:
        return True

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        exp_manager.frontend.send_information(Req("You can let me introduce a specific topic to part of the story."
                                                  "\n If we put multiple topics in, I will try writing a line with regard to all topics.\n"
                                                  "Just let me know the topic and where to apply."))
        topic_message = "Which topic should I introduce? Try one from %s or type in yours:" % exp_manager.creative_context.suggested_topics
        topic_options = {}
        for item in exp_manager.creative_context.suggested_topics:
            topic_options[item] = item
        topic = exp_manager.frontend.get_information(
            Req(topic_message, info={"options": generate_option_list(topic_options)}))

        # Bugfix: make topic lower cased so generator recognizes it
        if type(topic) is str:
            topic = topic.lower().capitalize()

        while True:
            start = exp_manager.frontend.get_information(
                Req("Where (line number) should I phase this topic in? ", cast_to=int, info={"options": c_option}))
            end = exp_manager.frontend.get_information(
                Req("Where (line number) should I phase this topic out? ", cast_to=int, info={"options": c_option}))
            if start <= end:
                break
            else:
                exp_manager.frontend.send_information(
                    Req("Starting line number should be smaller than ending line number."))
        exp_manager.frontend.send_information(Req("OK."))
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
        # exp_manager.frontend.send_information(Req("New topic weights: %s" % topic_weights))
        exp_manager.frontend.send_information(
            Req("You've added a sketch for topic %s! You can add more, or see updated stories by asking me to show "
                "the stories again!" % topic))

        return True
