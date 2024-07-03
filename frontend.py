import re
import streamlit as st
import requests
import json
st.title('Your copilot to prepare your next day at school')
# Lista de opciones para el selector desplegable
language_options = [ "Spanish",  "Català", "English","Français","Arabic", "Italian", "Nederlandse taal"]
theme_options = [ "Generic","Emotional Education",  "Gender and intersectionality", "Self-care and care for other people"]
    # Mostrar el selector desplegable
theme_selected = st.selectbox("Select in which Theme are you focused :", theme_options)
st.write(f"You have selected: {theme_selected}")
language_selected = st.selectbox("Select in which language you want the answer :", language_options)
    # Mostrar la opción seleccionada
st.write(f"You have selected: {language_selected}")
question = st.text_area(height=100,label="What is your question", value="")
# topic = st.text_input("Tematica", "")
if st.button("Ask a question"):
    #st.write("Querying the repository ... \"", question1+"\"")
    st.write("Generating answer based on the results in progress...")
    url = "http://127.0.0.1:8000/query_ai"

    payload = json.dumps({
      "query": question + "La respuesta tiene que ser siempre en " + language_selected,
      "theme": theme_selected 
    })
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    answer = json.loads(response.text)["answer"]
    rege = re.compile("\[Document\ [0-9]+\]|\[[0-9]+\]")
    m = rege.findall(answer)
    num = []
    for n in m:
        num = num + [int(s) for s in re.findall(r'\b\d+\b', n)]


    st.markdown(answer)
    documents = json.loads(response.text)['context']
    show_docs = []
    for n in num:
        for doc in documents:
            if int(doc['id']) == n:
                show_docs.append(doc)
                with st.expander(str(doc['id'])+" - " +doc['filename']+  doc['topic'][0]):
                    st.write(doc['content'])
        
#for n in num:
#        for doc in documents:
#            if int(doc['id']) == n:
#                show_docs.append(doc)
        
#        for doc in show_docs:
#            with st.expander(str(doc['id'])+" - " +doc['filename']):
#                st.write(doc['topic'])
#                st.write(doc['content'])

#for doc in show_docs:
#            with st.expander(str(doc['id'])+" - " +doc['filename']):
#                st.write(doc['topic'])
#                st.write(doc['content'])
        