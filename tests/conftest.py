from typing import Any, Generator

import pytest
from faker import Faker
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import collect_list
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


@pytest.fixture(scope="session")
def spark_connect_start():
    kwargs = {
        "entrypoint": "/opt/spark/sbin/start-connect-server.sh org.apache.spark.deploy.master.Master --packages org.apache.spark:spark-connect_2.12:3.5.2,io.delta:delta-core_2.12:2.3.0 --conf spark.driver.extraJavaOptions='-Divy.cache.dir=/tmp -Divy.home=/tmp' --conf spark.connect.grpc.binding.port=8081",
    }
    with (
        DockerContainer(
            "apache/spark",
        )
        .with_bind_ports(8081, 8081)
        .with_env("SPARK_NO_DAEMONIZE", "True")
        .with_kwargs(**kwargs) as container
    ):
        _ = wait_for_logs(
            container, "SparkConnectServer: Spark Connect server started at"
        )
        yield container


@pytest.fixture(scope="session")
def spark_session(
    spark_connect_start: DockerContainer,
) -> Generator[SparkSession, Any, Any]:
    ip = spark_connect_start.get_container_host_ip()
    yield (
        SparkSession.builder.remote(f"sc://{ip}:8081")  # type: ignore
        .appName("Testing PySpark Example")
        .getOrCreate()
    )


@pytest.fixture(scope="session")
def persons(spark_session: SparkSession) -> Generator[DataFrame, Any, Any]:
    yield spark_session.createDataFrame(
        [
            (1, "George", "Washington", "1732-02-22"),
            (2, "Henry", "Ford", "1863-06-30"),
            (3, "Benjamin", "Franklin", "1706-01-17"),
            (4, "Martin", "Luther King Jr.", "1929-01-15"),
        ],
        ["id", "PersonalityName", "PersonalitySurname", "birth"],
    )


@pytest.fixture(scope="session")
def employments(spark_session: SparkSession) -> Generator[DataFrame, Any, Any]:
    yield spark_session.createDataFrame(
        [
            (1, 1, "president"),
            (2, 2, "industrialist"),
            (3, 3, "inventor"),
            (4, 4, "minister"),
        ],
        ["id", "person_fk", "Employment"],
    )


@pytest.fixture(scope="session")
def persons_synthetic(spark_session: SparkSession) -> Generator[DataFrame, Any, Any]:
    fake = Faker()
    nb_elem = 100_000
    data = [
        (i, fake.first_name(), fake.last_name(), fake.date()) for i in range(nb_elem)
    ]
    yield spark_session.createDataFrame(
        data,
        ["id", "PersonalityName", "PersonalitySurname", "birth"],
    )


@pytest.fixture(scope="session")
def employments_synthetic(
    spark_session: SparkSession, persons_synthetic: DataFrame
) -> Generator[DataFrame, Any, Any]:
    fake = Faker()
    persons_sample = persons_synthetic.sample(0.8)
    person_ids_sample = persons_sample.select(collect_list("id")).first()[0]

    data = [(idx, id_fk, fake.job()) for idx, id_fk in enumerate(person_ids_sample)]
    yield spark_session.createDataFrame(
        data,
        ["id", "person_fk", "Employment"],
    )
