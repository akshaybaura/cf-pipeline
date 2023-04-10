# Solution to Assignment

## Sections
1. [TL;DR version](#tldr)  
2. [Details](#details)  
3. [Replication steps](#replication)

## TL;DR version

![High Level architecture](/taxi-1/images/architecture.jpeg)

This project involves building a data engineering pipeline to extract, validate, and transform data from the Chicago Taxi Trips dataset available on the City of Chicago's open data portal. The pipeline is built using asyncio and pydantic to efficiently process and validate the data, followed by streaming the data to a Kafka topic and ultimately dumping it into a PostgreSQL database using a JDBC sink.

Once the data is in the database, it is transformed using dbt to create a dimensional model alongwith a non-relational model that enables efficient querying and analysis of the data. Finally, the data is exposed through APIs built on FastAPI, allowing for easy integration with other applications.

## Details

The data pipeline follows these main steps:  

**Async Calls to API**: The data pipeline makes async calls to an API endpoint to fetch data. This is done using the aiohttp library which provides a simple interface to perform asynchronous HTTP requests. I used asyncio to handle the async calls, which allows us to make multiple requests in parallel.
Since the API is rate limited quite strictly compared to the data it hosts, I went about approaching this in a relaxed way as follows:  
1. Divide the records in chunks of 10000 which comprises 1 page.
2. In one async call, request for 5 pages asynchronously.
3. Streaming downwards is synchronous to reduce complexity for the current context.

**Validation and Schema Compliance**: Once I have the data, I validate and convert the data types using Pydantic in compliance with the avsc file which is representative of the schema in Schema Regsitry for the downstream kafka topic. Pydantic helps ensure that the data we're working with is in the correct format and structure. This step is important to prevent issues downstream in our pipeline caused by incorrect or missing data.

**Publishing to Kafka**: Once the data is fetched from the API, it is serialized to Avro format and published to a Kafka topic using the confluent-kafka library. The Kafka topic acts as a buffer for the data and ensures that the data is delivered reliably and efficiently to downstream systems. It helps with decoupling the API data pull and database feed. Avro serialisation helps with lesser network bandwidth consumption and support for schema evolution. The kafka setup I have used is modelled after confluent kafka's docker setup.   

**Inserting into PostgreSQL**: The data is then inserted into a PostgreSQL table using a JDBC sink connector for kafka. The JDBC connector allows us to easily connect to the PostgreSQL database and insert data efficiently and reliably. It allows for a lot of customizations such as auto create, auto evolve, insert mode, deserialisation etc.  

**Data Transformation using DBT**: Once the data is in PostgreSQL, I transform it using DBT. DBT is used to transform data in SQL and apply best practices for data modeling. By using DBT, I created a dimensional model that is optimized for reporting and analytics. I also create a NoSQL model to have the data in json format referenced by the corresponding trip_id. The model creation is incremental in nature.  
I also put in unit tests for different models and source transaction table, and the relationships between them.  

**API Development using FastAPI**: Finally, I expose the data using APIs built on FastAPI. I created 2 APIs:  
1. data/*format*: to download the transactional dataset in csv or json format.  
2. custom_query/*format*/*query-string*: to display/download data queried in sql syntax from models or transactional table.  

**Error Handling and Logging**: The data pipeline includes error handling and logging to ensure that any errors or issues are logged and can be addressed. If an error occurs during the pipeline execution, it is logged with detailed information to help with debugging and troubleshooting.

## Replication

1. Run `docker-compose up -d`.
This step might take a few minutes based on the network speed since the confluent images are bulky.  
2. When done, run: `docker-compose ps` to check the state of the containers. Ideally it should look like this:  
![docker-compose-ps](/taxi-1/images/docker-compose-ps-op.png)  
If any containers exit, feel free to fire `docker-compose up -d` again.  

-------------------**Requisites**--------------------------------------  
There is a little bit of automation remaining as part of connecting all the microservices automatically at startup due to time crunch. Hence, here are a couple of manual steps we need to take in advance:  
1. On your local system execute: `docker inspect postgresql -f "{{json .NetworkSettings.Networks }}" | jq -r '.taxi_default."Gateway"'`. Note the IP address, this is the IP address of the postgres container.  
2. On local, execute: `docker exec -it etl-container bash` => execute: `vi /home/app/expose/expose_apis.py` => edit to change the value of the variable "host" on line #11 to reflect the IP value obtained above => save changes.  
Execute: cd ~ && vi .dbt/profiles.yml => change the value of host there as well.  

-------------------**Requisites end**--------------------------------------  

3. On a browser, enter: `http://localhost:9021`. Since, it could take a few seconds for the broker to be registered completely, you might see something like this:  

![9021-unhealthy](/taxi-1/images/9021-unhealthy.png)  

Wait for a few seconds, it will turn to something like this:  

![9021-healthy](/taxi-1/images/9021-healthy.png)  

4. Now that the cluster is stable, we will create a connector. Change directory to `extract_stream_load` and execute `./pg_sink_connector_create.sh`. It would ask you the topic to land the data in kafka the table name to land the data in postgres. As you press enter, it will give you the connector details.  

5. Return to the browser to the control-center console. To verify that the connector is successfully created and running, select the cluster => select Connect on left panel => select connect-default, you should see the connector created in last step in running state, e.g.  

![connector-state](/taxi-1/images/connector-state.png)  

6. Now, the pipeline is up. We just need to execute our script to flow the data through it.  
But first, on your bash terminal, run: `docker exec -it postgresql /bin/bash` and then `psql -h localhost -U postgres`, this will get you to the psql terminal. Run `\dt` to verify if any tables exist already. Since, its a fresh instance, you won't see any tables.  

On another bash terminal, run: `docker exec -it etl_container python /home/app/extract_stream_load/async_pull.py`. Do not close the terminal. You would see logs from the execution like below:  

![script-logs](/taxi-1/images/script-run-op.png)  

> Note: I have inserted an app token in async_pull.py on line#24 since the website claimed it makes the calls faster. I have seen the api calls sometimes fail to start, you might want to retry by commenting out the token block in such cases.  

Now, verify the table in postgres.  

![table-created](/taxi-1/images/table-created.png)  

![table-count](/taxi-1/images/table-count.png) 

7. Now that the transactional table is populated, we can view the data using the api. On your local, execute: `docker exec -it etl_container uvicorn home.app.taxi.expose.expose_apis:app --reload --host 0.0.0.0`. On your web browser, type `localhost:8000`, you'll see a tab as below:  

![api-home](/taxi-1/images/api_home.png)  

and you could download the dataset as: `localhost:8000/data/csv` or `localhost:8000/data/json`.  

Also, if you want to display sample data on the page itself: `localhost:8000/custom_query/display/select tip_id, trip_Seconds,trip_miles from trips` would return something like this:  

![api-data-display](/taxi-1/images/api-display-data.png)   

8. The only thing now remains is dbt transformation and testing. Run the following command on your local: `docker exec -it etl_container bash -c "cd /home/app/transform/taxi_tf; dbt run; dbt test `. You would see dbt running the models  
![dbt-run](/taxi-1/images/dbt-run-op.png)  
and tests.   
![dbt-test](/taxi-1/images/dbt-tests.png)  

You can query the tables in postgres created post dbt transformations like this:  

![postges-tables](/taxi-1/images/dbt-models.png)  


9. You could also see the graph view of model: `docker exec -it etl_container bash -c "cd /home/app/transform/taxi_tf; dbt docs generate; dbt docs serve --port 8001" `

![dbt-display](/taxi-1/images/dim_model_dbt.png)  
