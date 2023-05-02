"""
StartExperiment.py

A universal entrypoint to define what systems to be available for experiments.

To use this entrypoint:

python StartExperiment.py [-c config_file]

Config files are in the following format:

{
    "mode": "story", # "Domain" used for experiments
    "api_profile": {
        "gen": "local",
    } # This is passed as parameters `api_profile` for CreativeContext if supported and provided.
}

"""

import argparse
import json

from StorytellingDomain.Application.Deployment.Presets.StoryPresets import story_mode_table
from StorytellingDomain.Application.Instances.Frontend.WebFrontendHelper.WebFrontendServer import WebFrontendServer


class ExperienceHost:
    def __init__(self, config):
        """
        Initialize the Experiment Host with a configuration dict.
        :param config: configuration dict.
        """
        if 'mode' in config:
            self.mode = config['mode']
        else:
            raise AttributeError("mode missing in config file.")
        if 'api_profile' in config:
            self.api_profile = config['api_profile']
        else:
            raise AttributeError("api_profile missing in config file.")
        if 'mode_table' in config:
            self.mode_table = config['mode_table']
        else:
            self.mode_table = story_mode_table

    def start_experiment(self, run_ssl=False):
        """
        Start the experiment server.
        :param run_ssl: Whether to run this server in HTTPS.
        :return: None (Use CTRL+C to stop the server)
        """
        if self.mode == "story":
            obj = WebFrontendServer(
                mode_table=story_mode_table,
                api_table=self.api_profile
            )
            obj.start_server(run_async=True, run_ssl=run_ssl)
        else:
            raise NotImplementedError
        print("Experiment Started")


# Fail-safes.
default_config = {
    "mode": "story",
    "api_profile": {
        "gen": "local",
    },
    "https":False,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config_file_path', help="config file path", default="")
    parser.add_argument('-s', '--https', action="store_true", help="run the server in https mode")
    args = parser.parse_args()
    path = args.config_file_path
    if len(path) >= 1:
        config_content = json.load(open(path, 'r'))
    else:
        config_content = default_config
    host = ExperienceHost(config=config_content)
    host.start_experiment(run_ssl=args.https)


if __name__ == '__main__':
    main()
