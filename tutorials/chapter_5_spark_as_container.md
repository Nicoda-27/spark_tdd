# Chapter 5: Leverage spark in a container

In [chapter 3](chapter_3_spark_test.md), it was demonstrated that the current testing approach rely on *Java* being available on the developer setup. As mentioned, this is not ideal as there is limited control and unexpected behavior can happen. A good testing practice is to have reproducible and idempotent tests, this means:

- Launching the test an infinite number of times should always have the same results
- A test should leave a clean plate after it has run, there should be no side effect to a test running (no files written, no change of environment variables, no database with remaining data etc)

The reasons why it's so important, is because otherwise you will spend most of your time relaunching the tests due to false positive, you would never be sure if you actually broke something or if the test is randomly failing. At the end, you will not trust the tests anymore and skip some of them, which defeats the purpose.

## Why using a container?

If you are unfamiliar with the concept of containers and docker images, I suggest you have a look at [docker](https://www.docker.com/). It will be leveraged here to start the *Spark* server for the tests; it's important to mention there are other opensource alternatives like [podman](https://podman.io/) or [nerdctl](https://github.com/containerd/nerdctl) to allow containerization.

Docker will be used thereafter as it has become the defacto standards for most companies, and it's available in the *Github* ci runner. It will be assumed that you have enough knowledge about the technology to use it.

## Container with spark connect

There is a small subtlety that needs to be understood. Previously, the *Java Virtual Machine (JVM)* was used to communicate with the python spark implementation (through the `spark_session`), it was using the java binary to create a swarm of workers that were handling the data processing. At the end, all the results were collected and communicated to the `spark_session` which was exposing it in the python code.

If you start a container with this, the `spark_session` will never be able to find the *JVM* inside the container as it's a binary. The container you want to create needs a way to communicate outside with the `spark_session` through the network. Luckily, [*Spark* connect](https://spark.apache.org/docs/3.5.3/spark-connect-overview.html) is providing a solution and the documentation is a must known. This is the chosen approach to containerize the *Spark* server and the worker creation.

*Spark* is already providing a docker [image](https://hub.docker.com/r/apache/spark) that you will leverage. If you don't have docker available on your setup, you will need to install it, see the official [documentation](https://docs.docker.com/engine/install/ubuntu/#installation-methods).

Let's uninstall `openjdk` to make sure `spark_session` will use the new setup, it will require elevation of privileges:

```sh
apt-get autoremove openjdk-8-jre
```

You can now relaunch the tests, it's expected that they fail with the following error:

```txt
ERROR tests/test_minimal_transfo.py::test_minimal_transfo - pyspark.errors.exceptions.base.PySparkRuntimeError: [JAVA_GATEWAY_EXITED] Java gateway process exited before sending its port number.
ERROR tests/test_minimal_transfo.py::test_transfo_w_synthetic_data - pyspark.errors.exceptions.base.PySparkRuntimeError: [JAVA_GATEWAY_EXITED] Java gateway process exited before sending its port number.
```

## Start the container

You will need to start the container with spark connect, you can launch

```sh
docker run -p 8081:8081 -e SPARK_NO_DAEMONIZE=True --name spark_connect apache/spark /opt/spark/sbin/start-connect-server.sh org.apache.spark.deploy.master.Master --packages org.apache.spark:spark-connect_2.12:3.5.2,io.delta:delta-core_2.12:2.3.0 --conf spark.driver.extraJavaOptions='-Divy.cache.dir=/tmp -Divy.home=/tmp' --conf spark.connect.grpc.binding.port=8081
```

It will print a lot in the terminal and at the end you should have:

```txt
24/12/27 14:04:27 INFO SparkConnectServer: Spark Connect server started at: 0:0:0:0:0:0:0:0%0:8081
```

This shows that the *Spark* server is up and running.

Each argument in the above command has a meaning and its importance:

- `docker run` is the docker command to start a container
- `-p 8081:8081` is an arguments to `docker run` that enables to use port 8081 to communicate with the created container
- `-e SPARK_NO_DAEMONIZE=True` is an environment variable that is passed to the container creation, it's necessary to use it for the server to be created as a foreground process
- `--name spark_connect` allows to name the created container
- `apache/spark` is the docker image that is used, if you never used it, it will be downloaded from [*Docker Hub*](https://hub.docker.com/r/apache/spark)

The rest of the command is what is called an [entrypoint](https://docs.docker.com/reference/dockerfile/#entrypoint), it's the command that will be executed inside the container. In here it contains multiple elements:

- `/opt/spark/sbin/start-connect-server.sh` is the binary of the spark server
- `org.apache.spark.deploy.master.Master` is an argument to the binary, in here the binary is asked to deploy a Master server, the same binary can be used to deploy a Worker
- `--packages org.apache.spark:spark-connect_2.12:3.5.2,io.delta:delta-core_2.12:2.3.0` is an optional argument to pass specific versions of spark, and delta dependencies
- `--conf spark.driver.extraJavaOptions='-Divy.cache.dir=/tmp -Divy.home=/tmp'` is extra argument to ask the server to write to `/tmp` inside the container, it's not a mandatory argument
- `--conf spark.connect.grpc.binding.port=8081` is an extra argument to start the server on the port 8081 on the localhost of the container

The last argument is where the magic happens, the server is started on port 8081, and docker is exposing the port of this container to the port of the docker host. Meaning, a spark server is now available on `http://localhost:8081`

## Use the container

Keep the previous terminal opened to keep the server running and open a new terminal. Now run:

```sh
pytest -k test_transfo_w_synthetic_data -s
```

The same error should appear, indeed the `spark_session` needs to be adapted to connect to the server you have just created. In [`test/conftest.py`](../tests/conftest.py):

```python
@pytest.fixture(scope="session")
def spark_session() -> Generator[SparkSession, Any, Any]:
    yield (
        SparkSession.builder.remote("sc://localhost:8081")  # type: ignore
        .appName("Testing PySpark Example")
        .getOrCreate()
    )
```

Basically, it indicates the *Spark* connect server *url* to the *Spark* session.

And you need to add an extra dependency, which is mandatory to communicate with the spark connect server. It's worth pointing to the usage of [extras](https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies) in uv:

```sh
uv add pyspark --extra connect
```

As this project is in *Python* 3.12, another error will appear related to [distutils](https://stackoverflow.com/questions/69919970/no-module-named-distutils-util-but-distutils-installed/76691103#76691103) as it was removed from the latest python version, yet some dependencies still requires it. You will have to add:

```sh
uv add setuptools
```

Now you can run:

```sh
pytest -k test_minimal_transfo -s
```

And it should run successfully, you should also see logs in the spark server in the docker run terminal.

## Improve the container usage

As mentioned at the beginning of this chapter, the tests need to leave a clean plate. In the previous approach, a container is still running eventhough the tests are done, it's not ideal.

To improve this, you will leverage [testcontainers](https://github.com/testcontainers/testcontainers-python) which empower you with easy docker creation and removal at the test level.

```sh
uv add testcontainers --dev
```

Now, the docker can be started at the session fixture level, in [`tests/conftest.py`](../tests/conftest.py), you can add an extra fixture:

```python
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
```

This will create a container with the previously described argument, the great thing with fixtures is that will kill the container at the end of the test execution. There is an extra step with:

```python
        _ = wait_for_logs(
            container, "SparkConnectServer: Spark Connect server started at"
        )
```

This enforces to yield the container only when the `SparkConnectServer: Spark Connect server started at` appeared in the container logs. It's necessary to wait for the server to be ready until it can be called.

The value that is yielded is the container which also contains the server url, you need to reuse in the `spark_session` fixture:

```python
@pytest.fixture(scope="session")
def spark_session(spark_connect_start: DockerContainer) -> Generator[SparkSession, Any, Any]:
    ip = spark_connect_start.get_container_host_ip()
    yield (
        SparkSession.builder.remote(f"sc://{ip}:8081")  # type: ignore
        .appName("Testing PySpark Example")
        .getOrCreate()
    )
```

You can now stop the container you started before

```sh
docker stop spark_connect
```

And run the tests:

```sh
pytest
```

You will notice all the tests are passing, and at the end of the test session there is no running containers.

The following command will show what remaining containers are still running. The spark container should not appear.

```sh
docker ps -a 
```

## Conclusion

You are now able to run local tests using spark and you can quickly iterate on your codebase and implement new features. You are no more depending on spark server to be launched for you on the cloud and waiting for it to process the data for you.

The feedback loop is quicker, you are no more giving money to cloud provider for testing purposes and you provide an easy setup for developers to iterate on your project.

They can launch `pytest` and will be transparent; this also means less documentation for you to write to describe the expected developer setup.
