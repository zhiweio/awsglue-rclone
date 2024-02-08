import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from shlex import quote
from shutil import which
from subprocess import SubprocessError
from typing import Optional, List, Dict
from urllib.parse import urlparse

import redo
import requests
from requests.exceptions import SSLError, ReadTimeout

from awsglue_rclone.config import Config
from awsglue_rclone.utils import nio_execute_command, execute_command

__all__ = ["RClone"]

log = logging.getLogger("awsglue-rclone")

RCLONE = "rclone"
# latest: https://downloads.rclone.org/rclone-current-linux-amd64.zip
RCLONE_DOWNLOAD_URL = (
    "https://downloads.rclone.org/v1.65.2/rclone-v1.65.2-linux-amd64.zip"
)
LOCAL_BIN_PATH = "/tmp/opt/bin"
RCLONE_PATH = "/tmp/opt/bin/rclone"
RCLONE_CONFIG_PATH = "/tmp/opt/.config/rclone.conf"


class Installation:
    def __init__(
        self,
        name: str,
        url: str,
        binary_path=None,
    ):
        self.name = name
        self.url = url
        self._binary_path = binary_path

    @property
    def binary_path(self):
        return self._binary_path

    def installed(self) -> bool:
        """
        :return: True if rclone is correctly installed on the system.
        """
        if which(self.name) is not None:
            self._binary_path = self.name
            return True

        if self.exists(self.binary_path) and self.executable():
            return True

        self._binary_path = self._binary_path or os.path.join(LOCAL_BIN_PATH, self.name)
        return False

    def _uncompress(self, zip_pkg):
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(zip_pkg, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        pkg_path = Path(zip_pkg)
        pkg_name = pkg_path.name.replace(pkg_path.suffix, "")
        tmp_file = Path(temp_dir) / pkg_name / self.name
        shutil.move(tmp_file, self.binary_path)
        shutil.rmtree(temp_dir)

    def _download(self):
        temp_dir = tempfile.mkdtemp()
        pkg_name = os.path.basename(urlparse(self.url).path)
        pkg = Path(temp_dir) / pkg_name
        with requests.get(self.url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(pkg, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
        self._uncompress(pkg)
        shutil.rmtree(temp_dir)

    @staticmethod
    def exists(file_path) -> bool:
        _bin = Path(file_path)
        if _bin.exists() and _bin.is_file():
            return True
        return False

    def executable(self) -> bool:
        if not self.exists(self.binary_path):
            raise FileNotFoundError(f"Please download {self.name!r} firstly")
        return os.access(self.binary_path, os.X_OK)

    @redo.retriable(
        attempts=5,
        sleeptime=10,
        max_sleeptime=300,
        sleepscale=1,
        retry_exceptions=(ReadTimeout, SSLError),
    )
    def download(self):
        if self.exists(self.binary_path):
            return
        log.info(f"Installing {self.name} to {self.binary_path!r}")
        Path(self.binary_path).parent.mkdir(parents=True, exist_ok=True)
        if self.url.startswith("https://") and self.url.endswith(".zip"):
            try:
                self._download()
            except (SSLError, ReadTimeout) as e:
                log.warning(f"Download failed: {e}, retrying...")
                raise e
        else:
            raise ValueError(f"Invalid download url: {self.url}")

    def install(self):
        if self.installed():
            return
        log.info(f"Installing {self.name}")
        if not self.exists(self.binary_path):
            self.download()
        if not self.executable():
            os.chmod(self.binary_path, 0o755)


class RClone:
    def __init__(self, config_path=RCLONE_CONFIG_PATH):
        self._installation = Installation(
            name=RCLONE,
            url=RCLONE_DOWNLOAD_URL,
            binary_path=RCLONE_PATH,
        )
        self._installation.install()
        self._config_path = config_path

    @property
    def config_path(self):
        return self._config_path

    @property
    def binary_path(self):
        return self._installation.binary_path

    @property
    def installed(self):
        return self._installation.installed()

    def configured(self) -> bool:
        if Installation.exists(self.config_path):
            return True
        return False

    def create_remote(self, config: Config, append=False):
        rclone_conf = Path(self.config_path)
        if not self.configured():
            rclone_conf.parent.mkdir(parents=True, exist_ok=True)
            rclone_conf.write_text("")
            log.debug(f"rclone configured at {self.config_path}")

        if not append:
            rclone_conf.write_text("")

        exist_remote = rclone_conf.read_text(encoding="utf8")
        new_remote = config.create()
        remotes = f"{exist_remote}\n\n{new_remote}"
        log.debug(f"rclone config:")
        log.debug(remotes)

        rclone_conf.write_text(remotes)

    def execute(
        self,
        command,
        extra_args: List = None,
        debug=False,
        call_check=False,
        nio=False,
    ) -> Optional[Dict]:
        if not self.installed:
            raise OSError(
                f"Cannot execute command {self.binary_path}, please check installation"
            )
        if not self.configured():
            raise FileNotFoundError(f"Cannot found rclone config at {self.config_path}")

        cmd = [self.binary_path, f"--config={self.config_path}"]
        if debug:
            cmd.append("-vv")
        cmd += [command]
        cmd += list(extra_args or [])
        if nio:
            ret = nio_execute_command(cmd)
        else:
            ret = execute_command(cmd)

        if call_check and ret["code"] != 0:
            raise SubprocessError(f"Error executing command {cmd}: {ret}")
        return ret

    def sync(self, source: str, dest: str, flags: List = None, **kwargs):
        """rclone sync source:path dest:path [flags]"""
        return self.execute(
            "sync", extra_args=[quote(source), quote(dest)] + (flags or []), **kwargs
        )

    def copy(self, source: str, dest: str, flags: List = None, **kwargs):
        """rclone copy source:path dest:path [flags]"""
        return self.execute(
            "copy", extra_args=[quote(source), quote(dest)] + (flags or []), **kwargs
        )

    def ls(self, dest: str, flags: List = None, **kwargs):
        """rclone ls remote:path [flags]"""
        return self.execute("ls", extra_args=[quote(dest)] + (flags or []), **kwargs)

    def lsd(self, dest: str, flags: List = None, **kwargs):
        """rclone lsd remote:path [flags]"""
        return self.execute("lsd", extra_args=[quote(dest)] + (flags or []), **kwargs)

    def listremotes(self, dest: str, flags: List = None, **kwargs):
        """rclone listremotes [flags]"""
        return self.execute(
            "listremotes", extra_args=[quote(dest)] + (flags or []), **kwargs
        )

    def delete(self, dest: str, flags: List = None, **kwargs):
        """rclone delete remote:path [flags]"""
        return self.execute(
            "delete", extra_args=[quote(dest)] + (flags or []), **kwargs
        )
