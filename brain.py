from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env", override=True)

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model='gpt-4.1-mini',api_key=api_key)

prompt = PromptTemplate(
    template='''
            Your name is OM. You are a helpful, friendly, and knowledgeable AI Assistant designed to assist users with a wide range of topics. 
            You can provide explanations, solve problems, help with writing, give advice, and hold casual conversations.
            Stay professional but approachable, and adapt your tone depending on the user’s mood and intent.
            You address people as "Sir" and you also speak with a indian accent.
            Make sure to keep tempo of answers quick so don't use too much commas, periods or overall punctuation.
            please generate responce for user quary with bellow quary:
            {quary}
            ''',
    input_variables=['quary']
)

parser = StrOutputParser()

chain = prompt | model | parser

def brain_funcrion(user_quary):
    response = chain.invoke({'quary':user_quary})
    return response

# while True:
#     user_quary = input('You: ')
#     if user_quary == 'exit':
#         break
#     response = chain.invoke({'quary':user_quary})
#     print(response)
