"""
WebFrontend.py

Describes the prototype interface the creative wand uses to get/present information.
"""

from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseFrontend, BaseRequest


class WebFrontend(BaseFrontend):
    def __init__(self, server_object, id):
        super().__init__()
        self.server_obj = server_object
        # self.send_chat_message = send_chat_message
        # self.send_object = send_object
        self.id = id
        self.set_state("id", id)

    @BaseFrontend.save_logs
    def get_information(self, request: BaseRequest) -> object:
        options = request.info['options'] if 'options' in request.info else None
        msg = self.server_obj.send_chat_message(request.message, self.id, wait=True, options=options)
        if msg == "[cancel]":
            raise InterruptedError("Canceling current communication and going back to main menu.")
        if request.cast_to is not None:
            msg = request.cast_to(msg)
        return msg

    @BaseFrontend.save_logs
    def send_information(self, info: BaseRequest):
        options = info.info['options'] if 'options' in info.info else None
        self.server_obj.send_chat_message(info.message, self.id, wait=False, options=options)

    def set_information(self, info: object):
        raise NotImplementedError("This frontend does not support user providing information without a request.")
        pass

    @BaseFrontend.save_logs
    def sync_react_states(self, keys: list = None):
        """
        When called, information stored in `state` will be sent to the React frontend.
        :param keys: If not None, only send keys in `state` in `keys`.
        :return:
        """
        result = {}
        if keys is None:
            result = self.state
        else:
            for item in keys:
                result[item] = self.get_state(item)
        print("Object sent to frontend: %s" % result)
        self.server_obj.send_object(event="document", obj=result)

    @BaseFrontend.save_logs
    def set_doc(self, doc: dict):
        raise DeprecationWarning("set_doc is deprecated.")
        # self.send_object(doc, sketch, self.id)
        obj = {}
        if "id" in doc:
            raise AttributeError("Conflicting keys for set_doc; id")
        for key in doc:
            obj[key] = doc[key]
        obj["id"] = self.id
        print("Object sent to frontend: %s" % obj)
        self.server_obj.send_object(event="document", obj=obj)
        # self.send_object(event='document', obj={"document": doc, "sketch": sketch, "id": self.id})

    def send_kill_to_react(self):
        print("Attemptiong to kill react session %s" % self.id)
        self.server_obj.send_object(event="kill_session", obj={"id": self.id})
