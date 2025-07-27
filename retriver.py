from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import json
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=".env", override=True)
api_key = os.getenv("OPENAI_API_KEY")
# Load and query

vectorstore = FAISS.load_local(
    "faiss_function_store",
    OpenAIEmbeddings(model="text-embedding-3-small"),
    allow_dangerous_deserialization=True
)

query = 'tell me my phone no'
results = vectorstore.similarity_search_with_score(query, k=5)
for doc, score in results:
    print(f"Score: {score}")
    print(doc.page_content)
    print(doc.metadata)
