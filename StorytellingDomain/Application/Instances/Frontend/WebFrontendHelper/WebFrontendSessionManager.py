"""
WebFrontendSessionManager.py

A class that manages complex objects as sessions.
"""


class SessionEndedException(BaseException):
    pass


class SessionManager:
    def __init__(self):
        self.creative_sessions = {}
        self.creative_session_vars = {}

    def create_session(self, id: str, session_obj: object) -> object:
        """
        Create a session object and put it into internal dict, then return this object.
        :param session_obj: session object to be inserted.
        :param id: Unique ID used to create this object.
        :return: the object.
        """
        if id in self.creative_sessions:
            # raise IndexError("Session already exists for %s!" % (id))
            self.destroy_session(id)
            print("Attempting to destroy a session and build a new one")
        self.creative_sessions[id] = session_obj
        self.creative_session_vars[id] = {"waiting": False, "received_msg": None}

        return self.creative_sessions[id]

    def destroy_session(self, id: str) -> bool:
        """
        Delete a session object and release resources.
        :param id: session to destroy.
        :return: whether operation is successful.
        """
        try:
            self.creative_sessions[id].end_session()
            del self.creative_sessions[id]
            del self.creative_session_vars[id]
            return True
        except IndexError:
            print("Attempting to remove a session that does not exist: %s" % id)
            return False

    def get_session(self, id: str) -> object:
        """
        Get a session object by id.
        :param id: identifier.
        :return: the session object.
        """
        if id not in self.creative_sessions:
            raise SessionEndedException("Session not exist when get_session(): %s. Maybe the session ended?" % id)
        else:
            return self.creative_sessions[id]

    def get_session_vars(self, id: str) -> object:
        if id not in self.creative_session_vars:
            raise SessionEndedException("Session not exist when get_session(): %s. Maybe the session ended?" % id)
        else:
            return self.creative_session_vars[id]

    def set_session_vars(self, id: str, obj: object) -> object:
        if id in self.creative_session_vars:
            self.creative_session_vars[id] = obj
            return self.creative_sessions[id]
        else:
            raise SessionEndedException("Session with id %s not found. Maybe the session ended?" % id)
