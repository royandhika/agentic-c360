import json

import paramiko
import psycopg2
import requests
import s3fs
from dagster import ConfigurableResource, EnvVar


class PostgresResource(ConfigurableResource):
    host: str = EnvVar("POSTGRES_APP_HOST")
    port: int = EnvVar.int("POSTGRES_APP_PORT")
    user: str = EnvVar("POSTGRES_APP_USER")
    password: str = EnvVar("POSTGRES_APP_PASS")
    dbname: str = EnvVar("POSTGRES_APP_DB")

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
        )


class MinIOResource(ConfigurableResource):
    endpoint: str = EnvVar("MINIO_ENDPOINT")
    bucket: str = EnvVar("MINIO_BUCKET")
    access_key: str = EnvVar("MINIO_ACCESS_KEY")
    secret_key: str = EnvVar("MINIO_SECRET_KEY")

    def get_s3(self) -> s3fs.S3FileSystem:
        return s3fs.S3FileSystem(
            key=self.access_key,
            secret=self.secret_key,
            client_kwargs={"endpoint_url": f"http://{self.endpoint}"},
        )


class VendorApiResource(ConfigurableResource):
    base_url: str = EnvVar("VENDOR_API_URL")

    def get(self, endpoint: str, params: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        resp = requests.get(url, params=params, timeout=120)
        resp.raise_for_status()
        return resp.json()


class SFTPSourceResource(ConfigurableResource):
    host: str = EnvVar("CRM_SFTP_HOST")
    port: int = EnvVar.int("CRM_SFTP_PORT")
    username: str = EnvVar("CRM_SFTP_USER")
    password: str = EnvVar("CRM_SFTP_PASS")
    remote_dir: str = EnvVar("CRM_SFTP_PATH")

    def read_json(self, filename: str) -> list[dict]:
        tpt = paramiko.Transport((self.host, self.port))
        tpt.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(tpt)
        try:
            sftp.chdir(self.remote_dir)
            with sftp.file(filename, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        finally:
            sftp.close()
            tpt.close()
        return data
