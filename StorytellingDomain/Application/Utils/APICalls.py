"""
APICalls.py

This file contains endpoints shared by multiple modules of the Application.

"""

# region api calls
from typing import Union

from CreativeWand.Utils.Network.RemoteAPI import RemoteAPIInterface
from StorytellingDomain.Application.Config.CreativeContextConfig import available_configs, available_carp_configs

default_connection_profile = "local"

default_carp_connection_profile = "local"


def call_generation_interface(
        prompt: str,
        topic: dict,
        connection_profile=None,
):
    """
    Utility function to call remote generation interface.
    :param prompt: the sentence to be continued.
    :param topic: topic weights used for generation.
    :return: sentence generated from remote API.
    """

    if connection_profile is None:
        connection_profile = default_connection_profile

    default_server_addr = available_configs[connection_profile]["default_server_addr"]
    generate_api_route = available_configs[connection_profile]["generate_api_route"]

    call_result = RemoteAPIInterface.request(
        method="POST",
        address="%s%s" % (default_server_addr, generate_api_route),
        data={"skill": 0,
              "sentence": prompt,
              "topic": topic, "task": "generation"}
    )

    if call_result.success:
        # Retrieve just the generated sentences.
        # return call_result.payload['out']['out_sentence'] #StorytellingDomain
        return call_result.payload['out_sentence']
    else:
        raise RuntimeError("Failed to call API: %s" % call_result.payload)


def call_carp_interface(
        stories: list,
        reviews: Union[list, dict],
        version: int,
        connection_profile: str = None,
):
    """
    Utility used to call CARP interface.

    for `reviews` if it is a dict then the value of each key will be used as the threshold
    for activation. (If carp score < value of key, then it will not be returned.)
    If list, all scores will be returned.

    :param stories: Lines of stories.
    :param reviews: Lines of "reviews".
    :param version: version of the CARP interface to be called.
    :param connection_profile: endpoint used to call remote API.
    :return: For each review line, which sentence in the `stories` matches it best.
    (In dict form, where key is review line and value is exact sentence.
    """
    if connection_profile is None:
        connection_profile = default_carp_connection_profile

    default_server_addr = available_carp_configs[connection_profile]["default_server_addr"]
    generate_api_route = available_carp_configs[connection_profile]["carp_api_route"]

    call_result = RemoteAPIInterface.request(
        method="POST",
        address="%s%s" % (default_server_addr, generate_api_route),
        data={"stories": stories, "reviews": reviews, "version": version}
    )

    if call_result.success:
        # Retrieve just the generated sentences.
        # return call_result.payload['out']['out_sentence'] #StorytellingDomain
        return call_result.payload
    else:
        raise RuntimeError("Failed to call API: %s" % call_result.payload)

# endregion
