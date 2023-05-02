"""
UserWork.py

This communication allows the user to select one sentence
and replace it with one desired by them.

"""
from StorytellingDomain.Application.Instances.Communications.StoryBaseCommunication import StoryBaseComm
from StorytellingDomain.Application.Utils.OptionsGenerator import c_option
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery


class UserWorkComm(StoryBaseComm):
    tag = ["human", "elaboration", "local"]

    def __init__(self):
        super(UserWorkComm, self).__init__()
        self.description = "Replace a sentence."
        self.first_time_intro="You can write a sentence by yourself. " \
                              "Specify a sentence to substitute and type in the sentence" \
                              ", and the sentence will be in the story." \
                              "\nDo note that if you choose to let the Wand rewrite the whole story," \
                              " your line will be overwritten."

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

        existing_work = exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="get_document"
            )
        )
        # if len(existing_work) > 0:
        #     exp_manager.frontend.send_information(Req("Your work so far: "))
        #     for index, line in enumerate(existing_work):
        #         exp_manager.frontend.send_information(Req("[%d] %s" % (index, line)))
        # else:
        #     exp_manager.frontend.send_information(Req("Your work so far: None"))

        to_replace = exp_manager.frontend.get_information(Req("Which sentence number do you want to replace? "))
        index = int(to_replace)
        new_sentence = exp_manager.frontend.get_information(
            Req(f"Write the substitute sentence for sentence {index} : ", info={"options": c_option}))

        exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="force_one",
                content={"index": index, "sentence": new_sentence}
            )
        )

        exp_manager.trigger_event("just_forced_sentence")
        exp_manager.set_state("last_modified_index", index)
