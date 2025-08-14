from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import asyncio

# Load API key
load_dotenv(dotenv_path=".env", override=True)
api_key = os.getenv("OPENAI_API_KEY")

# Initialize model
model = ChatOpenAI(model='gpt-4.1-mini', api_key=api_key) 


systemBehaviour = """
Your name is OM. You are a helpful AI Assistant designed to understand both user queries and task requests. You are maintained by somnath and he is your boss.
Given a transcript of a conversation/command and retriv informations as json structure/text docs, analyze the informations and extract the primary action(s) that
need to be executed and answer for normal/general quary.
Use the retrieved documents and current conversation to respond appropriately.
You may be given results from previously executed actions.
Use this information to give a more accurate or intelligent answer.
If action results are provided, incorporate them naturally into your response.

## Instructions:
- If the user asks a general question observe carefully, respond in `converssion_output` and the actions as null.
- If the user gives a task or command (like "open light", "play music", etc), return one or more structured `action` items and reply in formality in the converssion_output.
- If the user mixes both, return both parts.
- If you confuse about user quary or need extra info for taking an action than feel free to ask 
- In arguments set only one allowedValues per action not coma seperated allowedValues.
- If allowedValues field was not empty than pass argument from allowedValues only don't pass other value.
- You can generate multiple actions for combined quaries.
- If no device was mentioned than consider "PC" as default.
- If user asks to play something than do perform search operation on youtube.

## Output Format (strict JSON):
[
  {"converssion_output": "<reply to query for both cases>"},
  {
    "action": "<Action description>",
    "functionName": "<function_name or null>",
    "arguments": {
      "arg1": "value",
      ...
    }
  }
]
Always include the outer [ ] brackets and do not break json format.
Be brief and use Indian tone.
"""

# Prompt with memory + context
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=systemBehaviour),
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="retrieved_docs")
])

# Create the parser
parser = StrOutputParser()

# Form the full chain
chain: Runnable = prompt | model | parser

def summarize_chat_history():
    if len(chat_history) <= 12:
        return  # no need to summarize yet

    early_history = chat_history[:-6]  # keep last 6 messages
    recent_history = chat_history[-6:]

    summary_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an AI assistant helping organize a human's daily conversation into a memory bank.
Your task is to summarize the following chat history which contain AIMessage and HumanMessage. Focus on:
- Important topics discussed
- Specific tasks, facts, or questions
- Any names, places, or entities mentioned
- The tone of the conversation (e.g., casual, technical, emotional)

Avoid unnecessary filler. Be concise, structured, and human-readable."""),
        MessagesPlaceholder(variable_name="chat_history")
    ])
    
    summary_chain = summary_prompt | model | parser
    summary = summary_chain.invoke({"chat_history": early_history})

    # Replace full old history with one summary message
    chat_history.clear()
    chat_history.append(AIMessage(content="Summary of earlier discussion: " + summary))
    chat_history.extend(recent_history)


# In-memory chat history (you can later replace with a vector store if needed)
chat_history = []
# print('programm execute')

vectorstore = FAISS.load_local(
    "faiss_function_store",
    OpenAIEmbeddings(model="text-embedding-3-small"),
    allow_dangerous_deserialization=True
)


async def brain_function(user_quary):
    # Add user message
    chat_history.append(HumanMessage(content=user_quary))

    results = vectorstore.similarity_search(user_quary, k=6)
    retrieved_doc_msgs = [SystemMessage(content=doc.page_content) for doc in results]

    for doc in results:
        print(doc.metadata)

    # # 🔍 Format prompt before sending to LLM
    # formatted_prompt = prompt.format_messages(
    #     chat_history=chat_history,
    #     retrieved_docs=retrieved_doc_msgs
    # )

    # # 🧾 Print the final prompt text (as the model sees it)
    # print("\n===== FULL PROMPT SENT TO LLM =====\n")
    # for msg in formatted_prompt:
    #     role = msg.type.upper()
    #     print(f"{role}: {msg.content}\n")
    # print("===== END OF PROMPT =====\n")

    # 🚀 Invoke model using same inputs
    response = await chain.ainvoke({
        "chat_history": chat_history,
        "retrieved_docs": retrieved_doc_msgs
    })


    chat_history.append(AIMessage(content=response))
    summarize_chat_history()
    return response


if __name__ == "__main__":
    async def assistant_loop():
        while True:
            quary = input("You: ")
            if 'exit' in quary:
                break
            print(await brain_function(quary))
        print(chat_history)
    asyncio.run(assistant_loop())
