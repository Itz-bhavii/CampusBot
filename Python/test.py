import tempfile

# with tempfile.TemporaryDirectory() as temp:










# import chromadb
# from sentence_transformers import SentenceTransformer
# from chromadb.utils import embedding_functions

# model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")



# chromaClient = chromadb.HttpClient("localhost",8000)
# chromaClient.delete_collection("my_collection")

# # collection = chromaClient.get_or_create_collection(name="my_collection", embedding_function=model)
# collection = chromaClient.get_or_create_collection(name="my_collection")

# collection = chromaClient.get_collection("my_collection")
# collection.add(
#     ids=["doc1","doc2","doc3"],
#     documents=[
#         "The college fees must be paid by the 15th of the month.",
#         "Our college library has a vast collection of books.",
#         "The library is open from 9 AM to 5 PM."
#     ]
# )


# result = collection.query(
#     query_texts=["What are the library hours?"],
#     n_results=1
# )
# print(result["documents"])