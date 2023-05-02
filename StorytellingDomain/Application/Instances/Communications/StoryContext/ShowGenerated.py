"""
ShowGenerated.py

The agent provides generated sentences to the user.
"""
from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery
from StorytellingDomain.Application.Utils.OptionsGenerator import ync_option


class ShowGeneratedComm(BaseCommunication):
    """
    Show generated sentences.
    """
    tag = ["general"]

    def __init__(self):
        super(ShowGeneratedComm, self).__init__()
        self.description = "[NOT USING ANYMORE: IF YOU SEE THIS SEND A MESSAGE TO ME]Show/Update generated sentences."

    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        document_filled = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_document_filled"))
        return document_filled

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()

        should_regenerate = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_should_regenerate"))
        if not should_regenerate:
            result = exp_manager.frontend.get_information(
                Req("You haven't made any changes. Do you want me to just try regenerating again?",
                    info={"options": ync_option}))
            if result.lower() == "yes":
                exp_manager.creative_context.execute_query(
                    StoryContextQuery(q_type="reset_should_regenerate"))

        exp_manager.frontend.send_information(Req("Loading... (Will take up to half a minute)"))

        done = False
        while not done:
            result = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generate_step_by_step"))
            done = result["done"]
            if done:
                break
            sentence = result["sentence"]
            idx = result["index"]
            exp_manager.frontend.send_information(Req(f"Working on #{idx}: {sentence}"))
        # generated_cache = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generated_contents"))
        exp_manager.frontend.send_information(Req("Done! Check the new story."))
        # exp_manager.frontend.send_information(Req("Here's the generated story:"))
        # for item in generated_cache:
        #     exp_manager.frontend.send_information(Req("%s" % item))
        return True
