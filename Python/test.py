import chromadb
from google import genai
import os
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions


model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

chromaClient = chromadb.HttpClient("localhost",8000)


collection = chromaClient.get_or_create_collection(name="practice_collection", embedding_function=model)

# API_KEY = os.getenv("API_KEY")
# googleClient = genai.Client(api_key=API_KEY)


# standalone_question = "What is the projected highest placement package in lakhs for the year 2026-27?"

# querryExpansionPrompt = f"""
# Given the following user question, generate 4 alternative ways of asking the same thing.
# The queries should be diverse and cover different phrasings. Include the original question in the list and dont add any hint that it is the original question and give the string such as 2 questions can be splitted by two new lines

# Original Question: "{standalone_question}"

# Alternative Queries:
# 1. {standalone_question}
# 2. ...
# 3. ...
# 4. ...
# 5. ...
# """

# expandedQuerryRaw = googleClient.models.generate_content(
#     model="gemini-2.0-flash",
#     contents=querryExpansionPrompt
# )

# questions = list(expandedQuerryRaw.text.strip().split("\n\n"))

# print(questions)
# print(len(questions))
# results = collection.query(
#     query_texts= questions,
#     n_results= 5
# )

# distinct = set({})

# count = 0
# for wholeList in results["documents"]:
#     for doc in wholeList:
#         distinct.add(doc)
#         # print("******************************************************************************************")
#         count = count + 1

# print(count)
# count = 0
# distinct = list(distinct)
# for doc in distinct:
#     print(doc)
#     print("******************************************************************************************")
#     count = count + 1
# print(count)
# for que in questions:
#     print(que)









# chromaClient.delete_collection("practice_collection")

# collection = chromaClient.get_or_create_collection(name="my_collection")

# collection = chromaClient.get_collection("practice_collection")
# collection.add(
#     ids=["doc1","doc2","doc3"],
#     documents=[
#         "The college fees must be paid by the 15th of the month.",
#         "Our college library has a vast collection of books.",
#         "The library is open from 9 AM to 5 PM."
#     ]
# )


# result = collection.query(
#     query_texts=[""],
#     n_results=1
# )
print(collection.get())











# from collections import defaultdict

# # Your corrected input data
# metadatas = [
#     {"sourceheader": "heading 1"},
#     {"sourceheader": "heading 1"},
#     {"sourceheader": "heading 3"},
#     {"sourceheader": "heading 2"}
# ]
# datas = [
#     "Data for the first heading 1.",
#     "More data for heading 1.",
#     "Data related to heading 3.",
#     "Content for heading 2."
# ]

# # Use defaultdict(list) to automatically create list containers for new headings
# grouped_data = defaultdict(list)

# # Iterate through the lists by index
# for i in range(len(metadatas)):
#     # Extract the actual heading string from the dictionary
#     heading = metadatas[i]["sourceheader"]
#     data_point = datas[i]
    
#     # Append the data to the correct list
#     grouped_data[heading].append(data_point)

# # Use a dictionary comprehension to join the lists into single paragraphs
# final_paragraphs = {heading: ' '.join(data_list) for heading, data_list in grouped_data.items()}

# data = list(grouped_data.keys() )
# print(data)