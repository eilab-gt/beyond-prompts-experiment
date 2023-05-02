"""
RequestGeneration.py

Initiate the generation process.
"""
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from StorytellingDomain.Application.Instances.Communications.StoryBaseCommunication import StoryBaseComm
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery
from StorytellingDomain.Application.Utils.OptionsGenerator import ync_option, generate_option_list


class GenerateComm(StoryBaseComm):
    """
    (re)Generate using information gathered.
    """

    tag = ["general"]

    def __init__(self, allow_no_sketch=False):
        description = "Generate whole story."

        super(GenerateComm, self).__init__(description=description)
        self.allow_no_sketch = allow_no_sketch

        self.first_time_intro = "The Wand will write the story, or write an alternative if the story is already generated," \
                                "based on the control applied." \
                                "\nUse this when starting fresh or if you wish to see an alternative generated."

    def can_activate(self) -> bool:
        # Always enable generation when no_sketch mode is up.
        if self.allow_no_sketch: return True
        return self.get_experience_manager().creative_context.is_generation_ready()

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()

        result = self.do_first_time_introduction()
        if not result:
            return False
        should_regenerate = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_should_regenerate"))
        if not should_regenerate:
            result = exp_manager.frontend.get_information(
                Req("You haven't made any changes. Do you want me to rewrite what I just wrote?",
                    info={"options": ync_option}))
            if result.lower() == "yes":
                exp_manager.creative_context.execute_query(
                    StoryContextQuery(q_type="reset_should_regenerate"))
            else:
                exp_manager.frontend.send_information(Req("Got it."))
                return False

        exp_manager.frontend.send_information(Req("OK, I'm generating parts that are not frozen by you..."))
        exp_manager.frontend.send_information(Req("Loading... (May take up to half a minute)"))
        # generated_cache = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generated_contents"))

        self.call_gen_step_by_step(exp_manager)

        exp_manager.frontend.send_information(Req("Done!"))

        exp_manager.set_state("have_generated_once", True)
        return True

    def call_gen_step_by_step(self, exp_manager):
        done = False
        while not done:
            result = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generate_step_by_step"))
            done = result["done"]
            if done:
                break
            sentence = result["sentence"]
            idx = result["index"]
            if sentence is not None:
                exp_manager.frontend.send_information(Req(f"Working on #{idx}: {sentence}"))


class GenerateCommV2(StoryBaseComm):
    """
    A modified version of GenerateComm allowing both generating in full or parts.
    """
    tag = ["general"]

    def __init__(self, allow_no_sketch=False):
        description = "Let the Wand write."

        super(GenerateCommV2, self).__init__(description=description)

        self.first_time_intro = "The wand can write a story for you based on applied controls." \
                                "\nYou can either get the whole story rewritten or only generating from a certain point," \
                                "leave the previous sentences untouched." \
                                "\nYou can use this multiple times for alternatives, and if you prefer the previous one, use the Undo function."

    def can_activate(self) -> bool:
        return True

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()

        result = self.do_first_time_introduction()
        if not result:
            return False

        mode = "whole"  # default mode, if document does not exist yet.

        document_filled = exp_manager.creative_context.execute_query(
            StoryContextQuery(q_type="get_document_filled"))

        exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="set_freeze_after",
                range_start=-1,
            )
        )

        if document_filled:
            options = {"Rewrite every sentence.": "whole", "Only rewrite story after a certain sentence.": "part"}
            options = generate_option_list(major_options=options, add_cancel=True)

            result = exp_manager.frontend.get_information(
                Req("I can rewrite the whole story or only after a certain sentence. Please choose an option:",
                    info={"options": options}))

            if result not in ["whole", "part"]:
                exp_manager.frontend.send_information(Req("Not sure what you want to do. Let's start over."))
                return False

            mode = result
        else:
            exp_manager.frontend.send_information(Req("As we do not have a story written, let's create one first!"))

        if mode == "whole":
            exp_manager.frontend.send_information(Req("OK, I'm generating parts that are not frozen by you..."))
            exp_manager.frontend.send_information(Req("Loading... (May take up to half a minute)"))
            # generated_cache = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generated_contents"))

            self.call_gen_step_by_step(exp_manager)

            exp_manager.frontend.send_information(Req("Done!"))

            exp_manager.set_state("have_generated_once", True)
            return True
        elif mode == "part":
            hint = "You can freeze a sentence and every one before it and only regenerate the ones after it.\n Which sentence position? (-1 to disable and regenerate everything:)"
            start = exp_manager.frontend.get_information(Req(hint))
            exp_manager.frontend.send_information(Req("OK. Loading..."))
            exp_manager.creative_context.execute_query(
                StoryContextQuery(
                    q_type="set_freeze_after",
                    range_start=int(start),
                )
            )
            # generated_cache = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generated_contents"))
            self.call_gen_step_by_step(exp_manager)
            return True

    def call_gen_step_by_step(self, exp_manager):
        done = False
        while not done:
            result = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generate_step_by_step"))
            done = result["done"]
            if done:
                break
            sentence = result["sentence"]
            idx = result["index"]
            if sentence is not None:
                exp_manager.frontend.send_information(Req(f"Working on #{idx}: {sentence}"))


class GenerateWithFreezeComm(GenerateComm):
    """
    (re)Generate using information gathered, with frozen mask set.
    """

    tag = ["general"]

    def __init__(self, allow_no_sketch=False):
        super(GenerateWithFreezeComm, self).__init__(allow_no_sketch=allow_no_sketch)
        self.description = "Regenerate part of story."
        self.first_time_intro = "The Wand will (re)write the story only after a given point, based on the control " \
                                "applied." \
                                "\nUse this when you are good with part of the story but want an alternative development."

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        result = self.do_first_time_introduction()
        if not result:
            return False
        exp_manager.set_state("just_forced_sentence", False)
        hint = "You can freeze a sentence and every one before it and only regenerate the ones after it.\n Which sentence position? (-1 to disable and regenerate everything:)"
        start = exp_manager.frontend.get_information(Req(hint))
        exp_manager.frontend.send_information(Req("OK. Loading..."))
        exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="set_freeze_after",
                range_start=int(start),
            )
        )
        # generated_cache = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="generated_contents"))
        self.call_gen_step_by_step(exp_manager)
        return True

    def can_activate(self) -> bool:
        # This can not be used when nothing is generated.
        if self.get_experience_manager().get_state("have_generated_once"):
            return True
        return False

    def confidence_to_interrupt_activate(self) -> float:
        # confidence = 1.0 if self.get_experience_manager().get_state("just_forced_sentence") else 0.0
        # print("Confidence interrupt: %s" % confidence)
        # return confidence
        return 0

    def suppress_interrupt(self):
        # self.get_experience_manager().set_state("just_forced_sentence", False)
        pass
