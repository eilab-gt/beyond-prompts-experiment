"""
SuggestSentence.py

Communication that chooses a sentence from the document and suggests a sentence to follow it.
"""

import random

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from StorytellingDomain.Application.Instances.Communications.StoryBaseCommunication import StoryBaseComm
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery
from StorytellingDomain.Application.Utils.OptionsGenerator import ync_option


def is_yes(reply: str) -> bool:
    """
    Check if a string means "yes".
    :param reply: user reply.
    :return: Is it "yes".
    """

    if "y" in reply or "Y" in reply:
        return True
    return False


class SuggestSentenceComm(StoryBaseComm):
    tag = ["agent", "elaboration", "local"]

    def __init__(self):
        super(SuggestSentenceComm, self).__init__()
        self.description = "Get a sentence suggestion."
        self.topics = ["science", "sports"]
        self.first_time_intro="By doing this you will initiate the Wand to inspire you by give a one-point suggestion." \
                              "\nIf you are good with that sentence you can select to put it into the story as suggested."

    def can_activate(self) -> bool:
        # can activate if there is at least one sentence in the document
        # exp_manager = self.get_experience_manager()
        # doc = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="get_document"))
        # for line in doc:
        #     if len(line)>0:
        #         return True
        # return False

        # text = ""
        # for line in doc:
        #     text += line + " "
        # return len(text) > len(doc)

        # This can not be used when nothing is generated.
        if self.get_experience_manager().get_state("have_generated_once"):
            return True
        return False

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False

        doc = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="get_document"))
        # topics = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="topic_weights"))

        # choose a random sentence and topic from predefined list
        indices = range(len(doc))
        indices = filter(lambda i: len(doc[i]) > 0, indices)
        i = random.choice(list(indices))
        sentence = doc[i]
        topic = random.choice(self.topics)

        # generate a new sentence with chosen sentence as prompt
        exp_manager.frontend.send_information(Req("Loading..."))
        res = exp_manager.creative_context.execute_query(StoryContextQuery(
            q_type="generate_one",
            content={"prompt": sentence, "topics": {topic: 1.0}}
        )
        )

        # display
        exp_manager.frontend.send_information(
            Req("What if after sentence [%d] '%s', we had something like this about '%s': '%s'?" % (
                i, sentence, topic, res)))
        result = exp_manager.frontend.get_information(
            Req("Should I include this sentence?", info={"options": ync_option}))
        if is_yes(str(result)):
            res = exp_manager.creative_context.execute_query(
                StoryContextQuery(
                    q_type="force_one",
                    content={"sentence": res, "index": i},
                )
            )
            exp_manager.frontend.send_information(
                Req("Done! You can go ahead to freeze the sentence to keep it from getting overwritten."))
        else:
            exp_manager.frontend.send_information(Req("Never mind."))

        return True
