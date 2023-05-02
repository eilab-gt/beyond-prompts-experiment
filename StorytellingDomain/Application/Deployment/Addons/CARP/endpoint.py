"""
endpoint.py

Endpoint for Plug & Blend Tool.
"""
from StorytellingDomain.Application.Deployment.Addons.CARP.carp_service.carp import CARPWorkflow


class CARPTool:
    def __init__(self, config):
        self.workflow = CARPWorkflow(config)

    def __call__(self, body):
        if "stories" not in body or "reviews" not in body:
            raise AttributeError("Bad request.")
        if "version" not in body:
            version = 1
        else:
            version = int(body["version"])
        return self.workflow(stories=body['stories'], reviews=body["reviews"], version=version)
