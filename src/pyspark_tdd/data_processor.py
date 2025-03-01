from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import to_date


class DataProcessor:
    def __init__(self, spark_session: SparkSession):
        self.spark_session = spark_session
        self.persons_rename = {
            "PersonalityName": "name",
            "PersonalitySurname": "surname",
            "birth": "date_of_birth",
        }
        self.employments_rename = {"Employment": "employment"}

    def run(self, persons: DataFrame, employments: DataFrame) -> DataFrame:
        persons = persons.withColumn(
            "birth", to_date(persons.birth)
        ).withColumnsRenamed(colsMap=self.persons_rename)

        employments = employments.withColumnsRenamed(colsMap=self.employments_rename)
        joined = persons.join(
            employments, persons.id == employments.person_fk, how="left"
        )
        joined = joined.drop("id", "person_fk")
        return joined
