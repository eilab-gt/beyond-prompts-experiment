"""
PresetObjects.py

Some domain-independent pre-built objects (experience manager with communications filled in, etc.) useful for other files.

"""
from typing import Type

from CreativeWand.Framework.CreativeContext.BaseCreativeContext import BaseCreativeContext
from CreativeWand.Framework.ExperienceManager.BaseExperienceManager import BaseExperienceManager
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseFrontend

# region Register Presets
# todo: make all these dynamic
import StorytellingDomain.Application.Deployment.Presets.StoryPresets as sp

comm_presets_functions = {
    "story": sp.create_comms_from_preset,
}

domain_specific_types = {
    "story": sp.class_name_to_type,
}


# endregion

def create_session(
        experience_manager_class_name: str = "ExperienceManager",
        frontend_class_name: str = "Frontend",
        creative_context_class_name: str = "CreativeContext",
        frontend_args=None,
        creative_context_args=None,
        domain: str = None,
        presets: str = None,
        em_info: dict = None,
        filtering_tags: list = None,
):
    """
    Creates a new experienceManager object with specified paramters.
    This function first translate names into their corresponding classes.
    :param filtering_tags: if not None, only communications with at least one tag (OR) in filtering_tags will be created.
    :param experience_manager_class_name: name of the experience manager class.
    :param frontend_class_name: name of the frontend.
    :param creative_context_class_name: name of the creative context.
    :param frontend_args: arguments to pass to the frontend __init__().
    :param creative_context_args: arguments to pass to the CreativeContext __init__().
    :param domain: domain of this setup, used to find communications.
    :param presets: preset name for communications, used to find communications.
    :param em_info: passed as `info` argument to the experiment manager __init__().
    :return: The experience manager.
    """
    emc = domain_specific_types[domain][experience_manager_class_name]
    fc = domain_specific_types[domain][frontend_class_name]
    ccc = domain_specific_types[domain][creative_context_class_name]

    return create_session_helper(
        experience_manager_class=emc, frontend_class=fc, creative_context_class=ccc,
        frontend_args=frontend_args,
        creative_context_args=creative_context_args,
        domain=domain,
        presets=presets,
        em_info=em_info,
        filtering_tags=filtering_tags
    )


def create_session_helper(
        experience_manager_class: type,
        frontend_class: type,
        creative_context_class: type,
        frontend_args=None,
        creative_context_args=None,
        domain: str = None,
        presets: str = None,
        em_info: dict = None,
        filtering_tags: list = None,
):
    """
    Creates a new experienceManager object with specified paramters.
    :param filtering_tags: if not None, only communications with at least one tag (OR) in filtering_tags will be created.
    :param experience_manager_class: class type of the experience manager.
    :param frontend_class: class type of the frontend.
    :param creative_context_class: class type of the creative context.
    :param frontend_args: arguments to pass to the frontend __init__().
    :param creative_context_args: arguments to pass to the CreativeContext __init__().
    :param domain: domain of this setup, used to find communications.
    :param presets: preset name for communications, used to find communications.
    :param em_info: passed as `info` argument to the experiment manager __init__().
    :return: The experience manager.
    """
    if creative_context_args is None:
        creative_context_args = {}
    if frontend_args is None:
        frontend_args = {}
    sem = experience_manager_class(frontend=frontend_class(**frontend_args), info=em_info)
    sem.bind_creative_context(creative_context_class(**creative_context_args))
    comms = comm_presets_functions[domain](name=presets)
    for item in comms:
        if filtering_tags is not None:
            if not hasattr(item, "tag"):
                print("Skipped %s as it has no tag." % item)
                continue
            found_tag = False
            for filter_tag in filtering_tags:
                if filter_tag in item.tag:
                    found_tag = True
                    break
            if not found_tag:
                print("Skipped %s as none of the tag (from %s) is in %s." % (str(item), item.tag, filtering_tags))
                continue
        sem.register_communication(item)
    return sem


def create_session_directly_from_objects(
        experience_manager_object: Type[BaseExperienceManager],
        frontend_object: Type[BaseFrontend],
        creative_context_object: Type[BaseCreativeContext],
        communication_objects=None,
):
    """
    Set up a creative session directly from objects.
    :param experience_manager_object: Created experience
    :param frontend_object: if not None, frontend object to be binded to experience manager.
    :param creative_context_object: creative context to be binded.
    :param communication_objects: communications to be used.
    """
    if communication_objects is None:
        print("No communication specified, will create an experience manager with no communications!")
        communication_objects = []
    experience_manager_object.bind_creative_context(creative_context_object)
    if frontend_object is not None:
        experience_manager_object.bind_frontend(frontend_object)
    for item in communication_objects:
        experience_manager_object.register_communication(item)
    return experience_manager_object
