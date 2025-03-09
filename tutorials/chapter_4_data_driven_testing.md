# Chapter 4: Property based testing

The test that you implemented in [Chapter 3](chapter_3_spark_test.md) is great, yet not complete as it takes only a limited amount of data. As spark is used to process data at scale, you have to test at scale too.

There are several solutions, the first one being taking a snapshot of production data and reusing at the test level (meaning integration test or local test). The second one is to generate synthetic data based on the data schema. With the second approach, you will be leaning into a property based testing approach.

The second approach will be leveraged here as the test case generation is deported to automated generation.

The python ecosystem provides [*Hypothesis*](https://hypothesis.readthedocs.io/en/latest/) for proper property based testing, or [*Faker*](https://faker.readthedocs.io/en/master/) for fake data generation. *Hypothesis* is way more powerful than Faker in the sense that it will generate test cases for you based on data property (being a string, being an integer etc) and shrink the test cases when unexpected behavior happen. *Faker* will be used here to generate synthetic data based on business property.

## A data driven test

You need two new fixtures similar to `persons` and `employments` that will generate synthetic data. First you need to install faker as a dev dependency:

```sh
uv add faker --dev
```

You can create `persons_synthetic` in [`tests/conftest.py`](../tests/conftest.py) like so:

```python
@pytest.fixture(scope="session")
def persons_synthetic(spark_session: SparkSession) -> Generator[DataFrame, Any, Any]:
    fake = Faker()

    nb_elem = fake.pyint(1, 100_000)
    data = [
        (i, fake.first_name(), fake.last_name(), fake.date()) for i in range(nb_elem)
    ]
    yield spark_session.createDataFrame(
        data,
        ["id", "PersonalityName", "PersonalitySurname", "birth"],
    )
```

In the above, a data frame of 100 000 rows is generated, feel free to increase the size to generate larger data frames. Fake names, surnames and date are generated on the fly according to business needs.

You can also create `employments_synthetic` in [`tests/conftest.py`](../tests/conftest.py), there is a dependency on `foreign_key` from `persons_synthetic` that needs to be handled:

```python
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
```

The `foreign_key` is reused from a sample of `persons_synthetic` and job name are generated on the fly.

The test can now be created:

```python
def test_transfo_w_synthetic_data(
    persons_synthetic: DataFrame, employments_synthetic: DataFrame, spark_session
):
    processor = DataProcessor(spark_session)
    df_out: DataFrame = processor.run(persons_synthetic, employments_synthetic)

    assert not df_out.isEmpty()
    assert set(df_out.columns) == set(
        ["name", "surname", "date_of_birth", "employment"]
    )
```

And you can launch `pytest -k test_transfo_w_synthetic_data -s` that should pass.

## How to handle slow tests

You might notice that `test_transfo_w_synthetic_data` is a bit slow, indeed it's generating a decent amount of data (even though far from a big data scale), modifying the data frames and joining two together.

In a test driven approach, it's necessary to have a quick feedback loop to iterate quickly on your local setup. Yet, this tests needs to be launched anyway as they validate behavior with decent amount of data.

A solution is to add tags to tests like so:

```python
import pytest
...

@pytest.mark.slow
def test_transfo_w_synthetic_data(
    persons_synthetic: DataFrame, employments_synthetic: DataFrame, spark_session
):
...
```

This tag can be leveraged by pytest to filter out tests at execution time, see [documentation](https://docs.pytest.org/en/stable/example/markers.html#mark-examples).

and add to [`pyproject.toml`](../pyproject.toml) the expected markers for *Pytest*

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
markers = ["slow"]
```

*Pytest* is now aware of this new marker when launching:

```sh
pytest --markers
```

You can now launch:

```sh
pytest -m "not slow"
```

It will validate only the tests not marked as slow.

In the ci, there is nothing to change as by default *Pytest* will launch all the test.

## What's next?

You now have testing at a decent data scale using proper testing framework. The next chapter will focus on test repeatability by improving how java is used for *Spark* at the test level.
