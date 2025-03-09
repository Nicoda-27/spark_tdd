from typing import Any, Generator

import pytest
from faker import Faker
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import collect_list


@pytest.fixture(scope="session")
def spark_session() -> Generator[SparkSession, Any, Any]:
    yield (
        SparkSession.builder.master("local")
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
