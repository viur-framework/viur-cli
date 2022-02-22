from .bp import default
from shutil import which
from flask import jsonify, render_template
import os
import subprocess
import platform
import os
from ...manager.tasks import TaskManager

@default.route("/")
def index():
	return render_template("index.html")

@default.route("/has/<arg>")
def has(arg):
	ret = {
		"state": False,
	}

	if arg == "viur":
		has_viur = which("viur") is not None
		ret["state"] = has_viur
		if has_viur:
			ret.update({"version": subprocess.check_output(["viur", "--version"]).strip().decode("utf-8")})
	elif arg == "project":
		ret["state"] = os.path.exists(os.path.join(default.__path__, "project.json"))

	return ret

@default.route("/path")
def path():
	return default.__path__

@default.route("/user")
def user():
	return os.getlogin()

@default.route("/cwd")
def cwd():
	return os.getcwd()

@default.route("/hostname")
def hostname():
	return platform.node()

@default.route("/display")
def display():
	hostname: str = platform.node()
	if hostname.find(".") != -1:
		hostname = hostname.split(".")[0]
	return f"{os.getlogin()}@{hostname}:{os.getcwd()}$  "

@default.route("/projects")
def projects():
	return subprocess.check_output(["viur", "project", "list"])


