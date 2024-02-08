import base64
import json
import logging
import sys
import tempfile
from subprocess import Popen, PIPE
from typing import List, Dict

import boto3

log = logging.getLogger("awsglue-rclone")

IS_WIN32 = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"


def execute_command(cmd: List[str]) -> Dict:
    proc = Popen(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
        encoding="utf-8",
        errors="utf-8",
    )
    log.debug(f"command: {cmd}, pid: {proc.pid}")
    (out, err) = proc.communicate()
    log.debug(out)
    if err:
        log.warning(err)
    return {"code": proc.returncode, "out": out, "error": err}


def nio_execute_command(cmd: List[str]) -> Dict:
    """Avoid large outputs deadlocking program
    ref: https://thraxil.org/users/anders/posts/2008/03/13/Subprocess-Hanging-PIPE-is-your-enemy/
    """
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".stdout"
    ) as out_f, tempfile.NamedTemporaryFile(delete=False, suffix=".stderr") as err_f:
        proc = Popen(cmd, stdout=out_f, stderr=err_f)
        log.debug(f"command: {cmd}, pid: {proc.pid}")
        code = proc.wait()
        err_f.seek(0)
        for line in err_f:
            log.warning(line.decode("utf8"))
    return {"code": code, "out": out_f.name, "error": err_f.name}


_secrets_client = boto3.client("secretsmanager")


def get_secret(secret_name):
    res = _secrets_client.get_secret_value(SecretId=secret_name)
    if "SecretString" in res:
        secret = res["SecretString"]
    else:
        secret = base64.b64decode(res["SecretBinary"])
    return json.loads(secret)
