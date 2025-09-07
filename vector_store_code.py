import os
import json
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv

import json
import re

load_dotenv(dotenv_path=".env", override=True)
api_key = os.getenv("OPENAI_API_KEY")

# Folder containing both JSON and TXT files
document_folder_path = "D:\\Programs\\OM-Version-2\\documents"

# Initialize
documents = []
embedding_texts = []

# Function to parse JSON file and return embedding text + Document
def json_to_doc(json_path):
    with open(json_path, "r") as f:
        function_json = json.load(f)

    doc_lines = []

    # Function name and description
    doc_lines.append(f"Function Name: {function_json['functionName']}")
    doc_lines.append(f"Description: {function_json['description']}\n")

    if 'group' in function_json:
        doc_lines.append(f"Group: {function_json['group']}\n")

    # Arguments
    doc_lines.append("Arguments:")
    for arg_name, arg_info in function_json['arguments'].items():
        doc_lines.append(f"- {arg_name}:")
        doc_lines.append(f"    Description: {arg_info.get('description', 'No description')}")
        allowed = arg_info.get('allowedValues', [])
        allowed_str = ", ".join(allowed) if allowed else "(any)"
        doc_lines.append(f"    Allowed Values: {allowed_str}")

    # Examples
    examples = function_json.get('examples', [])
    if examples:
        doc_lines.append("\nExample Prompts:")
        for ex in examples:
            doc_lines.append(f"- {ex}")

    doc_str = "\n".join(doc_lines)
    metadata = {
        "functionName": function_json.get("functionName"),
        "group": function_json.get("group", None),
        "type": "function_schema"
    }
    return doc_str, Document(page_content=json.dumps(function_json), metadata=metadata)

# Function to parse .txt files
def txt_to_doc(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(txt_path)
    metadata = {
        "filename": filename,
        "type": "text_note"
    }
    return content, Document(page_content=content, metadata=metadata)

# Process all files
for filename in os.listdir(document_folder_path):
    path = os.path.join(document_folder_path, filename)

    if filename.endswith(".json"):
        doc_str, doc = json_to_doc(path)
        embedding_texts.append(doc_str)
        documents.append(doc)

    elif filename.endswith(".txt"):
        content, doc = txt_to_doc(path)
        embedding_texts.append(content)
        documents.append(doc)

# Create embeddings
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Create vectorstore with embedded text
vectorstore = FAISS.from_texts(
    texts=embedding_texts,
    embedding=embedding_model,
    metadatas=[doc.metadata for doc in documents],
    ids=None
)

# Replace stored docs with original JSON or TXT contents
vectorstore.docstore._dict = {
    k: doc for k, doc in zip(vectorstore.docstore._dict.keys(), documents)
}

# Save FAISS vectorstore to local disk
vectorstore.save_local("faiss_function_store")

# convert VCF files to a dictionary format
# def contacts_to_dict(vcf_path):
#     contacts = {}
#     name, phone = None, None
    
#     with open(vcf_path, 'r', encoding='utf-8', errors='ignore') as f:
#         for line in f:
#             line = line.strip()
            
#             # Name
#             if line.startswith("FN:") or line.startswith("FN;"):
#                 name = line.split(":", 1)[1].strip()
#                 # Clean up emojis/special symbols from names
#                 name = re.sub(r'[^\w\s]', '', name).strip().lower()
            
#             # Phone
#             elif line.startswith("TEL"):
#                 phone = line.split(":", 1)[1].strip()
#                 # Normalize phone number
#                 phone = phone.replace(" ", "").replace("-", "")
            
#             # End of a contact
#             elif line == "END:VCARD":
#                 if name and phone:
#                     contacts[name] = phone
#                 name, phone = None, None

#     return contacts

# 10 digit Number extraction and filtering
# def is_company_number(number):
#     # Ignore numbers with non-digit characters or less than 10 digits
#     # You can add more rules here if needed
#     return not re.fullmatch(r'\+?\d{10,}', number)

# def extract_last_10_digits(number):
#     digits = re.sub(r'\D', '', number)  # Remove non-digit characters
#     if len(digits) >= 10:
#         return digits[-10:]
#     return None

# with open('contacts.json', 'r', encoding='utf-8') as f:
#     contacts = json.load(f)

# filtered_contacts = {}
# for name, number in contacts.items():
#     if is_company_number(number):
#         continue
#     last_10 = extract_last_10_digits(number)
#     if last_10:
#         filtered_contacts[name] = last_10

# # Save to a new JSON file
# with open('contacts_10digit.json', 'w', encoding='utf-8') as f:
#     json.dump(filtered_contacts, f, indent=4)

# print("Saved filtered contacts to contacts_10digit.json")

