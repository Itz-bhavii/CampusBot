import chromadb

chromaClient = chromadb.HttpClient(host="localhost",port=8000)
chromaClient.delete_collection("practice_collection")