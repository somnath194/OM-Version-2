from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

# Load API key
load_dotenv(dotenv_path=".env", override=True)
api_key = os.getenv("OPENAI_API_KEY")

# Initialize model
model = ChatOpenAI(model='gpt-4.1-mini', api_key=api_key)  

# Define prompt with memory (chat history)
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content='''Your name is OM. You are a helpful, friendly, and knowledgeable AI Assistant designed to assist users with a wide range of topics.
You provide explanations, solve problems, help with writing, give advice, and hold casual conversations.
Stay professional but approachable. You address people as "Sir" and speak with an Indian accent.
Keep answers quick without too many commas, periods, or punctuation.'''),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessage(content="{quary}")
])

# Create the parser
parser = StrOutputParser()

# Form the full chain
chain: Runnable = prompt | model | parser

# In-memory chat history (you can later replace with a vector store if needed)
chat_history = []
# print('programm execute')

def brain_function(user_quary):
    # Add user message
    chat_history.append(HumanMessage(content=user_quary))
    
    # Run chain with chat history
    response = chain.invoke({
        "quary": user_quary,
        "chat_history": chat_history
    })
    
    # Add assistant message to history
    chat_history.append(AIMessage(content=response))
    return response

# if __name__ == "__main__":
#     while True:
#         quary = input("You: ")
#         if 'exit' in quary:
#             break
#         print(brain_function(quary))
#     print(chat_history)
