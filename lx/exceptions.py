import traceback
import sys

# for exception forwarding
def formatExceptionInfo(maxTBlevel=None):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        #excArgs = exc.__dict__["args"]
        excArgs = exc.args
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb, exc)

class LipidXException(Exception):

	def __init__(self, head, body = "", exc_args = ()):
		self.head = head
		self.body = body

		#(excName, excArgs, excTb, exc)
		self.exc_args = ()

	def __str__(self):
		return repr(self.head)

class SyntaxErrorException(Exception):

	def __init__(self, p_value, queryName, lineno, end = ""):
		self.p_value = p_value
		self.queryName = queryName
		self.lineno = lineno

	def __str__(self):
		return repr(self.p_value)

class ImportException(Exception):

	def __init__(self, text):
		self.value = text

	def __str__(self):
		return repr(self.value)

class MyOptionsExcp(Exception):

	def __init__(self, option):
		self.value = option

	def __str__(self):
		return repr(self.value)

class MyScanExcp(Exception):

	def __init__(self, option):
		self.value = option

	def __str__(self):
		return repr(self.value)

class MyMissingArgExcp(Exception):

	def __init__(self, attr):
		self.attr = attr

	def __str__(self):
		return repr(self.attr)

class MySemanticExcp(Exception):

	def __init__(self, attr):
		self.attr = attr

	def __str__(self):
		return repr(self.attr)

class MyVariableException(Exception):

	def __init__(self, attr):
		self.attr = attr

	def __str__(self):
		return repr(self.attr)

class LogicErrorException(Exception):

	def __init__(self, text):
		self.value = text

	def __str__(self):
		return repr(self.value)

