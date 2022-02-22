import flask
from .routes import default
from flask_cors import CORS
from .manager.tasks import TaskManager
from .manager.io import SocketIoManager
from .manager.app import App
from .routes import routes

#import viur
import os
import logging

def main():
	logging.getLogger().setLevel(logging.DEBUG)

	#for k, v in viur.ViurCommandManager().items():
	#	build_params = "".join([f"<{arg}>/" for arg in v.args])
	#	App().app.add_url_rule(f"/cmd/{k}/{build_params}", None, v, methods=["GET", "POST"])

	for route in routes:
		route.__path__ = os.path.dirname(__file__)
		App().register_blueprint(route)

	TaskManager().start()
	SocketIoManager().init_app(App().app)

	SocketIoManager().run(App().app, debug=True, host="127.0.0.1", port=63901)
