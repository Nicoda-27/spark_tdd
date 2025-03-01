# Chapter 3: Implement a first test with *spark*

This chapter will focus on implementing a first *spark* data manipulation with an associated test. It will go through the issues that will be encountered and how to solve them.

## The data

A dummy use case is used to demonstrate the workflow.

The scenario is that production data is made of two tables `persons` and `employments` with the following schema and data types. Here is a sample of the data.

### Persons

| id: int | PersonalityName: str      | PersonalitySurname: str | birth: datetime(str)
|---| ----------- | ----------- | ---
|1| George      | Washington       | 1732-02-22
|2| Henry   | Ford        | 1863-06-30
|3| Benjamin   | Franklin        |1706-01-17
|4| Martin   | Luther King Jr.        | 1929-01-15

### Employments

| id: int | person_fk: int | Employment
|---| ----------- | -----------
|1| 1| president
|2| 2| industrialist
|3| 3| inventor
|4| 4| minister

The goal is to change the names of the columns and to join the data. The data here is just a sample, it's overkill to use *spark* to process data like this. Yet, in a big data context, you need to foresee that the data will contains more lines and more complex joins. The sample is just here as a demonstration.

## The dummy test

First, you need to add spark dependencies

```sh
uv add pyspark
```

Before diving into the implementation, you need to make sure you can reproduce a very simple use case. It's not worth diving into complex data manipulation if you are not able to reproduce simple documentation snippet.

You will write your first test [`test_minimal_transfo.py`](../tests/test_minimal_transfo.py). You will try first to use *pyspark* to do simple data frame creation.

```python
from pyspark.sql import SparkSession


def test_minimal_transfo():
    spark: SparkSession = (
        SparkSession.builder.master("local")
        .appName("Testing PySpark Example")
        .getOrCreate()
    )

    df = spark.createDataFrame([(3, 4), (1, 2)], ["col1", "col2"])
    df.show()
```

The first part with the session create or fetch a local *spark* session, the second part leverages the session to create a data frame.

Then you can launch:

```sh
pytest -k test_minimal_transfo -s
```

If you have a minimal developer setup, it should not work because it's trying to use *Java* which you might be missing and the following error will be displayed:

```txt
FAILED tests/test_minimal_transfo.py::test_minimal_transfo - pyspark.errors.exceptions.base.PySparkRuntimeError: [JAVA_GATEWAY_EXITED] Java gateway process exited before sending its port number
```

It's a bit annoying, because you need to have *Java* installed on our *dev* setup, the ci setup and all your collaborators setup. On the future chapters, a better alternative will be described.

There are different flavors of *Java*, you can simply install the [*openjdk*](https://openjdk.org/) one. It will require elevation of privileges:

```sh
apt-get install openjdk-8-jre
```

You can now relaunch:

```sh
pytest -k test_minimal_transfo -s
```

and it should display

```txt
+----+----+                                                                     
|col1|col2|
+----+----+
|   3|   4|
|   1|   2|
+----+----+
```

This is a small victory, but you can now use a local *spark* session to manage data frames, yay !

## The real test case - version 0

On the previous sample, it shows that the `spark session` plays a pivotal role, it will be instantiated differently in the tests context than in the production context.

This means we can leverage a *pytest* fixture to be reused for all tests later on; it can be created at the session level so there is only one spark session for the whole test suite. Meaning, you can create a [`tests/conftest.py`](../tests/conftest.py) to factorize common behavior. If you are not familiar with pytest and fixtures, it's advised to have a look at [documentation](https://docs.pytest.org/en/6.2.x/fixture.html).

In [`tests/conftest.py`](../tests/conftest.py):

```python
from typing import Any, Generator

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark_session() -> Generator[SparkSession, Any, Any]:
    yield (
        SparkSession.builder.master("local")
        .appName("Testing PySpark Example")
        .getOrCreate()
    )
```

Then, it can be reused in [`tests/test_minimal_transo.py`](../tests/test_minimal_transfo.py):

```python
from pyspark.sql import SparkSession

def test_minimal_transfo(spark_session: SparkSession):

    df = spark_session.createDataFrame([(3, 4), (1, 2)], ["col1", "col2"])
    df.show()
```

You can again run `pytest -k test_minimal_transfo -s` to check the behavior has not changed. It's important in a test driven approach to keep launching the tests after code modification to ensure nothing was broken.

To be closer to the business context, you can implement a data transformation object. There will be a clear separation between data generation and data transformation. You can do so in [`src/data_transform.py`](../src/pyspark_tdd/data_processor.py)

```python
from pyspark.sql import DataFrame, SparkSession


class DataProcessor:
    def __init__(self, spark_session: SparkSession):
        self.spark_session = spark_session

    def run(self, persons: DataFrame, employments: DataFrame) -> DataFrame:
        raise NotImplementedError
```

Now, there is a prototype for `DataProcessor`, the tests can be improved to actually assert on elements like so in [`test_minimal_transfo.py`](../tests/test_minimal_transfo.py)

```python
from pyspark.sql import DataFrame, SparkSession

from pyspark_tdd.data_processor import DataProcessor


def test_minimal_transfo(spark_session: SparkSession):
    persons = spark_session.createDataFrame(
        [
            (1, "George", "Washington", "1732-02-22"),
            (2, "Henry", "Ford", "1863-06-30"),
            (3, "Benjamin", "Franklin", "1706-01-17"),
            (4, "Martin", "Luther King Jr.", "1929-01-15"),
        ],
        ["id", "PersonalityName", "PersonalitySurname", "birth"],
    )
    employments = spark_session.createDataFrame(
        [
            (1, 1, "president"),
            (2, 2, "industrialist"),
            (3, 3, "inventor"),
            (4, 4, "minister"),
        ],
        ["id", "person_fk", "Employment"],
    )
    processor = DataProcessor(spark_session)
    df_out: DataFrame = processor.run(persons, employments)
    
    assert not df_out.isEmpty()
    assert set(df_out.columns) == set(
        ["name", "surname", "date_of_birth", "employment"]
    )

```

The example above will ensure that the data frame fits some criteria, but it will raise an `NotImplementedError` as you have to implement the actual data processing. It's intended, the actual processing code can be created after testing is properly setup.

The actual test is still not ideal as test case generation is part of the test itself. *Pytest* [parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html) can be leveraged:

```python
import pytest 

from pyspark.sql import SparkSession

@pytest.mark.parametrize(
    "persons,employments",
    [
        (
            (
                [
                    (1, "George", "Washington", "1732-02-22"),
                    (2, "Henry", "Ford", "1863-06-30"),
                    (3, "Benjamin", "Franklin", "1706-01-17"),
                    (4, "Martin", "Luther King Jr.", "1929-01-15"),
                ],
                ["id", "PersonalityName", "PersonalitySurname", "birth"],
            ),
            (
                [
                    (1, 1, "president"),
                    (2, 2, "industrialist"),
                    (3, 3, "inventor"),
                    (4, 4, "minister"),
                ],
                ["id", "person_fk", "Employment"],
            ),
        )
    ],
)
def test_minimal_transfo(spark_session: SparkSession, persons, employments):
    persons = spark_session.createDataFrame(*persons)
    employments = spark_session.createDataFrame(*employments)

    processor = DataProcessor(spark_session)
    df_out: DataFrame = processor.run(persons, employments)

    assert not df_out.isEmpty()
    assert set(df_out.columns) == set(
        ["name", "surname", "date_of_birth", "employment"]
    )
```

The above example show how test cases generation can be separated from test runs. It allows to see at first glance what this test is about without noise about test data. Most likely, the test data frames could be reused in another test, it needs to be refactored again. The test part becomes:

```python
from pyspark.sql import DataFrame, SparkSession

from pyspark_tdd.data_processor import DataProcessor


def test_minimal_transfo(spark_session: SparkSession, persons: DataFrame, employments: DataFrame):
    processor = DataProcessor(spark_session)
    df_out: DataFrame = processor.run(persons, employments)

    assert not df_out.isEmpty()
    assert set(df_out.columns) == set(
        ["name", "surname", "date_of_birth", "employment"]
    )
```

and two fixtures `persons` and `employments` are created in [`tests/conftest.py`](../tests/conftest.py):

```python
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

```

You can now relaunch `pytest -k test_minimal_transfo -s` and notice the `NotImplementedError` being raised; which is a good thing. The code has changed 3 times, yet the behavior remains the same, and the tests confirm it.

## The real test case - version 1

Now that there is a proper testing in place, source code can be implemented. There could be variations of this, the intent here is not to provide the best source code, but the best way to test:

```python
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

        employments = employments.withColumnRenamed(colsMap=self.employments_rename)
        joined = persons.join(
            employments, persons.id == employments.person_fk, how="left"
        )
        joined = joined.drop("id", "person_fk")
        return joined
```

If you rerun `pytest -k test_minimal_transfo -s`, then the test is successful.

## What about ci?

A strong dependency to *Java* is now in place, running the tests in ci will depend on the ci having *Java* installed or not. This is an issue because it requires the developer to have a defined *dev* setup outside of the python ecosystem, there are extra steps for anyone to launch the tests.

Keep in mind, there is limited control over the developer setup, what if the *Java* already installed in the developer setup is not spark compliant? It will then be frustrating for the developer to investigate and most likely reinstall another *Java* version which might impact other projects. See the mess

Luckily, the ci runner on *Github* has *Java* installed for us; so the ci should run.

## Clean up

You can now also clean up the repository to have a clean plate. For instance, `src/pyspark_tdd/multiply.py` and `tests/test_dummy.py` can be removed.

## What's next

Now, you have a comfortable setup to modify and tweak the code. You can run the tests and be sure to reproduce.

In the next chapter, a more data driven approach to test case generation will be explored.
