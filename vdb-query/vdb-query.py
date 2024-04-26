import json
import boto3
import lancedb
import os

from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_community.vectorstores.lancedb import LanceDB


# A lambda function invoked by an API Gateway HTTP Post method
def handler(event, context):
    # Get the input from the event
    input = json.loads(event['body'])
    querydata  = input['querydata']
    query = querydata['query']
    category = querydata['category']
    topic = querydata['topic']
    config = input['config']
    maxTokenCount = int(config['maxTokenCount'])
    stopSequences = config['stopSequences'],
    temperature = float(config['temperature'])
    topP = float(config['topP'])

    # print(input)
    # print(querydata)
    # print(query)
    # print(category)
    # print(topic)
    # print(config)
    # print(maxTokenCount)
    # print(stopSequences)
    # print(temperature)
    # print(topP)

    try:

        # Get vectordb bucket from environment variables
        vdbbucket = os.environ['VdbBucketName']
        # Connect to the database
        constr = "s3://" + vdbbucket + "/"+ category + "/"
        db = lancedb.connect(constr)
        
        # Open the lancedb table
        table = db.open_table(topic)

        # Create a vector store with the lancedb table
        embedding = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1")
        vs = LanceDB(connection=table, embedding=embedding, vector_key="vector")

        # Search the vector store for similar documents to the query
        docs = vs.similarity_search(query, 1)
        
        # Get the page content of the similar documents
        result = [doc.page_content for doc in docs]
        
        # print("Result-1: " + result[0])
        # print("Result-2: " + result[1])
        # print("Result-3: " + result[2])

        # Code to create invoke bedrock titan infrence  model with a prompt and get the response
        # Prompt is designed to tell llm to generate a response based on the query and context only
        prompt = "Answer the following question: " + query + " with the only information provided in the following Context: " + result[0]

        inputText = "User: "+ prompt + "\n" + "Assistant: "

        # print("Prompt: " + prompt + "\n\n")

        body = json.dumps ({
            "inputText": inputText,
            "textGenerationConfig": {
                "maxTokenCount": maxTokenCount,
                "stopSequences": stopSequences,
                "temperature": temperature,
                "topP": topP
            }
        })
        
        print("Body: " + body + "\n\n")

        brc = boto3.client('bedrock-runtime')
        br_response = brc.invoke_model(
            body=body,
            modelId='amazon.titan-text-express-v1',
            # trace='ENABLED'|'DISABLED',
        )
        response_body = json.loads(br_response.get("body").read())

        print(f"Input token count: {response_body['inputTextTokenCount']}")

        for result in response_body['results']:            
            rsp = result['outputText']
            print(f"Output Token count: {result['tokenCount']}")
            print(f"Response: {result['outputText']}")
            print(f"Completion reason: {result['completionReason']}")

        response_to_api = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': rsp
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'text/plain'
            },
            'body': "Error"
        }
    
    # Return the response to api gateway
    return response_to_api