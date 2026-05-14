import os, sys, subprocess;

def _EnsureBinaryFromAssembly(binary_path):
  if not binary_path.lower().endswith(".bin"):
    return
  asm_path = binary_path[:-4] + ".asm"
  if not os.path.isfile(asm_path):
    return
  if os.path.isfile(binary_path) and os.path.getmtime(binary_path) >= os.path.getmtime(asm_path):
    return
  try:
    subprocess.check_call(["nasm", "-f", "bin", asm_path, "-o", binary_path])
  except OSError as e:
    raise OSError("Cannot build %s from %s: NASM is required." % (binary_path, asm_path)) from e

def LongPath(path = None, *sub_paths):
  if not path or path == ".":
    path = os.getcwd()
  for sub_path in sub_paths:
    path = os.path.join(path, sub_path)
  # Turn relative paths into absolute paths and normalize the path
  path = os.path.abspath(path)
  # Win32 has issues with paths > MAX_PATH. The string '\\?\' allows us to work
  # around MAX_PATH limitations in most cases. One example for which this does 
  # not work is os.chdir(). No other limitations are currently known.
  # http://msdn.microsoft.com/en-us/gozerlib.ary/aa365247.aspx
  if (sys.platform == "win32") and not path.startswith(u"\\\\?\\"):
    path = u"\\\\?\\" + path
    if not path.endswith(os.sep) and os.path.isdir(path):
      # os.listdir does not work if the path is not terminated with a slash:
      path += os.sep
  return path

def ShortPath(path = None, *sub_paths):
  # Untested with paths > MAX_PATH
  path = LongPath(path, *sub_paths)
  if path.startswith("\\\\?\\"):
    path = path[4:]
  return os.path.relpath(path, os.getcwd())

def ReadFile(file_name, path=None):
  if path == None:
    path = os.getcwd()
  file_path = os.path.join(path, file_name)
  if not os.path.isfile(file_path):
    _EnsureBinaryFromAssembly(file_path)
  fd = open(file_path, "rb")
  try:
    return fd.read().decode("latin-1")
  finally:
    fd.close()

def WriteFile(file_name, contents, path=None):
  if path == None:
    path = os.getcwd()
  fd = open(os.path.join(path, file_name), "wb")
  try:
    if isinstance(contents, str):
      contents = contents.encode("latin-1")
    return fd.write(contents)
  finally:
    fd.close()
