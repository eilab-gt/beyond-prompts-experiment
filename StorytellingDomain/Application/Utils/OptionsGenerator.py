"""
OptionsGenerator.py

Hosts utility functions that makes creating option lists easier.
"""


def generate_option_list(major_options=None,
                         add_yn: bool = False,
                         add_cancel: bool = False):
    """
    Generate an option list confined to what the WebFrontend needs.
    WebFrontend expects a list of dict in format "label":<what is shown on frontend>,"value":<what is returned as user input>.
    :param major_options: every key will be treated as a label (what the frontend displays)
     while every value will be treated as the internal value returned if such option is selected.
    :param add_yn: add yes/no confirmation.
    :param add_cancel: add cancel button.
    :return: a list of dicts forming `options` that can be used by `send/get_information`.
    """
    if major_options is None:
        major_options = {}
    result = []
    for key in major_options:
        result.append({"label": key, "value": major_options[key]})
    if add_yn:
        result.append({"label": "Yes", "value": "yes"})
        result.append({"label": "No", "value": "no"})
    if add_cancel:
        result.append({"label": "Cancel", "value": "[cancel]"})
    return result

def is_yes(reply: object) -> bool:
    """
    Check if a string means "yes".
    :param reply: user reply.
    :return: Is it "yes".
    """
    reply = str(reply)
    if "y" in reply or "Y" in reply:
        return True
    return False

yn_option = generate_option_list(add_yn=True)
ync_option = generate_option_list(add_yn=True, add_cancel=True)
c_option = generate_option_list(add_cancel=True)
