# Implementing RAG with Event based Serverless Architecture on AWS 

In Generative AI, Retrieval-Augmented Generation (RAG) is a method to generate response by LLM by giving it context from an authoritative knowledge base. This repo shows how to implement a RAG with event based Serverless Architecture on AWS. 

___ 

### LanceDB - A Vector Database 

In this application we use LanceDB (https://lancedb.github.io/lancedb/) as vector database with S3. It is an open source serverless vector database for AI that's designed to store, manage, query and retrieve embeddings on large-scale multi-modal data. 

Here the compute part of LanceDB engine works with-in Lambda and data is stored on S3 as Lance Table objects. 
___ 

### RAG Serverless Architecture 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/Implementing-RAG.png?raw=true) 

___ 

### Structure of this repo 

This repo contains two lambda functions, a SAM Template to deploy and one test data file.

* VectorDB Ingest Function (vdb-ingest) - in "vdb-ingest" folder 

* VectorDB Query Function (vdb-query) - in "vdb-query" folder. 

* A SAM template to deploy this repo. 

* A PDF file "Samosa-Recipe.pdf" for testing in test-data folder 

___ 

### Prerequisites 

AWS Account and IAM user with necessary permissions for creating Lambda, aws cli, SAM cli, configure IAM user with necessary programmatic permissions. 

In your AWS Account you need to apply and get access to the foundation models 'Titan Embeddings G1 - Text' and 'Titan Text G1 - Express' in Amazon Bedrock service. You can also try with other text generating models by changing the code in Lambda function. 

* Install and configure AWS CLI, SAM CLI, Python 3.12 and Docker. You can follow respective guides from their websites. 

Please install and configure above before going further 

* You can incur charges in your AWS Account by following these steps below. 

* The code will deploy in us-west-2 region, change it wherever necessary if deploying in another supported region. 

___ 

### Deploy 

After downloading the repo in the terminal Change Directory to repo directory and follow the steps below 

* The packages used in this code base langchain_community and lancdb are heavy in size, they don't fit in Lambda Layers as they go beyond 250mb limit. So, we make the docker images of our code and run them as containers with lambda functions. 

* Run the following SAM command to build, it will build docker images and as well makes the repo ready for deployment. 

<pre><code>sam build</pre></code> 

* Deploy the SAM template. To learn more about SAM you can follow the guide here https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html 

* Run following SAM command to deploy, make sure you agree (type 'y') when SAM asks for confirmation to create IAM roles and deploy the changeset. 

The resources on AWS will be created with the 'stack name' and 'region' you give while running the following command and your aws 'account-id'. You can look at the format in SAM template ‘template.yaml’ in this repo. The resources created can also be found in the CloudFormation's output console. 

<pre><code>sam deploy --guided</pre></code> 

___ 

### Ingesting Data 

The present code is written to accept only PDF files. I have used PyPDFLoader. You can extend this repo or try other loaders from LangChain community. 

You need to create a folder for the category of data files you want to upload in the ingestion bucket. You get the ingestion bucket name from the "sam deploy" command output or from outputs of CloudFormation's console. It will be in the format "<AWS::StackName>-ingest-<AWS::Region>-<AWS::AccountId>" 

You can try with any data PDF files. 

* Example - One of my favorite snacks is Samosa. I want to create a category of "Recipes" and upload the PDF file of "Samosa-Recipe.pdf" which I have created and provided in test-data folder in repo. We can ingest this recipe file and ask queries on the recipe. 

With following command inside the repo directory, you can create folder for category "recipes" in the ingestion bucket and upload a file "Samosa-Recipe.pdf" in it. 

<pre><code>aws s3 cp ./test-data/Samosa-Recipe.pdf s3://<'Replace-With-Your-Ingest-Bucket-Name-from-SAM-Outputs'>/recipes/Samosa-Recipe.pdf</pre></code> 

When you ingest the file in the S3 ingest bucket an event notification is triggered to invoke the "vdb-ingest" lambda function. This Lambda function reads the raw pdf file from the ingest bucket, it creates chunks of the document and gets the embedding vectors from the Bedrock Embedding model "Titan Embeddings". Once it gets the embeddings, it will create a LanceDB Table (vector) in the folder same as "category" in Vector DB bucket on S3 and then adds the embedding vectors to the vector table. 

You can monitor the function in CloudWatch logs. It will look like as below 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/Ingest-Fun-Log.png?raw=true) 


The Lance table is a folder in the S3 Vector DB bucket which contains other folders and data as below 

Samosa-Recipe.lance table (S3 Folder) under "recipes" folder in the Vector DB bucket. 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/LanceTable-on-S3.png?raw=true) 


Transactions 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/LanceTable-Transactions.png?raw=true) 


Versions 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/LanceTable-Versions.png?raw=true) 


Data 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/LanceTable-Data.png?raw=true) 

___ 

### Querying 

You can invoke the Query function from the API Gateway endpoint with curl or postman. You can get the API Gateway endpoint from the SAM output.

While querying you must pass the "query" along with "category" and "topic" and as well as LLM "config" parameters. The query function reads the lance table with the help of Bedrock Embeddings, gets the context and passes it on to LLM to generate a response. 

In our example you can do the following with curl. This command is provided in test-commands.md file in test-data folder of this repo. 

``` 
curl -d '{  
    "querydata":{ 
    "query":"Why is my samosa not crispy?", 
    "category":"recipes", 
    "topic":"Samosa-Recipe" 
    }, 
    "config":{ 
        "maxTokenCount": 1024, 
        "stopSequences": "User:", 
        "temperature": 0, 
        "topP": 0.8 
    } 
}' < Replace this with API Gateway Endpoint'> 

``` 

The expected output for the above can be as below 

``` 
This happens when you fry the samosa in hot oil. You need to fry the samosa on low heat always. Also, your dough needs to be stiff. Soft dough will also result in a not-so-crispy samosa. 

``` 

Query with Curl 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/RAG-Query-curl.png?raw=true) 


Query with Postman 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/RAG-Query-Postman.png?raw=true) 

 
Query Function Log from Cloud Watch 

![alt text](https://github.com/getramki/serverless-rag/blob/main/images/Query-Fun-log.png?raw=true) 