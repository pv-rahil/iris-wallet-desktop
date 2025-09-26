import os
import tempfile
import stat
import shutil

from accessible_constant import FAKEUSB_MOUNT_PATH

FAKE_LSBLK_OUTPUT = r"""
{
  "blockdevices": [
    {
      "name": "sdb",
      "tran": "usb",
      "children": [
        {
          "name": "sdb1",
          "mountpoint": "/tmp/fakeusb_mount",
          "label": "FAKE_USB"
        }
      ]
    }
  ]
}
"""

class FakeUSB:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="fakeusb_")

    def setup(self):
        """Create fake lsblk and mount directory."""
        fake_lsblk_path = os.path.join(self.tmpdir, "lsblk")

        with open(fake_lsblk_path, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("echo '%s'\n" % FAKE_LSBLK_OUTPUT.strip().replace("'", "'\\''"))

        st = os.stat(fake_lsblk_path)
        os.chmod(fake_lsblk_path, st.st_mode | stat.S_IEXEC)

        # Ensure a fixed shared mount path for both app instances
        os.makedirs(FAKEUSB_MOUNT_PATH, exist_ok=True)

        # Return environment override for subprocess
        env = os.environ.copy()
        env["PATH"] = f"{self.tmpdir}:" + env["PATH"]
        return env

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


def clear_fake_usb_mount_all():
    """
    Remove all files from the fake USB mount directory (shared between instances).
    """
    try:
        if os.path.isdir(FAKEUSB_MOUNT_PATH):
            for name in os.listdir(FAKEUSB_MOUNT_PATH):
                path = os.path.join(FAKEUSB_MOUNT_PATH, name)
                try:
                    if os.path.isfile(path) or os.path.islink(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass
