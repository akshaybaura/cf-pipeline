# Solution to Assignment

## Sections
1. [TL;DR version](#tldr)  
2. [Details](#details)  

## TL;DR version

![High Level architecture](/taxi-2/images/architecture_plan.jpeg)

This pipeline allows for high scalability and versatility, with large amounts of data being handled efficiently through the combination of Kafka, S3, and ClickHouse. The use of dbt and Airflow for transformation and orchestration ensures that the data is processed accurately and efficiently. Apache Superset provides a powerful tool for data visualization and querying, while the creation of reverse ETL procedures ensures that any changes to the data warehouse are accurately reflected in the source systems. 

## Details

### Data Ingestion Layer
The data ingestion layer is responsible for capturing data from different sources and feeding them into the pipeline. We would use streaming mechanism to get the data into our system. We would use Kafka to capture and stream data in real-time. The layer ensures that data is captured and stored in the most efficient way possible. 
The producer application will use a serializer which will be able to bifurcate small messages(text) from large messages (media files). Large messages will be stored in an S3 bucket and the corresponding url will be sent back to the producer which will be replaced in the actual message and streamed to the kafka topic alongwith small messages.

### Data Processing Layers
The data processing layers are responsible for preliminary transforming and cleaning the data before it is stored in the data warehouse and also post the load. Hence, the layer consists of two parts - pre-load processing layer and post-load layer.  
The pre-load layer is responsible for validating the data, converting data types, and cleaning the data using tools such as Pydantic which would internally leverage the schema stored in Schema-Registry of Kafka setup to comply with data contracts and schema evolution.  
The post-load layer is responsible for creating and complying with a data model that would subsequently enable faster and efficient data retrieval from the warehouse. For this, we could use DBT. An added advantage of using this tool would be the capability of integrating unit, smoke, regression tests with the models themselves. To orchestrate some of the dependencies between different models and tests, we could use Airflow.   

### Data Storage Layer
The data storage component stores the data in ClickHouse, a column-oriented OLAP database, and enables easy retrieval of data. The layer ensures that data is transformed and stored in an efficient and organized manner. Clickhouse has a very fast response to aggregate queries and can have 4096 concurrent connections. It has a lot features out of the box such as inbuilt support for kafka, dbt and visualisation tools.  

### Data Visualization Layer
The data visualization layer is responsible for visualizing the data and enabling self-service querying, dashboarding etc. The layer consists of Apache Superset, a data visualization tool that enables easy and interactive data exploration. The layer ensures that data is easily accessible and can be visualized in a user-friendly way.  
For reverse ETL and specific other usecases, we could build mechanisms to achieve them such as writing scripts or procedures to fetch data from warehouse to feed the source system on a microbatch interval or use tools such as hightouch, rockset etc.  

### Host
Each of these tools (with exception of S3) are natively open source. Hence, we would need to host them unless we go for a managed version. To host them, we can deploy these microservice containers as tasks and services in AWS ECS or as pods in EKS. Managing the underlying EC2 instances still could be a pain point, hence we could opt for Fargate instead.  

### Pros of Each Tool
**Kafka**: Provides reliable, real-time streaming of data and ensures efficient data capture and delivery.  
**S3**: Provides scalable and cost-effective storage for large files and ensures easy retrieval of data.  
**Pydantic**: Provides a robust and easy-to-use framework for data validation and transformation, enabling efficient data processing.  
**ClickHouse**: Provides fast querying and retrieval of data and enables efficient storage of data in a column-oriented format.  
**DBT**: Provides easy-to-use transformation and modeling of data and ensures efficient and organized storage of data in the data warehouse.  
**Airflow**: Provides orchestration of workflows, enabling efficient transformation of data in batches and microbatches.  
**Apache Superset**: Provides interactive data exploration and visualization, enabling self-service querying and dashboarding. Can also help to reduce the operational overhead and improve the scalability and availability of the application.  
**AWS ECS/EKS (with fargate)**: Provides easy orchestration of containers and lower maintenance overhead with use of fargate.   
