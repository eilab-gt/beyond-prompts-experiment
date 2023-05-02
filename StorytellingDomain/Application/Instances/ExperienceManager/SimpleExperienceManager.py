"""
SimpleExperienceManager.py

Describe the baseline "simple" experience manager.
"""
import math
import time
from typing import Union

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.CreativeContext.BaseCreativeContext import BaseCreativeContext
from CreativeWand.Framework.ExperienceManager.BaseExperienceManager import BaseExperienceManager
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseFrontend
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from StorytellingDomain.Application.Instances.CreativeContext import StoryCreativeContext
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery
from StorytellingDomain.Application.Instances.Frontend import CommandLineFrontend
from StorytellingDomain.Application.Instances.Frontend.WebFrontend import WebFrontend
from StorytellingDomain.Application.Instances.Frontend.WebFrontendHelper.WebFrontendSessionManager import \
    SessionEndedException
from StorytellingDomain.Application.Utils.APICalls import call_carp_interface
from StorytellingDomain.Application.Utils.OptionsGenerator import yn_option


def is_yes(reply: str) -> bool:
    """
    Check if a string means "yes".
    :param reply: user reply.
    :return: Is it "yes".
    """

    if "y" in reply or "Y" in reply:
        return True
    return False


class SimpleExperienceManager(BaseExperienceManager):
    frontend: BaseFrontend

    def __init__(
            self,
            creative_context: BaseCreativeContext = None,
            frontend: BaseFrontend = None,
            info: dict = None,
    ):
        super(SimpleExperienceManager, self).__init__(creative_context=creative_context, frontend=frontend, info=info)

        self.api_profile = {}  # todo: complete this

        self.default_log_location = "logs/"

        if self.frontend is None:
            # Set default
            self.frontend = CommandLineFrontend()
        """
        Frontend used. In this case just printing and input().
        """

        self.use_carp = False
        if 'use_carp_for_options' in self.info:
            self.use_carp = self.info["use_carp_for_options"]

        self.enable_interrupt = True
        if 'enable_interrupt' in self.info:
            self.enable_interrupt = self.info["enable_interrupt"]

        self.creative_context: StoryCreativeContext

    def let_user_choose(
            self,
            options: dict,
            intro: str = "Choose an option:\n",
            prompt: str = "What's your selection?",
            options_per_page: int = 0,
            current_page: int = 0,
            cast_to: type = None
    ) -> object:
        """
        Show a list of options to the user, and then return the choice the user gives.
        For any option, if it is a dict, it is treated as submenus and the item is used as the new `options` parameter.
        If a key starts with "_" then it will not be displayed.
        This can be used for key `_desc` which is loaded as the description of the item for a submenu item at its parent level,
        Can also be used as commenting out an option.
        :param cast_to: if not None, will attempt to convert result to this type.
        :param intro: Text that appears before all options.
        :param prompt: Text that appears after all options, as a prompt for selecting an option.
        :param options: Options provided, value as actual text displayed.
        :param options_per_page: if >0, page the option list.
        :param current_page: if `options_per_page` is used, describes the current page.
        :return: key of selected option.
        """

        # Generate a list of options to be displayed.
        options_to_show = ""

        options_list = []
        quick_options = []
        key_to_dict = {}
        for key in options:
            if str(key).startswith("_"):
                continue # Internal name used only for showing submenu, skip this
            if type(options[key]) is dict:
                if len([i for i in list(options[key].keys()) if not str(i).startswith("_")]) == 0:
                    continue # All items in the menu item starts with "_". Nothing to show, hiding this menu item
                desc_for_submenu = options[key]["_desc"] if "_desc" in options[key] else "..."
                this_option_text = f"[{key}] {desc_for_submenu}\n"
                key_to_dict[key] = options[key]
            else:
                this_option_text = f"[{key}]{options[key]}\n"
            options_list.append(this_option_text)
            quick_options.append({"label": key, "value": key})

        text_to_display = f"{intro}"

        # pagination calculations. We use 0 for first page.
        total_pages = 1 if options_per_page <= 0 else math.ceil(len(options_list)/options_per_page)
        has_previous_page = current_page > 0
        has_next_page = current_page < total_pages - 1
        start_index = min(current_page * options_per_page,len(options_list))
        last_index = len(options_list) if options_per_page <= 0 \
            else min((current_page+1)*options_per_page,len(options_list))

        if has_previous_page:
            text_to_display = f"{text_to_display}(Click < for previous page)\n"

        for item in options_list[start_index:last_index]:
            text_to_display = f"{text_to_display}{item}"

        if has_next_page:
            text_to_display = f"{text_to_display}(Click > for next page)\n"

        text_to_display = f"{text_to_display}{prompt}"

        quick_options_this_page = []
        if has_previous_page:
            quick_options_this_page.append({"label": "<", "value": "<"})
        for item in quick_options[start_index:last_index]:
            quick_options_this_page.append(item)
        if has_next_page:
            quick_options_this_page.append({"label": ">", "value": ">"})

        #text_to_display = f"{intro}{options_to_show}{prompt}"

        user_choice = self.frontend.get_information(
            Req(text_to_display, info={"options": quick_options_this_page}, cast_to=cast_to))

        if user_choice in key_to_dict:
            user_choice = self.let_user_choose(
                options=key_to_dict[user_choice],
                intro=intro, prompt=prompt, cast_to=cast_to, current_page=0, options_per_page=options_per_page
            )
        elif user_choice == "<":
            user_choice = self.let_user_choose(
                options = options, intro=intro, prompt=prompt, cast_to=cast_to,
                current_page=current_page - 1, options_per_page=options_per_page
            )
        elif user_choice == ">":
            user_choice = self.let_user_choose(
                options = options, intro=intro, prompt=prompt, cast_to=cast_to,
                current_page=current_page + 1, options_per_page=options_per_page
            )

        return user_choice

    def evaluate_free_text_by_carp(self, description_list: list, text: str) -> str | None:
        user_choice = text
        self.frontend.send_information(Req("I can't find an exact match. Let me take in what you just said..."))
        # User choice is not a number, use CARP
        reviews = {user_choice: 0.1}
        call_result = call_carp_interface(
            stories=description_list,
            reviews=reviews,
            connection_profile=None if 'carp' not in self.api_profile else self.api_profile[
                'carp'],
            version=2,
        )

        if len(call_result[user_choice]) == 0:
            self.frontend.send_information(Req("I'm not sure what you want to do - Let's try again."))
            return None
            # force_display_list = True
        else:
            best_item = max(call_result[user_choice], key=call_result[user_choice].get)
            self.frontend.send_information(Req(("Sounds like you want to: %s" % best_item)))
            confirmation = self.frontend.get_information(
                Req("Should I go ahead?", info={"options": yn_option}))
            if not is_yes(confirmation):
                self.frontend.send_information(
                    Req("Maybe I got it wrong."))
                return None
                # raise InterruptedError("Interrupted by rejected CARP inference.")
                # force_display_list = True
            return best_item

    def interrupt_activate(self, comm: BaseCommunication) -> bool:
        return comm.activate()

    def wish_to_interrupt_with_preferred(self) -> Union[None, BaseCommunication]:
        if len(self.comm_group_manager.get_interrupt_communications()) > 0:
            return self.comm_group_manager.get_interrupt_communications()[0]
        else:
            return None

    def activate_preferred(self) -> bool:
        if len(self.comm_group_manager.get_interrupt_communications()) > 0:
            self.comm_group_manager.get_interrupt_communications()[0].activate()
            return True
        else:
            return False

    def get_list_of_available_communications_for_user(self) -> list:
        return self.comm_group_manager.get_available_communications(sort_by="description")

    def start_session(self) -> None:
        # Define constants
        max_turn_count = 12
        turn_count = max_turn_count
        timer_enabled = True

        _str_cw_intro = "Select a way to work with the Wand:\n"
        _str_cw_prompt = "Choose from the options or type in what you wish to do..."

        # Initialize components
        self.frontend.set_state("document", [])
        self.frontend.set_state("sketch", [])
        if type(self.frontend) is WebFrontend:
            self.frontend.sync_react_states()
        self.save_state_checkpoint()

        # Start main agent loop
        while True:
            self.save_logs()
            self.save_state_checkpoint()
            # As we just started a session / finished a communication, now it's time to refresh states and update connecting modules.
            try:
                self.refresh_manager_states()

                # Refresh frontend states and sync info to react
                doc = self.get_state("doc")
                sketches = self.get_state("sketches")
                highlight_coeff = self.get_state("highlight_coeff")
                print("COEFF:%s" % highlight_coeff)
                self.frontend.set_state("document", doc)
                self.frontend.set_state("sketch", sketches)
                self.frontend.set_state("highlight_coeff", highlight_coeff)

                if type(self.frontend) is WebFrontend:
                    self.frontend.sync_react_states()


            except:
                print("Trying to send docs to frontend before round but failed.")

            # If experiment is timed then kill session if time limit got exceeded.
            if timer_enabled:
                self.frontend.send_information(Req("You have %s interactions left. The experiment will end after the counter reaches 0." % turn_count))
                turn_count -= 1
                if turn_count < 0:
                    self.frontend.send_information(
                        Req("Experiment ends here. Thank you for your participation. You will be rediected to end page in 10 seconds."))
                    time.sleep(10)
                    self.frontend.send_kill_to_react()
                    break

            try:
                # If a communication wants to "interrupt activate" here is how it is processed.
                preference = self.wish_to_interrupt_with_preferred()
                if preference is not None and self.enable_interrupt:
                    user_choice = self.frontend.get_information(
                        Req("The creative wand want to help by: %s. Is it OK? (yes/no)" % preference.description))
                    if type(user_choice) is str and is_yes(user_choice):
                        success = self.activate_preferred()
                        if success:
                            continue
                    else:
                        self.suppress_all_interrupts()

                # Generate list of context-aware available communications.
                list_of_comms = self.get_list_of_available_communications_for_user()
                comms_dict = {}
                user_options_dict = {}
                this_key = 1  # Key for the first element
                for item in list_of_comms:
                    this_key_str = str(this_key)
                    comms_dict[this_key_str] = item
                    user_options_dict[this_key_str] = item.description
                    this_key += 1  # Increment key count
                # Append default options
                # user_options_dict["More"] = {
                #     "_desc": "Testing description",
                #     "_Done":"Test Done",
                #     "Done2":"Test Done2"
                # }
                user_options_dict["Done"] = "Say \"We're Done!\" (End the session)"
                description_list = list(user_options_dict.values())

                user_choice = self.let_user_choose(
                    options=user_options_dict,
                    intro=_str_cw_intro,
                    prompt=_str_cw_prompt,
                    options_per_page=6,
                    current_page=0,
                )

                if user_choice not in user_options_dict:
                    if self.use_carp:
                        # Clean up the list for very short prompts.
                        # like "..." as they are used for internal processing.
                        description_list_clean = [i for i in description_list if len(i) > 5]
                        if len(description_list_clean) > 0:
                            should_consume_a_turn = self.evaluate_free_text_by_carp(
                                description_list=description_list_clean,
                                text=str(user_choice),
                            )
                        else:
                            print("No list item can be parsed by CARP. Say we don't know.")
                            should_consume_a_turn = None
                        user_choice = None
                        # Translate descriptions back into key for options.
                        if should_consume_a_turn is not None:
                            for key in user_options_dict:
                                if user_options_dict[key] == should_consume_a_turn:
                                    user_choice = key
                                    break
                    else:
                        self.frontend.send_information(
                            Req("The Wand doesn't know what to do with your input, Let's start over."))
                        user_choice = None

                def assemble_current_states():
                    # Assemble manager log item
                    state_after_operation = self.get_state_dump()
                    state_after_operation["user_choice"] = user_choice
                    state_after_operation["user_choice_comm"] = str(type(comms_dict[user_choice]))
                    state_after_operation["turns_left"] = turn_count
                    state_after_operation["turn_consumed"] = should_consume_a_turn
                    return state_after_operation

                if user_choice in comms_dict:
                    should_consume_a_turn = self.interrupt_activate(comms_dict[user_choice])
                    if not should_consume_a_turn: # Comm failed, refund turns
                        turn_count += 1
                    else:
                        self.frontend.save_logs_manually("turn_ended",request=[max_turn_count-turn_count])
                    self.add_log_item(assemble_current_states())
                elif user_choice == "Done":
                    self.frontend.send_information(Req("Thank you for using! You have %s turn(s)." % turn_count))
                    self.frontend.send_kill_to_react()
                    self.add_log_item("Done")
                    break
                else:
                    turn_count += 1 # Refund turns
                    self.frontend.send_information(
                        Req("The Wand doesn't know what to do with your input, Let's start over."))


            except Exception as e:
                print("Exception: %s" % e)
                print("Type: %s" % type(e))
                if type(e) is SessionEndedException:
                    self.end_session()
                    return
                elif type(e) is InterruptedError:
                    turn_count += 1
                    self.frontend.send_information(
                        Req("Let's start over."))
                else:
                    turn_count += 1
                    self.frontend.send_information(
                        Req("Sorry that something went wrong. Would you mind trying again?"))

        # If we are somehow out of the main loop due to early stopping, end the session.
        self.end_session()

    def refresh_manager_states(self):
        """
        When called, this function updates itself with needed information from the Creative Context.
        :return: None
        """
        doc = self.creative_context.document
        sketches = self.creative_context.execute_query(
            StoryContextQuery(
                q_type="get_all_sketches"
            )
        )
        self.set_state("doc", doc)
        self.set_state("sketches", sketches)

    def end_session(self):
        self.session_ended = True
        self.save_logs()
