from typing import Callable
from flask_apscheduler import APScheduler
from ..singleton import Singleton
from ..manager import io

import subprocess
import threading

from .io import socketio_lock

import traceback
import os

class CoreRunner(threading.Thread):
	def send(self, line):
		if line:
			if type(line) is bytes:
				line = line.decode("utf-8")
			line = line.rstrip()
			print(line)
			socketio_lock.acquire()
			io.socketio.emit("run", line+os.linesep)
			socketio_lock.release()

	def run(self) -> None:
		try:
			p = subprocess.Popen(['viur', 'run'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			os.set_blocking(p.stdout.fileno(), False)

			while not getattr(self, "stop", False):
				## Nur zum testen
				#os.chdir("/home/cian/Projects/gruenerleben")
				#print("Testing...")
				#os.system("pipenv shell")
				#for line in iter(p.stdout.readline, b''):
				#	if line:
				#		self.send(line.rstrip())

				print("Hello!")

				#print(p.stdout.seek(0))
				line = p.stderr.readline()
				if line:
					self.send(line)

				"""line = p.stderr.readline()
				if line:
					self.send(line)"""
		except:
			traceback.print_exc()


class TaskManager(Singleton):
	def __init__(self):
		self._scheduler = APScheduler()
		self._thread: CoreRunner = None
	
	def __del__(self):
		self._scheduler.shutdown(True)
		del self._scheduler

	def add_job(self, id: str, func: Callable, **kwargs):
		self._scheduler.add_job(id, func, **kwargs)

	def is_core_running(self):
		return self._thread is not None

	def local_run(self, name: str):
		self.local_stop()
		self._thread = CoreRunner(name=name)
		self._thread.start()

	def local_stop(self):
		if self._thread:
			self._thread.stop = True
			self._thread.join()
			self._thread = None

	def start(self):
		self._scheduler.start()
