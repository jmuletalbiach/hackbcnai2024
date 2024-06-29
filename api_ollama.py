from fastapi import FastAPI
#import qdrant_client
from langchain_community.embeddings import HuggingFaceEmbeddings
#from langchain_mistralai.chat_models import ChatMistralAI
#from langchain_mistralai.embeddings import MistralAIEmbeddings

#from langchain_core.messages import HumanMessage
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import environment_var
import os
from openai import OpenAI
#from langgraph.graph import END, MessageGraph




class Item(BaseModel):
    query: str
    def __init__(self, query: str) -> None:
        super().__init__(query=query)

nom_model = "sentence-transformers/msmarco-bert-base-dot-v5"
arguments_model = {'device': 'cpu'}
arguments_encoder = {'normalize_embeddings': True}
hf = HuggingFaceEmbeddings(
    model_name=nom_model,
    model_kwargs=arguments_model,
    encode_kwargs=arguments_encoder
)


## Client Ollama

client_genai = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )

##Client Mistral
# Define LLM
## model = ChatMistralAI(mistral_api_key=api_key)

##Client 



if environment_var.qdrant_storage =="cloud":
        client = QdrantClient(
        url=environment_var.qdrant_cloud_url, 
        api_key=environment_var.qdrant_cloud_key,
        )
        print (environment_var.qdrant_cloud_url)
        print(client.get_collections())
elif environment_var.qdrant_storage =="local":
        client = QdrantClient("localhost", port=6333)
        print ("qdrant local instance")

collection_name = "SocialEducation"
qdrant = Qdrant(client, collection_name, hf)


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Init"}

@app.post("/search")
def search(Item:Item):
    query = Item.query
    search_result = qdrant.similarity_search(
        query=query, k=10
    )
    i = 0
    list_res = []
    for res in search_result:
        list_res.append({"id":i,"path":res.metadata.get("path"),"content":res.page_content})
    return list_res

@app.post("/query_ai")
async def query_ai(Item:Item):
    query = Item.query
    search_result = qdrant.similarity_search(
        query=query, k=2
    )
    i = 0
    list_res = []
    context = ""
    mappings = {}
    i = 0
    for res in search_result:
        context = context + str(i)+"\n"+res.page_content+"\n\n"
        mappings[i] = res.metadata.get("path")
        list_res.append({"id":i,"path":res.metadata.get("path"),"content":res.page_content})
        i = i +1

    rolemsg = {"role": "system",
               "content": "Answer user's question using documents given in the context. In the context are documents that should contain an answer. Please always reference document id (in squere brackets, for example [0],[1]) of the document that was used to make a claim. Use as many citations and documents as it is necessary to answer question."}
    messages = [
        rolemsg,
        {"role": "user", "content": "Documents:\n"+context+"\n\nQuestion: "+query},
       ## {"role": "user", "content": "Capital of France"},
    ]
    print (messages)

    completion = client_genai.chat.completions.create(
        model="phi3",
        messages=messages,
        temperature=0.2,
        top_p=1,
        max_tokens=512,
        stream=False
    )
    response = completion.choices[0].message.content
    return {"context":list_res,"answer":response}
