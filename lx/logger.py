import time
import builtins
import re

class TeeLogger:
    def __init__(self, gui_writer=None, file_path=None, also_stdout=False):
        self.gui_writer = gui_writer
        self.file_path = file_path
        self.also_stdout = also_stdout

        # Save original print
        self._original_print = builtins.print

        # Ensure log file exists
        if file_path:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("")

    def log(self, text):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        line = f"{timestamp} {text}"

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
