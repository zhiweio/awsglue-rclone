import logging
import textwrap
from typing import Dict

from awsglue_rclone.utils import get_secret

log = logging.getLogger("awsglue-rclone-config")


class RemoteTypes:
    """These are all the cloud systems support by rclone (generated with v1.65.2).
    A more detailed overview can be found here: https://rclone.org/overview/
    """

    amazon_cloud_drive = "amazon cloud drive"
    azureblob = "azureblob"
    azurefiles = "azurefiles"
    b2 = "b2"
    box = "box"
    cache = "cache"
    chunker = "chunker"
    combine = "combine"
    compress = "compress"
    crypt = "crypt"
    drive = "drive"
    dropbox = "dropbox"
    fichier = "fichier"
    filefabric = "filefabric"
    ftp = "ftp"
    google_cloud_storage = "google cloud storage"
    google_photos = "google photos"
    hasher = "hasher"
    hdfs = "hdfs"
    hidrive = "hidrive"
    http = "http"
    imagekit = "imagekit"
    internetarchive = "internetarchive"
    jottacloud = "jottacloud"
    koofr = "koofr"
    linkbox = "linkbox"
    local = "local"
    mailru = "mailru"
    mega = "mega"
    memory = "memory"
    netstorage = "netstorage"
    onedrive = "onedrive"
    opendrive = "opendrive"
    oracleobjectstorage = "oracleobjectstorage"
    pcloud = "pcloud"
    pikpak = "pikpak"
    premiumizeme = "premiumizeme"
    protondrive = "protondrive"
    putio = "putio"
    qingstor = "qingstor"
    quatrix = "quatrix"
    s3 = "s3"
    seafile = "seafile"
    sftp = "sftp"
    sharefile = "sharefile"
    sia = "sia"
    smb = "smb"
    storj = "storj"
    sugarsync = "sugarsync"
    swift = "swift"
    tardigrade = "tardigrade"
    union = "union"
    uptobox = "uptobox"
    webdav = "webdav"
    yandex = "yandex"
    zoho = "zoho"


class Config:
    def __init__(
        self,
        alias: str,
        properties: Dict = None,
        secret: str = None,
    ):
        self.alias = alias
        self.properties = properties
        if secret:
            self.properties = get_secret(secret)
        if not self.properties:
            raise ValueError("No remote properties provided")

    def create(self):
        raise NotImplemented("Please implement this method")


class LocalConfig(Config):
    def create(self):
        return textwrap.dedent(
            f"""
[{self.alias}]
type = {RemoteTypes.local}
nounc = true
        """
        )


class SFTPConfig(Config):
    def create(self):
        return textwrap.dedent(
            f"""
[{self.alias}]
type = {RemoteTypes.sftp}
host = {self.properties["host"]}
user = {self.properties["user"]}
port = {self.properties["port"]}
pass = {self.properties["pass"]}
md5sum_command = none
sha1sum_command = none
        """
        )


class S3Config(Config):
    def create(self):
        region = self.properties["region"]
        location_constraint = self.properties.get("location_constraint", region)
        return textwrap.dedent(
            f"""
[{self.alias}]
type = {RemoteTypes.s3}
provider = AWS
env_auth = true
access_key_id = {self.properties["access_key_id"]}
secret_access_key = {self.properties["secret_access_key "]}
region = {region}
location_constraint = {location_constraint}
        """
        )
