
import os
import os.path
import time
import vim

class SkimHelper(object):
  """Helps Skim do a backwards search in MacVim's terminal client"""

  def __init__(self, buffer_number):
    """Initializes the class

    :buffer_number: vim buffer number

    """
    self.buffer_number = buffer_number
    self.ticker_active = False
    self.updates_done = { "": True, "\n": True }
    self.clean_old_watch_files()
    self.maybe_update_position(fake=True)
    self.start_ticking()

  def start_ticking(self):
    """Starts the ticking loop
    :returns: nothing

    """
    if not self.ticker_active:
      vim.command('set updatetime=1000')
      vim.command('autocmd CursorHold <buffer> pythonx skim_helper().tick()')
      self.ticker_active = True

  def stop_ticking(self):
    """Stops the ticking loop
    :returns: nothing

    """
    if self.ticker_active:
      vim.command("autocmd! CursorHold <buffer>")
      self.ticker_active = False

  def tick(self):
    """Executes one iteration of the ticker loop
    :returns: nothing

    """
    self.maybe_update_position()
    vim.command('call feedkeys("f\\e")')

  def get_buffer_file(self):
    """Get the file of the buffer associated to self.
    :returns: the file name

    """
    for b in vim.buffers:
      if b.number == self.buffer_number:
        return b.name

  def get_watch_file(self):
    """Get the file used by skim to comunicate with us
    :returns: the file name

    """
    buffer_file = self.get_buffer_file()
    if buffer_file:
      watch_file = buffer_file.replace(os.path.sep, "_@_")
      watch_file = os.path.join("~", ".skim_vim_search", watch_file)
      watch_file = os.path.expanduser(watch_file)
      return watch_file

  def maybe_update_position(self, fake = False):
    """Check if Skim asked to update our position, and, if so, do it.

    :fake: if True, do not really update, but mark it as done
    :returns: nothing

    """
    watch_file_name = self.get_watch_file()
    if watch_file_name:
      try:
        with open(watch_file_name, "r") as watch_file:
          update_id = watch_file.readline()
          if update_id in self.updates_done:
            return
          new_line = int(watch_file.readline())
          new_col = 1 #int(watch_file.readline())
          if not fake:
            vim.command("call cursor({},{})".format(new_line, new_col))
            vim.command("normal zRzz")
          self.updates_done[update_id] = True
      except (IOError, ValueError):
        return

  def clean_old_watch_files(self):
    """Delete watch files older than 1 minute
    :returns: nothing

    """
    watch_dir = os.path.join("~", ".skim_vim_search")
    watch_dir = os.path.expanduser(watch_dir)
    try:
      for watch_file in os.listdir(watch_dir):
        watch_file_path = os.path.join(watch_dir, watch_file)
        st = os.stat(watch_file_path)
        if st.st_mtime < time.time() - 60:
          os.remove(watch_file_path)
    except OSError:
      return


skim_helper_farm = {}

def skim_helper(buffer_number=None):
  if buffer_number==None:
    buffer_number = vim.current.buffer.number
  if buffer_number not in skim_helper_farm:
    skim_helper_farm[buffer_number] = SkimHelper(buffer_number)
  return skim_helper_farm[buffer_number]
