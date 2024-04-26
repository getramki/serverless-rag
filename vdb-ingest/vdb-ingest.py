# A Lambda function invoked by s3 upload object event
import urllib
import json
import boto3
import lancedb
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from lancedb.pydantic import Vector, LanceModel
from lancedb.embeddings import get_registry
import pandas as pd
import os

s3 = boto3.client('s3')

def handler(event, context):
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # Get vectordb bucket from environment variables
    vdbbucket = os.environ['VdbBucketName']

    try:
        if (key.find('/')!=-1):
            k = key.split('/')
            prefix = k[0]
            obj = k[1]
            
            category = prefix

        else:
            category = "default"
        
        response = s3.get_object(Bucket=bucket, Key=key)
        
        # Download s3 object to tmp directory
        with open('/tmp/file.pdf', 'wb') as f:
             f.write(response['Body'].read())
        
        # Load the PDF document and split it into chunks
        loader = PyPDFLoader('/tmp/file.pdf')
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(docs)

        # Extract the page content from the Document objects
        doc_pages = [doc.page_content for doc in docs]

        # create text embeddings with bedrock model with docs object
        embed_client = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1")
        embeddings = embed_client.embed_documents(doc_pages)

        # Define a Pydantic Lance model to store the text and vector embeddings
        model = get_registry().get("bedrock-text").create(name="amazon.titan-embed-text-v1")
        class tblschema(LanceModel):
             text: str = model.SourceField()
             vector: Vector(model.ndims()) = model.VectorField() # type: ignore

        df = pd.DataFrame({
                            "text": doc_pages,                            
                            "vector": embeddings
                           })
        
        # Connect to the database
        constr = "s3://" + vdbbucket + "/"+ category + "/"
        # Connect to the LanceDB, create a table, and add the data to the table
        db = lancedb.connect(constr)
        file = obj.rsplit('.', 1)[0]
        table = db.create_table(file, schema=tblschema, mode="overwrite")        
        table.add(df)
        
    except Exception as e:
        print(e)        
        raise e
    
    return {
        'statusCode': 200,
        'body': json.dumps('Ingestion Success!')
    }