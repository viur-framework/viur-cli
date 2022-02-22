from flask import jsonify
from .bp import project
from ...manager.tasks import TaskManager

@project.route("/state")
def state():
	return jsonify(TaskManager().is_core_running())

@project.route("/start", methods=["POST"])
def start():
	
	state = TaskManager().is_core_running()
	if not TaskManager().is_core_running():
		TaskManager().local_run("server")
		state = True

	return jsonify(state)

@project.route("/stop", methods=["POST"])
def stop():
	
	state = TaskManager().is_core_running()
	if TaskManager().is_core_running():
		TaskManager().local_stop()
		state = False

	return jsonify(state)