# awsglue-rclone

awsglue-rclone is a wrapper for RClone designed for use with AWS Glue Python Shell, rclone everything within Glue!

## Installation

Install awsglue-rclone from source:

```shell
$ git clone https://github.com/zhiweio/awsglue-rclone.git && cd awsglue-rclone/
$ python3 setup.py install
```


## Usage

Install `rclone` on local machine (Glue shell)

```python
from awsglue_rclone import RClone

rclone = RClone()

```

Build AWS S3 remote config

```python
from awsglue_rclone.config import S3Config

cn_s3_conf = S3Config(
    alias="cn",
    properties={
        "region": "cn-north-1",
        "access_key_id": "xxx",
        "secret_access_key": "xxx",
    },
)
```

Create `rclone.config` file

```python
rclone.create_remote(cn_s3_conf)
```

Build from Secrets Manager

secrets: `rclone/aws_s3/us_west`
```json
{
    "region": "us-west-1",
    "access_key_id": "xxx",
    "secret_access_key": "xxx",
}
```

```python
us_s3_conf = S3Config(
    alias="us",
    secret="rclone/aws_s3/us_west",
)
rclone.create_remote(us_s3_conf, append=True)
```

List remote files

```python
ret = rclone.ls("cn:bucket/yourfolder")

{
    "code": 0,
    "out": "     2079 README.md\n",
    "error": ""
}
```

Print verbose

```python
ret = rclone.ls("cn:bucket/yourfolder", debug=True)

{
    "code": 0,
    "out": "     2079 README.md\n",
    "error": "2024/02/08 17:00:09 DEBUG : rclone: Version \"v1.64.2\" starting with parameters [\"rclone\" \"--config=/tmp/opt/.config/rclone.conf\" \"-vv\" \"ls\" \"cn:bucket/yourfolder/\"]\n2024/02/08 17:00:09 DEBUG : Creating backend with remote \"cn:bucket/yourfolder/\"\n2024/02/08 17:00:09 DEBUG : Using config file from \"/tmp/opt/.config/rclone.conf\"\n2024/02/08 17:00:09 DEBUG : fs cache: renaming cache item \"cn:bucket/yourfolder/\" to be canonical \"cn:bucket/yourfolder\"\n2024/02/08 17:00:09 DEBUG : 7 go routines active\n"
}
```

Copy files between two remotes, set `nio=True` to save command output (stdout/stderr) into temporary files
```python
rclone.copy("cn:bucket/yourfolder", "us:bucket/yourfolder", nio=True)

{
    "code": 0,
    "out": "/var/folders/bj/h5g9fnl93dg6tllvsp4hr73r0000gn/T/tmpuhom0swf.stdout",
    "error": "/var/folders/bj/h5g9fnl93dg6tllvsp4hr73r0000gn/T/tmp4jf_9nok.stderr"
}
```

Build other remote Config providers

```python
from awsglue_rclone.config import Config, RemoteTypes

# provider for onedrive storage
class OneDriveConfig(Config):
    def create(self):
        token = {
            "access_token": self.properties["access_token"],
            "token_type": self.properties.get("token_type", "Bear"),
            "refresh_token": self.properties["refresh_token"],
            "expiry": "2018-08-26T22:39:52.486512262+08:00",
        }
        token = json.dumps(token)
        drive_id = self.properties["drive_id"]
        drive_type = "business"
        return textwrap.dedent(
            f"""
[{self.alias}]
type = {RemoteTypes.onedrive}
token = {token}
drive_id = {drive_id}
drive_type = {drive_type}
        """
        )
```

## Authors

- [@zhiweio](https://www.github.com/zhiweio)


## License

[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)

