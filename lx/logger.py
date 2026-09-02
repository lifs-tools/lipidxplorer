import time
import builtins
import re
import sys


class _LineBuffer:
    """Collect fragmentary stream writes and emit them one whole line at a time.

    traceback.print_exc() and warnings.warn() reach sys.stderr as several
    write() calls per line. Logging each call separately would stamp a
    timestamp into the middle of a sentence, so hold on to a partial line
    until its newline arrives.
    """

    def __init__(self, emit):
        self._emit = emit
        self._buffer = ""

    def write(self, data):
        if not data:
            return
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self._emit(line)

    def flush(self):
        if self._buffer:
            line, self._buffer = self._buffer, ""
            if line.strip():
                self._emit(line)


class TeeLogger:
    def __init__(self, gui_writer=None, file_path=None, also_stdout=False,
                 context=""):
        self.gui_writer = gui_writer
        self.file_path = file_path
        self.also_stdout = also_stdout
        # Stamped onto every line, so controller output is as attributable as
        # the workers' -- including lines from code that has no idea a batch
        # is running (see _WorkerLog in lx.batch_processor).
        self.context = context

        # Save original print
        self._original_print = builtins.print

        # Set by install_as_streams(); see restore_streams().
        self._saved_stdout = None
        self._saved_stderr = None
        self._stream = None

        # Ensure log file exists
        if file_path:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("")

    def log(self, text):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        prefix = f"{timestamp} {self.context}" if self.context else timestamp
        line = f"{prefix} {text}"

        # GUI output
        if self.gui_writer:
            try:
                self.gui_writer.write(line + "\n")
            except Exception:
                pass

        # File output
        if self.file_path:
            try:
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

        # Stdout output (safe)
        if self.also_stdout:
            self._original_print(line)

    # ------------------------------------------------------------
    # SAFE write() for TextIO + print()
    # ------------------------------------------------------------
    def write(self, data, *args, **kwargs):
        if not data:
            return

        # Remove newline only
        text = data.rstrip("\n")

        # Ignore pure whitespace or empty strings
        if not text.strip():
            return

        # Ignore lines that are JUST a timestamp (created by logger)
        if re.fullmatch(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]", text.strip()):
            return

        # Finally log normally
        self.log(text)


    def flush(self):
        pass

    # ------------------------------------------------------------
    # SAFE install_as_print() without recursion
    # ------------------------------------------------------------
    def install_as_print(self):
        def print_override(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            self.log(text)

        builtins.print = print_override

    def restore_print(self):
        """Undo install_as_print().

        Without this, builtins.print stays bound to a finished run's logger
        for the rest of the session, so anything printed afterwards is filed
        away into that run's log instead of reaching the user.
        """
        builtins.print = self._original_print

    def install_as_streams(self):
        """Route sys.stdout and sys.stderr here as well as print().

        install_as_print() only rebinds builtins.print, but warnings.warn()
        and traceback.print_exc() write straight to sys.stderr. In a windowed
        PyInstaller build that is a null sink, so those messages vanish --
        including "Could not detect delimiter ... falling back to comma",
        which silently changes how a result file is parsed.
        """
        if self._saved_stdout is None:
            self._saved_stdout = sys.stdout
            self._saved_stderr = sys.stderr

        self._stream = _LineBuffer(self.log)
        sys.stdout = self._stream
        sys.stderr = self._stream

    def restore_streams(self):
        """Undo install_as_streams(), flushing any partial line first."""
        if self._stream is not None:
            self._stream.flush()
            self._stream = None

        if self._saved_stdout is not None:
            sys.stdout = self._saved_stdout
            sys.stderr = self._saved_stderr
            self._saved_stdout = None
            self._saved_stderr = None
