"""
endpoint.py

Endpoint for Plug & Blend Tool.
"""
from StorytellingDomain.Application.Deployment.Addons.PNB.pnb2.pnb_logits_processor import PNBWorkflow


class PNBTool:
    def __init__(self, config):
        self.workflow = PNBWorkflow(config)

    def __call__(self, body):
        return self.workflow(body)
