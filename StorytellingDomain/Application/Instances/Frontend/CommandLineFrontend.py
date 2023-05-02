"""
CommandLineFrontend.py

An entry point for using command lines to interact with creative wand.

Mostly for testing now.
"""
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseFrontend, BaseRequest


class CommandLineFrontend(BaseFrontend):

    @BaseFrontend.save_logs
    def get_information(self, request: BaseRequest) -> object:
        result = input(request.message)
        return result

    @BaseFrontend.save_logs
    def send_information(self, info: BaseRequest):
        print(info.message)

    def set_information(self, info: object):
        raise NotImplementedError("This frontend does not support user providing information without a request.")
