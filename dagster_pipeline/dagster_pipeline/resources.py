import s3fs
import psycopg2
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
