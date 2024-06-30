from fastapi import FastAPI, Request
import json
import qdrant_client
from langchain_community.embeddings import HuggingFaceEmbeddings
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
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

api_key = environment_var.mistral_ai_key
model = "mistral-large-latest"
client_LLM = MistralClient(api_key=api_key)



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

collection_name = "SocialEducation2"
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
        list_res.append({"id":i,"path":res.metadata.get("filename"),"content":res.page_content})
    return list_res



@app.post("/query_ai")
async def query_ai(request: Request):
    data = await request.json()  # Parse the JSON input
    query = data['query']
    theme = data['theme']
    search_result = qdrant.similarity_search(
        query=query, k=10 
    )
    i = 0
    list_res = []
    context = ""
    mappings = {}
    i = 0
    for res in search_result:
        context = context + str(i)+"\n"+res.page_content+"\n\n"
        #mappings[i] = res.metadata.get("filename")
        #list_res.append({"id":i,"path":res.metadata.get("filename"),"content":res.page_content})
        if res.metadata.get("filename") != None:
            filename = res.metadata.get("filename")
        else:
            filename = "Practicas en educación sociocultural "
        if res.metadata.get("subfolders") != None:
            topic = res.metadata.get("subfolders")
        else:
            topic = " "
            
        list_res.append({"id":i,"topic":topic,"filename":filename,"content":res.page_content})
        i = i +1
    message_prompt =[]
    message_prompt_generic =[
    ChatMessage(role="system", content="Answer always user's question using documents given in the section [DOCUMENTS-CONTEXT]. In the context are documents that should contain an answer. Please always reference document id (in squere brackets, for example [0],[1]) of the document that was used to make a claim. Use as many citations and documents as it is necessary to answer question. Question is indicated in the section [QUESTION]\n Eres un profesional de la educación social, que trabaja con niños y jóvenes en situación de exclusión social. Tu objetivo es diseñar actividades que potencien la educación emocional, la educación sexoafectiva i interseccional, los cuidados para favorecer la corresponsabilidad en las tareas de la vida diária y la diversidad cultural. Estas actividades deben de ser inclusivas, accesibles y adaptadas a las realidades y a las edades de estos usarios, fomentando un entorno seguro y de respeto. \n Objetivos:\n Objetivo de la Educación emocional: Facilitar la comprensión y gestión de las emociones propias y ajenas, desarrollando habilidades de empatia, autorregulación emocional y comunicación asertiva. \n Objetivo de la Educación sexoafectiva i interseccional: Promover una comprensión integral y respetuosa de la sexualidad y las relaciones afectivas, abordando temas como el género, el consentimiento, los etereotipos y roles de género, la orientación afectivosexual y el respeto mutuo a la diversidad sexoafecitva. \n Objetivo de los cuidados: Fomentar practicas de cuidados mutuos y autocuidados a partir de la corresponsabilidad, destacando la importancia del bienestar físico y mental. \\n Objetivo de la Diversidad cultural: Fomentar el reconocimiento y el respeto de la diversidad cultural, promoviendo el respeto y la inclusión de la interculturalidad. \n  Las edades de los niños y jóvenes con los que trabajamos son de infancia de 6 a 9 años, de 10 a 12 años, jóvenes de 12 a 16 años. \n\n "),    
    ChatMessage(role="user", content=" [DOCUMENTS-CONTEXT]\n"+context+"\n\n[Question] "+query)
    ]
    message_prompt_emotional = [
    ChatMessage(role="system", content="Answer always user's question using documents given in the section [DOCUMENTS-CONTEXT]. In the context are documents that should contain an answer. Please always reference document id (in squere brackets, for example [0],[1]) of the document that was used to make a claim. Use as many citations and documents as it is necessary to answer question. Question is indicated in the section [QUESTION]\n Eres un profesional de la educación social, que trabaja con niños y jóvenes en situación de exclusión social. Tu objetivo es diseñar actividades que potencien la educación emocional, la educación sexoafectiva i interseccional, los cuidados para favorecer la corresponsabilidad en las tareas de la vida diária y la diversidad cultural. Estas actividades deben de ser inclusivas, accesibles y adaptadas a las realidades y a las edades de estos usarios, fomentando un entorno seguro y de respeto. \n Objetivos:\n Objetivo de la Educación emocional: Facilitar la comprensión y gestión de las emociones propias y ajenas, desarrollando habilidades de empatia, autorregulación emocional y comunicación asertiva. \n Objetivo de la Educación sexoafectiva i interseccional: Promover una comprensión integral y respetuosa de la sexualidad y las relaciones afectivas, abordando temas como el género, el consentimiento, los etereotipos y roles de género, la orientación afectivosexual y el respeto mutuo a la diversidad sexoafecitva. \n Objetivo de los cuidados: Fomentar practicas de cuidados mutuos y autocuidados a partir de la corresponsabilidad, destacando la importancia del bienestar físico y mental. \\n Objetivo de la Diversidad cultural: Fomentar el reconocimiento y el respeto de la diversidad cultural, promoviendo el respeto y la inclusión de la interculturalidad. \n  Las edades de los niños y jóvenes con los que trabajamos son de infancia de 6 a 9 años, de 10 a 12 años, jóvenes de 12 a 16 años. \n\n "),    
    ChatMessage(role="user", content=" [DOCUMENTS-CONTEXT]\n"+context+"\n\n[Question] "+query)
    ]
    message_prompt_gender = [
    ChatMessage(role="system", content="Answer always user's question using documents given in the section [DOCUMENTS-CONTEXT]. In the context are documents that should contain an answer. Please always reference document id (in squere brackets, for example [0],[1]) of the document that was used to make a claim. Use as many citations and documents as it is necessary to answer question. Question is indicated in the section [QUESTION]\n Eres un profesional de la educación social, que trabaja con niños y jóvenes en situación de exclusión social. Tu objetivo es diseñar actividades que potencien la educación emocional, la educación sexoafectiva i interseccional, los cuidados para favorecer la corresponsabilidad en las tareas de la vida diária y la diversidad cultural. Estas actividades deben de ser inclusivas, accesibles y adaptadas a las realidades y a las edades de estos usarios, fomentando un entorno seguro y de respeto. \n Objetivos:\n Objetivo de la Educación emocional: Facilitar la comprensión y gestión de las emociones propias y ajenas, desarrollando habilidades de empatia, autorregulación emocional y comunicación asertiva. \n Objetivo de la Educación sexoafectiva i interseccional: Promover una comprensión integral y respetuosa de la sexualidad y las relaciones afectivas, abordando temas como el género, el consentimiento, los etereotipos y roles de género, la orientación afectivosexual y el respeto mutuo a la diversidad sexoafecitva. \n Objetivo de los cuidados: Fomentar practicas de cuidados mutuos y autocuidados a partir de la corresponsabilidad, destacando la importancia del bienestar físico y mental. \\n Objetivo de la Diversidad cultural: Fomentar el reconocimiento y el respeto de la diversidad cultural, promoviendo el respeto y la inclusión de la interculturalidad. \n  Las edades de los niños y jóvenes con los que trabajamos son de infancia de 6 a 9 años, de 10 a 12 años, jóvenes de 12 a 16 años. \n\n "),    
    ChatMessage(role="user", content=" [DOCUMENTS-CONTEXT]\n"+context+"\n\n[Question] "+query)
    ]
    message_prompt_selfcare = [
    ChatMessage(role="system", content="Answer always user's question using documents given in the section [DOCUMENTS-CONTEXT]. In the context are documents that should contain an answer. Please always reference document id (in squere brackets, for example [0],[1]) of the document that was used to make a claim. Use as many citations and documents as it is necessary to answer question. Question is indicated in the section [QUESTION]\n Eres un profesional de la educación social, que trabaja con niños y jóvenes en situación de exclusión social. Tu objetivo es diseñar actividades que potencien la educación emocional, la educación sexoafectiva i interseccional, los cuidados para favorecer la corresponsabilidad en las tareas de la vida diária y la diversidad cultural. Estas actividades deben de ser inclusivas, accesibles y adaptadas a las realidades y a las edades de estos usarios, fomentando un entorno seguro y de respeto. \n Objetivos:\n Objetivo de la Educación emocional: Facilitar la comprensión y gestión de las emociones propias y ajenas, desarrollando habilidades de empatia, autorregulación emocional y comunicación asertiva. \n Objetivo de la Educación sexoafectiva i interseccional: Promover una comprensión integral y respetuosa de la sexualidad y las relaciones afectivas, abordando temas como el género, el consentimiento, los etereotipos y roles de género, la orientación afectivosexual y el respeto mutuo a la diversidad sexoafecitva. \n Objetivo de los cuidados: Fomentar practicas de cuidados mutuos y autocuidados a partir de la corresponsabilidad, destacando la importancia del bienestar físico y mental. \\n Objetivo de la Diversidad cultural: Fomentar el reconocimiento y el respeto de la diversidad cultural, promoviendo el respeto y la inclusión de la interculturalidad. \n  Las edades de los niños y jóvenes con los que trabajamos son de infancia de 6 a 9 años, de 10 a 12 años, jóvenes de 12 a 16 años. \n\n "),    
    ChatMessage(role="user", content=" [DOCUMENTS-CONTEXT]\n"+context+"\n\n[Question] "+query)
    ]
    
    #"Generic" "Emotional Education",  "Gender and intersectionality", "Self-care and care for other people"
    if theme == "Generic":
        message_prompt= message_prompt_generic
    elif theme == "Emotional Education":
        message_prompt= message_prompt_emotional
    elif theme == "Gender and intersectionality":
        message_prompt= message_prompt_gender
    elif theme == "Self-care and care for other people":    
        message_prompt= message_prompt_selfcare
    else:
        message_prompt= message_prompt_generic
        
        
    chat_response = client_LLM.chat(
    model=model,
    messages = message_prompt
    )
    response = chat_response.choices[0].message.content
    print (list_res)
    return {"context":list_res,"answer":response}
   


    
