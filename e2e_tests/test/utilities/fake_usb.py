"""
Fake USB module.
"""
from __future__ import annotations

import os
import shutil
import stat
import tempfile

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


def setup_fake_usb() -> tuple[dict[str, str], str]:
    """Create fake lsblk and mount directory."""
    tmpdir = tempfile.mkdtemp(prefix='fakeusb_')
    fake_lsblk_path = os.path.join(tmpdir, 'lsblk')

    with open(fake_lsblk_path, 'w', encoding='utf-8') as f:
        f.write('#!/bin/sh\n')
        f.write(
            "echo '%s'\n" %
            FAKE_LSBLK_OUTPUT.strip().replace("'", "'\\''"),
        )

    st = os.stat(fake_lsblk_path)
    os.chmod(fake_lsblk_path, st.st_mode | stat.S_IEXEC)

    # Ensure a fixed shared mount path for both app instances
    os.makedirs(FAKEUSB_MOUNT_PATH, exist_ok=True)

    # Return environment override for subprocess
    env = os.environ.copy()
    env['PATH'] = f"{tmpdir}:" + env['PATH']
    return env, tmpdir


def cleanup_fake_usb(tmpdir: str):
    """Remove the fake USB environment."""
    shutil.rmtree(tmpdir, ignore_errors=True)


def clear_fake_usb_mount_all() -> None:
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
