from weakref import proxy

# Modified from: https://stackoverflow.com/questions/8237390/can-a-python-singleton-class-be-inherited
class Singleton(object):
	_instance = None

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
			cls._instance.__init__(*args, **kwargs)
		return proxy(cls._instance)
