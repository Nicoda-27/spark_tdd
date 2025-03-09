import pytest
from pyspark.sql import DataFrame

from pyspark_tdd.data_processor import DataProcessor


def test_minimal_transfo(spark_session, persons: DataFrame, employments: DataFrame):
    processor = DataProcessor(spark_session)
    df_out: DataFrame = processor.run(persons, employments)

    assert not df_out.isEmpty()
    assert set(df_out.columns) == set(
        ["name", "surname", "date_of_birth", "employment"]
    )


@pytest.mark.slow
def test_transfo_w_synthetic_data(
    persons_synthetic: DataFrame, employments_synthetic: DataFrame, spark_session
):
    processor = DataProcessor(spark_session)
    df_out: DataFrame = processor.run(persons_synthetic, employments_synthetic)

    assert not df_out.isEmpty()
    assert set(df_out.columns) == set(
        ["name", "surname", "date_of_birth", "employment"]
    )
