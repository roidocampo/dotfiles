
import sys
import multiprocessing
import subprocess

try:
    pyexe
except:
    pyexe = subprocess.getoutput('which python')
    sys.executable = pyexe
    multiprocessing.set_executable(pyexe)
    multiprocessing.set_start_method('spawn')

import jupyter_client
import time

print(jupyter_client.kernelspec.find_kernel_specs())
print(jupyter_client.kernelspec.get_kernel_spec('python3').to_dict())

km = jupyter_client.KernelManager(kernel_name='sjk-singular')

km.start_kernel()

print(km.is_alive())

kc = km.client()
kc.start_channels()

try:
    kc.wait_for_ready(timeout=60)
except RuntimeError:
    kc.stop_channels()
    km.shutdown_kernel()
    raise

print(kc.kernel_info())
print(kc.execute("1+2;"))

while True:
    try:
        msg = kc.get_iopub_msg(timeout=0.1)
    except:
        break
    print(msg['msg_type'])

print("here")
kc.stop_channels()
km.shutdown_kernel()
print("here")

