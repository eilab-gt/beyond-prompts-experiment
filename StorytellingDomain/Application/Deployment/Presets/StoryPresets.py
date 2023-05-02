"""
StoryPresets.py

A reference implementation of preset objects (communications, creative context, etc.) for story domain.

TODO: consider migrating this as a common component of the main Creative Wand framework.

"""
from os import path

from StorytellingDomain.Application.Instances.Communications.Echo import EchoComm
from StorytellingDomain.Application.Instances.Communications.FeedbackComm import FeedbackComm
from StorytellingDomain.Application.Instances.Communications.OpeningMessage import OpeningMessageComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.CARP.CARPFindLineByCriticComm import \
    CARPFindLineByCriticComm, CARPOutOfTopicDetectionComm, CARPFindLineByDefaultCriticComm, CARPOOTDOnLastSentence, \
    CARPFindByDefaultCriticComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.InspirationComm import InspirationComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.RequestGeneration import GenerateComm, \
    GenerateWithFreezeComm, GenerateCommV2
from StorytellingDomain.Application.Instances.Communications.StoryContext.ResetAreaComm import ResetAreaComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.ShowGenerated import ShowGeneratedComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.SuggestSentenceComm import SuggestSentenceComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.TopicRegenerationComm import \
    TopicRegenerationComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.UserProvideSketch import UserSketchComm
from StorytellingDomain.Application.Instances.Communications.StoryContext.UserWorkComm import UserWorkComm
from StorytellingDomain.Application.Instances.Communications.UndoCommunication import UndoComm
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryCreativeContext
from StorytellingDomain.Application.Instances.ExperienceManager.SimpleExperienceManager import SimpleExperienceManager
from StorytellingDomain.Application.Instances.Frontend.WebFrontend import WebFrontend
from CreativeWand.Utils.Misc.FileUtils import relative_path


# If you need to add new entries (new communications, differet types of frontend, experience managers, etc.)
# Add an entry in the import above, then add it to either `class_name_to_type` or `comm_list_objects`.

# Here, we define a string to class type translation dict to help us define a Creative Wand setup by these names.
# As they share common interfaces, this allows plug-and-play ness of setting up Creative Wand using modules.

class_name_to_type = {
    "ExperienceManager": SimpleExperienceManager,
    "Frontend": WebFrontend,
    "CreativeContext": StoryCreativeContext,
}

"""
Specifically for communications, we use this dictionary.
valid value formats in this dictionarys are as follows:

- type
If a single type is provided, a communication object will be created with no parameters.

- [type, dict]
If a list is provided, the first item will be interpreted as the `type` of the communication.
The second item, a `dict`, will be parsed as `**kwargs` to the communication.
"""


comm_list_objects = {"OpeningMessageComm": OpeningMessageComm, "EchoComm": EchoComm,
                     "FeedbackComm": [FeedbackComm, dict(description="Report goal completion.",
                                                         question_to_ask="Which subgoal did we achieve?",
                                                         options=[
                                                             "Start by talking about Business",
                                                             "Ending in talking about Sports",
                                                             "Mentioning Soccer",
                                                         ]
                                                         )],
                     "UserSketchComm": UserSketchComm,
                     "ShowGeneratedComm": ShowGeneratedComm, "GenerateWithSketchComm": ShowGeneratedComm,
                     "GenerateComm": GenerateComm, "GenerateWithFreezeComm": GenerateWithFreezeComm,
                     "GenerateComm_nosketch": [GenerateComm, dict(allow_no_sketch=True)],
                     "GenerateWithFreezeComm_nosketch": [GenerateWithFreezeComm, dict(allow_no_sketch=True)],
                     "GenerateCommV2": GenerateCommV2,
                     "UserWorkComm": UserWorkComm, "InspirationComm": InspirationComm,
                     "TopicRegenerationComm": TopicRegenerationComm, "SuggestSentenceComm": SuggestSentenceComm,
                     "ResetAreaComm": ResetAreaComm,
                     "FeedbackSubgoalAchieved": [FeedbackComm, dict(
                         description="Report to us on achieving subgoals.",
                         question_to_ask="Which subgoal did we achieve? (1 to 3, or None)?"
                     )],
                     "CARPFindLineByCriticComm": CARPFindLineByCriticComm,
                     "CARPFindLineByDefaultCriticComm": CARPFindLineByDefaultCriticComm,
                     "CARPFindByDefaultCriticComm": CARPFindByDefaultCriticComm,
                     "CARPTopicComm": CARPOutOfTopicDetectionComm,
                     # "CARPOOTDOnLastSentenceComm":CARPOOTDOnLastSentence,
                     "UndoComm": UndoComm,
                     }

"""
This defines groups of communications to be used in a Creative Wand setup.
"""
comm_list_presets = {
    # "s1_local_only": [
    #     "OpeningMessageComm",
    #     "FeedbackComm",
    #     "ResetAreaComm",
    #     "FeedbackSubgoalAchieved",
    #     "GenerateComm_nosketch",
    #     "GenerateWithFreezeComm_nosketch",
    #     "UserWorkComm",
    #     "CARPFindLineByCriticComm",
    # ], "s1_global_only": [
    #     "OpeningMessageComm",
    #     "FeedbackComm",
    #     "ResetAreaComm",
    #     "FeedbackSubgoalAchieved",
    #     "UserSketchComm",
    #     "GenerateWithSketchComm",
    # ],
    "s2_test": [
        "UndoComm",
        "UserSketchComm",
        "TopicRegenerationComm",
        "SuggestSentenceComm",
        "UserWorkComm",
        "GenerateCommV2",
        "CARPFindLineByCriticComm",
        "CARPFindLineByDefaultCriticComm",
        "CARPFindByDefaultCriticComm",
        "CARPTopicComm",
        "FeedbackComm",
    ], "test": list(comm_list_objects.keys())}

"""
Each session will be initiated with a mode described below.

Please also see how these information is used by the session creator in:
StorytellingDomain.Application.Instances.Frontend.WebFrontendHelper.WebFrontendServer.WebFrontendServer.home

`filtering_tags` is a special key that is used to simplify ablation building.
A communication has to 
- has a `list`-type `tag` attribute
- at least has one item in its `tag` that also exists in `filtering_args`
Or it will be removed from the communication list and not exist in the final session.

For example, if a Communication has tag `[1,2]` and
- `filtering_tags = [3,4]` : This will not be included;
- `filtering_tags = [2,3]` : This WILL be included.


"""
story_mode_table = {
    "test": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False}},
    # "local": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
    #           "presets": "s1_local_only", "goal": "story_goal_stub"},
    # "global": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
    #            "presets": "s1_global_only", "goal": "story_goal_stub"},
    "s2_f": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False}},
    # "rl": {"experience_manager_class_name": "RLEM", "domain": "story", "presets": "s1_local_only",
    #        "goal": "story_goal_stub"},
    "s2_h": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False},
             "filtering_tags": ["general", "human"]},
    "s2_a": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False},
             "filtering_tags": ["general", "agent"]},
    "s2_g": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False},
             "filtering_tags": ["general", "global"]},
    "s2_l": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False},
             "filtering_tags": ["general", "local"]},
    "s2_e": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False},
             "filtering_tags": ["general", "elaboration"]},
    "s2_r": {"experience_manager_class_name": "ExperienceManager", "domain": "story",
             "presets": "s2_test", "em_args": {"use_carp_for_options": True, "enable_interrupt": False},
             "filtering_tags": ["general", "reflection"]},
}


def generate_goal_message(mode_description):
    """
    Generate default goal message.
    """
    basepath = path.dirname(__file__)
    filepath = path.abspath(path.join(basepath, "StoryGoalMessage.md"))
    goal_str = open(filepath, "r").read()
    message = goal_str.format(
        goal_info="Create a story that \n* Start by talking about Business; \n* Ending in talking about Sports; and\n * Mentions soccer."
    )
    return message


for key in story_mode_table:
    if "goal" not in story_mode_table[key]:
        story_mode_table[key]["goal"] = generate_goal_message(story_mode_table[key])


def create_comms_from_preset(name: str) -> list:
    """
    Instantiate all communications based on the name for the preset.
    :param name: preset name.
    :return: all instantiated communications (Still needs bi
    """
    result = []
    try:
        comm_list = get_preset(name)
    except KeyError:
        raise KeyError("Unknown preset for exp_setup: %s" % name)
    if comm_list is not None:
        for item in comm_list:
            result.append(o(item))
    return result
    # sem.register_communication(o(item))
    # print("Registered: Frontend # %s" % sem.frontend.id)


def get_preset(name: str) -> list:
    """
    Get a preset communication list from the preset dictionary.
    :param name: key for the comm list.
    :return: the comm list.
    """
    return comm_list_presets[name]


def o(name: str) -> object:
    """
    Get an object from comm_list_objects.
    :param name: key
    :return: value
    """
    entry = comm_list_objects[name]
    if type(entry) is list:
        result = entry[0](**entry[1])
    else:
        result = entry()
    print("Created object: %s" % result)
    return result

# if __name__ == '__main__':
#     # Generate yml equivalent of presets.
#     import yaml
#     with open('story_runs.yaml','w') as file:
#         yaml.dump(story_mode_table,file)
#     with open('story_modes.yaml','w') as file:
#         yaml.dump(comm_list_presets,file)
