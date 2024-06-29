import re
import streamlit as st
import requests
import json
st.title('Your copilot to prepare your next day at school')
question = st.text_area(height=100,label="What is your question", value="")
# topic = st.text_input("Tematica", "")
if st.button("Ask a question"):
    #st.write("Querying the repository ... \"", question1+"\"")
    st.write("Generating answer based on the results in progress...")
    url = "http://127.0.0.1:8000/query_ai"

    payload = json.dumps({
      "query": question
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
    a = 1244
    for doc in show_docs:
        with st.expander(str(doc['id'])+" - "+doc['topic']+doc['subtopic']+doc['filename']):
            st.write(doc['content'])
            with open(doc['path'], 'rb') as f:
                st.download_button("Refernce to source", f, file_name=doc['filename'].split('/')[-1],key=a
                )
                a = a + 1
