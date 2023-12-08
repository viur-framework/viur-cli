# dxffgxdfg"""
# Everything related to maintaining the project.json configuration file for a viur project.
# """
#
# import json
# from pprint import pprint
# import click
# import re
#
# from .utils import *
#
# project_config = None
# projectConfigFilePath = "project.json"
#
#
# def load_config(path=None):
#     """
#         Load project.json and write to the global projectConfig.
#
#         This function is responsible for loading the project.json configuration file and populating the global
#         projectConfig variable.
#         It handles error checks, such as missing or invalid JSON configuration files, and updates the project
#         configuration.
#
#         :param path: str, optional
#             The path to the project.json file. If not provided, the default projectConfigFilePath is used.
#
#         :return: dict
#             The project configuration loaded from the project.json file.
#     """
#
#     global project_config
#
#     if not path:
#         path = projectConfigFilePath
#
#         # Search in any parent folder for a project.json,
#         # change working directory because subsequent commands
#         # require for project root folder.
#         changed = False
#         while not os.path.exists(path):
#             os.chdir("..")
#             changed = True
#
#             if os.getcwd() == "/":
#                 echo_fatal(f"{path} not found - please check if you are in the right folder.")
#
#         if changed:
#             echo_info(f"Project root is {os.getcwd()}")
#
#     try:
#         f = open(path, "r")
#         project_config = json.loads(f.read())
#     except FileNotFoundError:
#         echo_fatal(f"Can't open {path} for reading")
#
#     except json.decoder.JSONDecodeError as e:
#         echo_fatal(f"The configuration in {path} contains invalid JSON: {str(e)}. Please verify right syntax.")
#
#     update_config(path)
#     return project_config
#
#
# def write_config(conf, path=None):
#     """
#     Write the current projectConfig dictionary to project.json.
#
#     This function is used to write the current project configuration, provided as a dictionary,
#     to the project.json file.
#
#     :param conf: dict
#         The project configuration to be written to the project.json file.
#
#     :param path: str, optional
#         The path to the project.json file. If not provided, the default projectConfigFilePath is used.
#
#     :return: None
#     """
#     global project_config
#
#     project_config = conf
#
#     if not path:
#         path = projectConfigFilePath
#
#     f = open(path, "w")
#     f.write(json.dumps(conf, indent=4, sort_keys=True))
#     f.close()
#
#
# def get_config():
#     """
#         Get the current project configuration.
#
#         This function returns the current project configuration stored in the global projectConfig variable.
#
#         :return: dict
#             The project configuration.
#     """
#     global project_config
#     return project_config
#
#
# def add_to_config():
#     """
#         Add a new configuration to project.json.
#
#         This function allows the addition of a new configuration to the project.json file.
#         It prompts for the configuration name, application name, and version.
#
#         :return: None
#     """
#     global project_config
#     if not project_config:
#         return
#
#     project_config.update({
#         click.prompt('name'): {
#             "application_name": click.prompt('application name'),
#             "version": click.prompt('develop version name')
#         }
#     })
#
#     write_config(project_config)
#
#
# def remove_from_config():
#     """
#     Remove a configuration from project.json.
#
#     This function allows the removal of an existing configuration from the project.json file. It prompts for the
#     configuration name to remove.
#
#     :return: None
#     """
#     global project_config
#     configname = click.prompt('name')
#     try:
#         del project_config[configname]
#         write_config(project_config)
#     except:
#         raise click.ClickException(click.style(f"{configname} not found", fg="red"))
#
# def fetch_core_version():
#     """
#     Fetch the version of the 'viur-core' package.
#
#     This function is responsible for fetching the version of the 'viur-core' package using 'pip list' and updating
#     the project configuration accordingly.
#
#     :return: None
#     """
#     try:
#         result = os.popen('pip list --format=json').read()
#         coreVersion = [x for x in json.loads(result) if x["name"] == "viur-core"][0]["version"]
#
#         project_config["default"]["core"] = coreVersion
#         write_config(project_config)
#     except:
#         if project_config and project_config["default"]:
#             project_config["default"]["core"] = "submodule"
#             write_config(project_config)
#
#
# def verions_to_builds(versionlist):
#     for entry in versionlist:
#         if entry in project_config["default"]:
#             if project_config["default"][entry]:
#                 project_config["default"]["builds"][entry] = {
#                     "command": f"viur install {entry}",
#                     "kind": "exec",
#                     "version": project_config["default"][entry].lstrip("v")
#                 }
#                 del project_config["default"][entry]
#
#
# def update_config(path=None):
#     """
#     Update the project configuration.
#
#     This function performs updates and migrations on the project configuration as needed. It includes version checks
#     and format updates. Ensure that 'load_config()' is called before invoking this function.
#
#     :param path: str, optional
#         The path to the project.json file. If not provided, the root directory of the project. is used.
#
#     :return: None
#     """
#     assert project_config, "load_config() must be called first!"
#
#     assert project_config["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "1.2.0"], \
#         "Invalid formatversion, you have to fix it manually"
#
#     if "format" not in project_config:
#         project_config["format"] = "1.0.1"
#
#     # Version 1.0.1
#     if (pyodide_version := project_config["default"].get("pyodide")) and pyodide_version.startswith("v"):
#         project_config["default"]["pyodide"] = pyodide_version[1:]  # remove v prefix
#
#     if project_config["format"] == "1.0.0":
#         project_config["format"] = "1.0.1"
#
#     # Version 1.1.1
#
#     if project_config["format"] == "1.1.0":
#         project_config["format"] = "1.1.1"
#         builds = project_config["default"].get("builds", {}).copy()
#         for k, v in builds.items():
#             if builds[k]["kind"] == "script":
#                 builds[k]["kind"] = "exec"
#         project_config["default"]["builds"] = builds
#
#     # Version 1.2.0
#     versionlist = ["admin", "scriptor", "vi"]
#
#     verions_to_builds(versionlist)
#
#     if "admin" in project_config["default"]["builds"] and "vi" in project_config["default"]["builds"]:
#         echo_info(f"It seems like you have an Admin and a Vi Version in your project.json. \n"
#                   f"per default the VI version will be overwritten by the viur-admin \n"
#                   f"if you want to keep your vi press 'n'")
#         if click.confirm(text=f"Do you want to use admin?", default=True):
#             del project_config["default"]["builds"]["vi"]
#         else:
#             del project_config["default"]["builds"]["admin"]
#
#     # conf updates must increase format version
#     write_config(project_config, path)
