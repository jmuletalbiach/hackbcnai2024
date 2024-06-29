import PyPDF2
from os import listdir
from os.path import isfile, join,isdir
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
import sys
from langchain_text_splitters import TokenTextSplitter
from pptx import Presentation
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import docx
import environment_var

def get_input_streams(dir):
    stream_list = []
    for f in listdir(dir):
        if isfile(join(dir,f)):
            stream_list.append(join(dir,f))
        elif isdir(join(dir,f)):
            stream_list= stream_list + get_input_streams(join(dir,f))
    return stream_list


def getTextFromWord(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)


def main_indexer(sourcepath):
    nom_model = "sentence-transformers/msmarco-bert-base-dot-v5"
    arguments_model = {'device': 'cpu'}
    arguments_encoder = {'normalize_embeddings': True}
    hf = HuggingFaceEmbeddings(
        model_name=nom_model,
        model_kwargs=arguments_model,
        encode_kwargs=arguments_encoder
    )

    if environment_var.qdrant_storage =="cloud":
        client = QdrantClient(
        url=environment_var.qdrant_cloud_url, 
        api_key=environment_var.qdrant_cloud_key,
        )
        print ("qdrant cloud service instance")
        print(client.get_collections())
    elif environment_var.qdrant_storage =="local":
        client = QdrantClient("localhost", port=6333)
        print ("qdrant local instance")
        print(client.get_collections())
    

    collection_name = "SocialEducation"
    if environment_var.qdrant_clean == "yes":
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)
        client.create_collection(collection_name,vectors_config=VectorParams(size=768, distance=Distance.DOT))
    qdrant = Qdrant(client, collection_name, hf)
    print(client.get_collections())

    print("Retrieving stream sources")
    files = get_input_streams(sourcepath)
    file_content = ""
    for file in files:
        file_content = ""
        if file.endswith(".txt"):
            print("indexing " + file)
            f = open(file,'r')
            file_content = f.read()
            f.close()
        elif file.endswith(".pdf"):
            print("indexing "+file)
            reader = PyPDF2.PdfReader(file)
            for i in range(0,len(reader.pages)):
                file_content = file_content + " "+reader.pages[i].extract_text()
        elif file.endswith(".docx"):
            print("indexing " + file)
            file_content = getTextFromWord(file)
        else:
            continue
        token_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
        text_list_tokenized = token_splitter.split_text(file_content)
        metadata = []
        #adding path metadata
        for i in range(0,len(text_list_tokenized)):
            metadata.append({"source":file})
        #adding topic metadata
        for i in range(0,len(text_list_tokenized)):
            metadata.append({"topic":"social subdirectori"})
        #more here??
        qdrant.add_texts(text_list_tokenized,metadatas=metadata)

    #only for debuggin (to be deleted)    
    print(files)
    print("Incremental stream processing processed!")

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments)>1:
        main_indexer(arguments[1])
    else:
        print("Indexing is not possible. Please review input streams")