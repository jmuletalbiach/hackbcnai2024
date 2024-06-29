
import uvicorn

#inicialization of start_backend
if __name__=="__main__":
    uvicorn.run("api_ollama:app",host='0.0.0.0', port=8000, reload=False,  workers=3)