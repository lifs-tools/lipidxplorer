"""Save a file with a "file is open in another program, try again?" loop.

startMFQL() runs on the GUI's Worker thread, but wx dialogs may only be
created and shown on the main (GUI) thread; wxOSX and wxGTK crash or hang
otherwise. ask_yes_no() therefore shows the dialog on the main thread via
wx.CallAfter and blocks the calling worker thread until the user answers.
"""
import queue

import wx


def ask_yes_no(parent, message, caption):
	"""Show a Yes/No question on the GUI thread, from any thread.

	Returns wx.ID_YES or wx.ID_NO. Called from a worker thread it waits for
	the answer; the main thread keeps running its event loop meanwhile.
	"""
	def show():
		dlg = wx.MessageDialog(parent, message, caption, wx.YES_NO | wx.ICON_QUESTION)
		try:
			return dlg.ShowModal()
		finally:
			dlg.Destroy()

	if wx.IsMainThread():
		return show()

	answer = queue.Queue(maxsize=1)

	def show_and_reply():
		try:
			result = show()
		except Exception:
			# never leave the worker waiting forever
			answer.put(wx.ID_NO)
			raise
		answer.put(result)

	wx.CallAfter(show_and_reply)
	return answer.get()


def save_with_retry(save, parent, what, ask=ask_yes_no):
	"""Call save() until it succeeds or the user gives up.

	save:   a no-argument callable that writes the file
	parent: the GUI frame, or None when there is no GUI (then a failure is
	        reported once on stdout and not retried)
	what:   what is being saved, for the messages, e.g. "MasterScan"
	ask:    the question function; replaceable for tests

	Returns True if the file was saved, False if not.
	"""
	while True:
		try:
			save()
			return True
		except OSError:
			if parent is None:
				print("Error: could not save %s" % what)
				return False
			message = ("The %s cannot be saved. It is probably open by another "
				"program. Try again?" % what)
			if ask(parent, message, "File writing error") != wx.ID_YES:
				return False
