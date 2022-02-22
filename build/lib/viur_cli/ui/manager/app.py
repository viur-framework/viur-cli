from ..singleton import Singleton
from flask import Flask, Blueprint
from flask_cors import CORS
import os.path

__path__ = os.path.dirname(__file__)
class App(Singleton):
	def __init__(self) -> None:
		path = os.path.join(__path__, "..", "static")
		print(path)
		self._app = Flask(__name__, static_folder=path, template_folder=path, static_url_path='')
		CORS(self._app)

	@property
	def app(self) -> Flask:
		return self._app

	def register_blueprint(self, _bp: Blueprint) -> None:
		self._app.register_blueprint(_bp)