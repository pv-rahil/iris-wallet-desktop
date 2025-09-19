import os
import tempfile
import stat
import shutil

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
        mount_path = "/tmp/fakeusb_mount"
        os.makedirs(mount_path, exist_ok=True)

        # Return environment override for subprocess
        env = os.environ.copy()
        env["PATH"] = f"{self.tmpdir}:" + env["PATH"]
        return env

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
