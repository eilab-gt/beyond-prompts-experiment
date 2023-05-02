"""
CARPFindLineByCriticComm.py

Communication using CARP.

Request a critic, find the line that best suits it.

"""
import random

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from StorytellingDomain.Application.Instances.Communications.StoryBaseCommunication import StoryBaseComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.CARP.CARPCriticList import get_default_critics
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery
from StorytellingDomain.Application.Utils.OptionsGenerator import c_option

info_sentence = """
Let's reflect on what is going wrong!
I can reflect on the story on some common critics such as "The story is too dark", "It should not be raining".
"""

info_sentence_for_default_critic = """
One second, thinking...
"""

info_sentence_for_out_of_topic = """
Let's reflect on what you just added in!
I can reflect on whether this sentence is out of topic, to help you keep the story connected.
"""


class CARPFindLineByCriticComm(StoryBaseComm):
    """
    Request a critic, find the line that best suits it.
    This uses CARP to give a score for each (sentence, critic) pair for further processing.
    """

    tag = ["human", "reflection", "global"]

    def __init__(self, do_highlight=True):
        """

        :param do_highlight: Enable highlighting functionality.
        """
        super(CARPFindLineByCriticComm, self).__init__()
        self.description = "Reflect together."
        self.do_highlight = do_highlight
        self.first_time_intro = "If you have a comment on the story, the Wand will help you find out" \
                                " which part of the story this comment is pointing to." \
                                "\nThe Wand will highlight these parts hinting further improvements."

    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        document_filled = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_document_filled"))
        return document_filled

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        exp_manager.frontend.send_information(Req(info_sentence))
        critic = exp_manager.frontend.get_information(
            Req("In one sentence, What's going wrong?", info={"options": c_option}))
        critic = str(critic)
        if len(critic) > 0:
            if not self.do_highlight:
                carp_result = exp_manager.creative_context.execute_query(
                    StoryContextQuery(q_type="carp", content=critic)
                )
                exp_manager.frontend.send_information(
                    Req("Seems like this line is going wrong: %s" % carp_result[critic]))
            else:
                lines_highlighted = self.carp_highlight_helper(critic)
                if lines_highlighted > 0:
                    exp_manager.frontend.send_information(
                        Req("We've highlighted places where we think things are going wrong."))
                else:
                    exp_manager.frontend.send_information(
                        Req("Looks like everything is good to me - I didn't highlight anything."))
        else:
            exp_manager.frontend.send_information(Req("Never mind."))

    def carp_highlight_helper(self, critic, mask=None, dry_run=False) -> int:
        """
        Use critic to request highlight coefficient from CARP.
        :param critic: one sentence critic used.
        :param mask: if not None, only elements evaluated to True will have their score of corresponding sentence presented to user.
        :param dry_run: only count how many lines are highlighted, do not actually highlight them.
        :return: How many lines are highlighted. (side effect: lines are highlighted)
        """
        exp_manager = self.get_experience_manager()
        carp_result = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="carp_highlight", content=[critic])
        )
        carp_inner = carp_result[critic]
        document = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_document"))
        document = list(document)
        highlight_scores = [0] * len(document)
        highlighted_count = 0
        for idx in range(len(document)):
            if document[idx] in carp_inner:
                # 0.15 => 0, 0.4 => 1
                if mask is None or (mask is not None and mask[idx]):
                    score = max(0, min(carp_inner[document[idx]] * 4 - 0.6, 1))
                    if not dry_run:
                        highlight_scores[idx] = score
                    if score > 0:
                        highlighted_count += 1
                    # highlight_scores[idx] = min(carp_inner[document[idx]] * 4 - 0.6, 1)
        exp_manager.set_state("highlight_coeff", highlight_scores)
        return highlighted_count

class CARPFindLineByDefaultCriticComm(CARPFindLineByCriticComm):
    """
    This communication applies a set of preset critic, instead of allowing the user to input one.
    """

    tag = ["agent", "reflection", "local"]
    #tag = ["agent", "reflection", "local", "global"]

    def __init__(self):
        super(CARPFindLineByCriticComm).__init__()
        self.description = "Get a story quality tip."
        self.do_highlight = True  # This one only supports highlight mode

        self.first_time_intro = "The wand will proofread the story with its own criteria and highlight" \
                                " places that may need work." \
                                "\nAs the Wand will use one out of many possible criteria, you will get different results every time."

        self.default_critic_list = get_default_critics()

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        exp_manager.frontend.send_information(Req(info_sentence_for_default_critic))

        critic = random.choice(self.default_critic_list)
        exp_manager.frontend.send_information(
            Req("Let me look into if: %s" % critic))

        result = self.carp_highlight_helper(critic)

        if result > 0:
            exp_manager.frontend.send_information(
                Req("I've highlighted place where I think: %s" % critic))
        else:
            exp_manager.frontend.send_information(
                Req("Looks like nothing is related to \"%s\"." % critic))

        return True

class CARPFindByDefaultCriticComm(CARPFindLineByDefaultCriticComm):
    """
    This communication applies a set of preset critic, instead of allowing the user to input one.
    """

    tag = ["agent", "reflection", "global"]

    def __init__(self):
        super(CARPFindLineByCriticComm).__init__()
        self.description = "Get a high-level story quality tip."
        self.do_highlight = True  # This one only supports highlight mode

        self.first_time_intro = "The wand will proofread the story with its own criteria and let you know whether" \
                                " there are places that may need work." \
                                "\nAs the Wand will use one out of many possible criteria, you will get different results every time."

        self.default_critic_list = get_default_critics()

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        exp_manager.frontend.send_information(Req(info_sentence_for_default_critic))

        critic = random.choice(self.default_critic_list)
        exp_manager.frontend.send_information(
            Req("Let me look into if: %s" % critic))

        result = self.carp_highlight_helper(critic, dry_run=True)

        if result > 0:
            exp_manager.frontend.send_information(
                Req("I found place where I think: %s" % critic))
        else:
            exp_manager.frontend.send_information(
                Req("Looks like nothing is related to \"%s\"." % critic))

        return True


class CARPOutOfTopicDetectionComm(CARPFindLineByCriticComm):
    """
    This communication looks into whether a given sentence relates to a given topic.
    """

    tag = ["human", "reflection", "local"]
    def __init__(self):
        super(CARPFindLineByCriticComm).__init__()
        self.description = "Check off-topicness of a sentence."
        self.do_highlight = True  # This one only supports highlight mode

        self.first_time_intro = "The Wand will check whether a sentence is on a specific topic."

        self.critic_template = "This part of the story should be related to %s."

    def confidence_to_interrupt_activate(self) -> float:
        if self.get_experience_manager().consume_event("just_forced_sentence", peek=True):
            return 1
        else:
            return 0

    def _determine_sentence_idx(self) -> int:
        """
        Determine which sentence to be used.
        """
        exp_manager = self.get_experience_manager()
        sent_idx = exp_manager.frontend.get_information(
            Req("Which sentence?", cast_to=int, info={"options": c_option}))
        exp_manager.frontend.send_information(Req("Looking into sentence %s." % sent_idx))
        return sent_idx

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        exp_manager.frontend.send_information(Req(info_sentence_for_out_of_topic))

        topic = exp_manager.frontend.get_information(
            Req("Which topic?", info={"options": c_option}))

        sent_idx = self._determine_sentence_idx()

        # if exp_manager.consume_event("just_forced_sentence"):
        #     exp_manager.frontend.send_information(Req("Looking into what you just added."))
        #     sent_idx = exp_manager.get_state("last_modified_index")
        # else:


        document = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_document"))
        mask = [False] * len(document)
        if sent_idx >= 0:
            mask[sent_idx] = True

        critic = self.critic_template % topic
        exp_manager.frontend.send_information(
            Req("Let me look into if: %s" % critic))

        result = self.carp_highlight_helper(critic, mask=mask)
        if result > 0:
            exp_manager.frontend.send_information(
                Req("The sentence is highlighted to the extent where I think: %s" % critic))
        else:
            exp_manager.frontend.send_information(
                Req("I think this sentence seems out-of-topic, based on my thought in: %s" % critic))
        return True


class CARPOOTDOnLastSentence(CARPOutOfTopicDetectionComm):
    """
    Let CARP check the last sentence the user just added on whether it's out of topic.
    """
    tag = ["agent", "reflection", "local"]
    def __init__(self):
        super(CARPFindLineByCriticComm).__init__()
        self.description = "By giving a topic, let the Wand check whether the sentence you just put in is out of that topic."
    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        return exp_manager.consume_event("just_forced_sentence")

    def _determine_sentence_idx(self) -> int:
        exp_manager = self.get_experience_manager()
        return exp_manager.get_state("last_modified_index")

