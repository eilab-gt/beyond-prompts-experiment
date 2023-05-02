import sys
import threading
import time

from flask import Flask, Response
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO

from StorytellingDomain.Application.Deployment.PresetObjects import create_session
from StorytellingDomain.Application.Instances.Frontend.WebFrontendHelper.WebFrontendSessionManager import SessionManager

# Put your SSL PEMs here.
default_ssl_params = {"ssl_context": (
    "/home/zhiyu/cert/fullchain.pem",
    "/home/zhiyu/cert/privkey.pem",)
}

from StorytellingDomain.Application.Instances.Frontend.WebFrontend import WebFrontend


class WebFrontendServer():
    def __init__(self, mode_table: dict = None, api_table: dict = None):
        """
        Create a new server object with mode configurations as a dict.
        mode_table should be in this format:
        "mode_name":{"experience_manager_class_name":"x","domain":"x","presets":"x"}

        This Server by default creates a WebFrontend.

        :param mode_table: mode configuration dict.
        :param api_table: api configuration dict. Passed directly to CreativeContext init.
        """
        self.all_sess = SessionManager()

        self.api_table = api_table

        self.mode_table = mode_table
        if self.mode_table is None:
            self.mode_table = {}
            print("No mode_table specified, all runs will go with defaults...")

        self.app = Flask(__name__)

        self.app.secret_key = 'creative_wand_T0P@Secret'
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins='*')
        self.list_of_managers = {}
        self.register_routes()

    def register_routes(self):
        """
        Register all flask routes.
        As we are now putting routes into class methods, we can't directly decorate it anymore.
        :return: None.
        """
        self.socketio.on_event("chat_message", self.handle_chat_message)
        self.app.route("/")(self.test)
        self.app.route("/startup", methods=['POST'])(self.home)
        self.app.route("/end_session", methods=['POST'])(self.handle_end_session)
        self.app.route("/get_goal", methods=['GET'])(self.handle_get_goal)

    def start_server(self, run_async=True, run_ssl=False):
        """
        Start running the server with the configurations preset.
        :param run_async: Whether to run the server asynchronously or not (if not block anything later from happening).
        :param run_ssl: Run the server in HTTPS mode (set certificate files in `default_ssl_params`)
        :return: None.
        """

        if run_ssl:
            ssl_params = default_ssl_params
        else:
            ssl_params = {}

        def run_async_stub():
            try:
                self.socketio.run(self.app, host='0.0.0.0', port=8000, debug=True, use_reloader=False,
                                  allow_unsafe_werkzeug=True, **ssl_params)
            except TypeError as e:
                if "werkzeug" in str(e):
                    print("Attempting to run the server again without allow_unsafe_werkzeug option...")
                    self.socketio.run(self.app, host='0.0.0.0', port=8000, debug=True,
                                      use_reloader=False, **ssl_params)

        if run_async:
            t = threading.Thread(target=run_async_stub)
            t.start()
        else:
            self.socketio.run(self.app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True, **ssl_params)

    # def _register_managers(self, session_type, obj):
    #     self.list_of_managers[session_type] = obj

    def send_chat_message(self, message, session_id, wait, options: list = None):
        """
        Send a chat message to the React frontend.
        They can be accompanied by "options" in list with each object following
        {"label":<label>,"value":<simulated_user_reply>} format.
        :param message: Payload.
        :param session_id: Which session to send the message to.
        :param wait: Whether to wait for a response.
        :param options: (list of dicts) When not None, the frontend will show "quick buttons".
        :return: If wait is True, the response payload. Else None.
        """
        time.sleep(0.3)
        obj_to_emit = {"message": message, "id": session_id}
        if options is not None:
            obj_to_emit["options"] = options
        self.socketio.emit('message', obj_to_emit)#, json=True)
        if wait:
            self.all_sess.set_session_vars(session_id, {"received_msg": None, "waiting": True})
            while self.all_sess.get_session_vars(session_id)['waiting']:
                time.sleep(0.001)
                continue
            msg = self.all_sess.get_session_vars(session_id)['received_msg']
            self.all_sess.set_session_vars(session_id, {"received_msg": None, "waiting": False})
            return msg
        else:
            return

    # def send_doc(doc, sketch, session_id):
    #     send_object(event='document', obj={"document": doc, "sketch": sketch, "id": session_id})
    #     # socketio.emit('document', {"document": doc, "sketch": sketch}, json=True)

    def send_object(self, event, obj):
        """
        Send an object to the React Frontend.
        :param event: name of the event (both side needs to use the same event name.)
        :param obj: Payload.
        :return: None.
        """
        print(f"Sending object event:{event} obj:{obj}")
        self.socketio.emit(event, obj)#, json=True)

    def receive_object(self, session_id, info):
        """
        Receive information from react side and save it somewhere.
        :param info: Object to save.
        :return:
        """
        # todo: Rohan - Find a way to call this function
        self.sess = self.all_sess.get_session(session_id)
        self.sess.manager.set_state(info)  # Parse this into any form you like

    # endregion

    # region Flask routes
    def test(self):
        return "There is nothing here."

    # @route('/startup', methods=["POST"])
    def home(self):
        """
        Main function to handle a session. Based on request parameters
        A session is created. This function just create the session and its id.
        :return:
        """
        this_id = request.json['id']
        this_code = request.json['code']
        this_mode = request.json['mode']
        if this_mode is None:
            print("No mode specified.")
            this_mode = "Default"
        print("MODE: %s" % this_mode)
        print(type(this_mode))
        print("start startup on %s, %s" % (this_id, this_code))

        frontend = WebFrontend(server_object=self, id=this_id)

        # Info to pass to the just-built experience manager
        em_info = {"session_code": this_code}

        creative_session = None

        # set fail-safe defaults
        domain = "story"
        presets = "s1_global_only"
        em_name = "ExperienceManager"
        goal = "Failed to get goal!"
        em_extra_args = {}

        if this_mode in self.mode_table:
            all_args = self.mode_table[this_mode]
            domain = all_args.get("domain", "story")
            presets = all_args.get("presets", "test")
            em_name = all_args.get("experience_manager_class_name", "ExperienceManager")
            filtering_tags = all_args.get("filtering_tags", None)
            goal = all_args.get("goal", "Goal missing - If you see this as a participant let us know!")
            em_extra_args = all_args.get("em_args", {})
            # try:
            #     domain = self.mode_table[this_mode]["domain"]
            #     presets = self.mode_table[this_mode]["presets"]
            #     em_name = self.mode_table[this_mode]["experience_manager_class_name"]
            #     goal = self.mode_table[this_mode]["goal"]
            #     em_extra_args = self.mode_table[this_mode]["em_args"]
            # except Exception as e:
            #     print(str(e))
            #     print("Mode settings broken: %s, only parsed part of config..." % this_mode)
        else:
            print("Unknown mode: %s, using default params..." % this_mode)

        print("API_TABLE: %s" % self.api_table)
        em_info = {"session_id": this_id, "session_type": presets, "session_mode": this_mode, "session_code": this_code,
                   "session_goal": goal}
        for key in em_extra_args:
            em_info[key] = em_extra_args[key]
        creative_session = create_session(
            experience_manager_class_name=em_name,
            frontend_args={"server_object": self,
                           "id": this_id},
            creative_context_args={
                "api_profile": self.api_table,
            },
            domain=domain, presets=presets,
            em_info=em_info,
            filtering_tags=filtering_tags
        )

        # if "1" in this_mode:
        #     creative_session = get_story_creative_session(
        #         id=this_id, frontend=frontend, exp_setup="s1_local_only", em_info=em_info)
        # elif "2" in this_mode:
        #     creative_session = get_story_creative_session(
        #         id=this_id, frontend=frontend, exp_setup="s1_global_only", em_info=em_info)
        # elif "test" in this_mode:
        #     print("New interface")
        #     creative_session = create_session(
        #         experience_manager_class_name="RLEM",
        #         frontend_args={"server_object": self,
        #                        "id": this_id},
        #         domain="story", presets="s1_local_only",
        #         em_info={"session_id": this_id, "session_type": "s1_local_only"}
        #     )
        # else:
        #     # raise ValueError()
        #     creative_session = get_story_creative_session(
        #         id=this_id, frontend=frontend, exp_setup="test", em_info=em_info)

        self.all_sess.create_session(id=this_id, session_obj=creative_session)
        print("Now we have %s sessions." % self.all_sess.creative_sessions.__len__())
        creative_session.start_session()
        print("Session %s finished. " % this_id)
        return "Done"

    def handle_get_goal(self):
        """
        Returns a string representing the goal for a specific mode.
        :return: paragraph containing this information.
        """
        code = request.args['id']
        session = self.all_sess.get_session(code)
        goal = session.info["session_goal"]

        resp = Response(goal)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

        # return goal

    # @route('/end_session', methods=['POST'])
    def handle_end_session(self):
        """
        Kill a session and remove its id from session manager.
        :return: id of session that just gets killed.
        """
        code = request.json['id']
        print("Received end session: %s" % code)
        self.all_sess.destroy_session(code)
        return code

    # @socketio.on('chat_message')
    def handle_chat_message(self, json):
        """
        Remotely called, pass a message payload to a session.
        :param json: message payload.
        :return: None
        """
        # print('received chat_message: ' + str(json['message']))

        received_msg = str(json['message'])
        received_code = str(json['id'])
        self.all_sess.set_session_vars(received_code, {"waiting": False, "received_msg": received_msg})


# endregion


if __name__ == '__main__':
    # Test code
    obj = WebFrontendServer(api_table={"gen": "local"})
    obj.start_server(run_async=True)
