# Send query request to API Gateway Endpoint
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
}' < Replace this with API Gateway Endpoint >