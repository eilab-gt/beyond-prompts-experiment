"""
StartAddonServer.py

Start an addon server for this domain.
"""

from CreativeWand.Addons.WebServer.AddonServer import run_addon_server
from StorytellingDomain.Application.Deployment.Addons.PNB.endpoint import PNBTool
from StorytellingDomain.Application.Deployment.Addons.CARP.endpoint import CARPTool

if __name__ == '__main__':
    """
    Default sets of API configurations for addons, that is passed to `run_addon_server`.
    Also see docs on `run_addon_server`.
    """
    tool_config = {
        "pnb": {  # Name of the tool (matched with `tools_to_enable`)
            "class": PNBTool,  # A class that has __call__(self, body) => return_value
            "config": {  # They are directly passed as `config` parameter for `__init__()`
                "base_location": "/mnt/hdd/trained_models/skill_model/ROC-large_v201",
                "gedi_location": "/mnt/hdd/trained_models/gedi_base/gedi_topic/",
            }
        },
        "carp": {
            "file": "CARP.endpoint",
            "class": CARPTool,
            "func": None,
            "config": {
                "carp_model_path":"/mnt/hdd/datasets/carp/CARP_L.pt",
            }
        },
        "pnb-gptj": {
            "external-name":"pnb",
            "file": "PNB.endpoint",
            "class": PNBTool,
            "func": None,
            "config": {
                "slurm": "yep",  # anything works here, this triggers routines for gpt-j
                "gedi_location": "/home/gpu_sudo/projects/creative-wand/models/gedi/gedi_topic",
            }
        },
        "carp-fiyero": {
            "external-name":"carp",
            "file": "CARP.endpoint",
            "class": CARPTool,
            "func": None,
            "config": {
                "carp_model_path": "/home/gpu_sudo/home/gpu_sudo/datasets/CARP_L.pt",
            }
        },
        "carp-slurm": {
            "external-name":"carp",
            "file": "CARP.endpoint",
            "class": CARPTool,
            "func": None,
            "config": {
                "carp_model_path": "/coc/flash5/zlin304/models/carp/CARP_L.pt",
            }
        },
        "pnb-slurm": {
            "external-name":"pnb",
            "file": "PNB.endpoint",
            "class": PNBTool,
            "func": None,
            "config": {
                "slurm": "yep",  # anything works here, this triggers routines for gpt-j
                "gedi_location": "/coc/flash5/zlin304/models/gedi/gedi_topic",
            }
        },
        "carp-demo-release": {
            "external-name": "carp",
            "file": "CARP.endpoint",
            "class": CARPTool,
            "func": None,
            "config": {
                "carp_model_path": "Models/carp/CARP_L.pt",
            }
        },
        "pnb-demo-release": {
            "external-name": "pnb",
            "file": "PNB.endpoint",
            "class": PNBTool,
            "func": None,
            "config": {
                "slurm": "yep",  # anything works here, this triggers routines for gpt-j
                "gedi_location": "Models/gedi/gedi_topic",
            }
        },
        "pnb-demo-release-small": {
            "external-name": "pnb",
            "file": "PNB.endpoint",
            "class": PNBTool,
            "func": None,
            "config": {
                #"slurm": "yep",  # anything works here, this triggers routines for gpt-j
                "gedi_location": "Models/gedi/gedi_topic",
            }
        },

    }

    # "pnb": {
    #     "file": "PNB.endpoint",
    #     "class": "PNBTool",
    #     "func": None,
    #     "config": {
    #         "base_location": "/mnt/hdd/trained_models/skill_model/ROC-large_v201",
    #         "gedi_location": "/mnt/hdd/trained_models/gedi_base/gedi_topic/",
    #     }
    # },
    # "pnb-gptj": {
    #     "file": "PNB.endpoint",
    #     "class": "PNBTool",
    #     "func": None,
    #     "config": {
    #         "slurm": "yep",  # anything works here, this triggers routines for gpt-j
    #         "gedi_location": "/home/gpu_sudo/projects/creative-wand/models/gedi/gedi_topic",
    #     }
    # },
    # "carp": {
    #     "file": "CARP.endpoint",
    #     "class": "CARPTool",
    #     "func": None,
    #     "config": {
    #         "intentionally-left-blank": None,
    #     }
    # },

    run_addon_server(
        tool_config=tool_config,
    )
