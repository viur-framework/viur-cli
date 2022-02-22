import socketio
import threading
from ..singleton import Singleton
from flask_socketio import SocketIO, Namespace
from flask import Flask
from weakref import proxy

class SocketIoManager(Singleton):
	def __init__(self) -> None:
		self._socket_io = SocketIO(cors_allowed_origins="*")

	@property
	def socket_io(self) -> SocketIO:
		return self._socket_io

	def init_app(self, app: Flask):
		self._socket_io.init_app(app)
		##self._socket_io.emit("log", ".....")

	def run(self, app:Flask, host=None, port=None, **kwargs):
		self._socket_io.run(app, host, port, **kwargs)


socketio_lock = threading.Lock()

socketio: SocketIO = proxy(SocketIoManager()._socket_io)

@socketio.event()
def connect():
	socketio_lock.acquire()
	socketio.emit("log", "HELLO")
	socketio_lock.release()


