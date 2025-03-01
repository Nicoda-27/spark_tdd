from typing import Any, Generator

import pytest
from pyspark.sql import DataFrame, SparkSession


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
