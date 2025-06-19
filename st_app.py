# st_app.py
import streamlit as st
import os
import shutil
import boto3
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_cohere import ChatCohere
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# AWS S3 config
S3_BUCKET = "wiki12"
S3_REGION = "us-east-1"
s3_client = boto3.client("s3", region_name=S3_REGION)

def upload_to_s3(file_path, s3_key):
    s3_client.upload_file(file_path, S3_BUCKET, s3_key)

def delete_from_s3(s3_key):
    s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

# Vector DB setup
vector_space_dir = os.path.join(os.getcwd(), "vector_db")
os.makedirs(vector_space_dir, exist_ok=True)

st.set_page_config(page_title="Wikipedia RAG ChatBot", layout="centered")
st.title("Wikipedia RAG ChatBot (LangChain + Cohere)")

if 'vectorstore' not in st.session_state:
    st.session_state['vectorstore'] = None
if 'memory' not in st.session_state:
    st.session_state['memory'] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
if 'retriever' not in st.session_state:
    st.session_state['retriever'] = None

# User input
first_name = st.text_input("Enter First Name")
last_name = st.text_input("Enter Last Name (optional)")

# Run scraper
from wiki_scraper.scraper import run_scraper  # Import scraper function

if st.button("Fetch Wikipedia & Create Chatbot"):
    if not first_name:
        st.warning("Please enter at least a first name.")
    else:
        person_name = f"{first_name} {last_name}".strip()
        file_name = f"{person_name.replace(' ', '_')}_output.txt"

        st.info(f"Scraping Wikipedia for: {person_name}")
        with st.spinner("Running Scraper..."):
            try:
                run_scraper(person_name)
                if os.path.exists(file_name):
                    loader = TextLoader(file_name, encoding="utf-8")
                    documents = loader.load()
                    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                    vectorstore = FAISS.from_documents(documents, embedding_model)
                    vectorstore.save_local(vector_space_dir)
                    st.session_state['vectorstore'] = vectorstore
                    st.session_state['retriever'] = vectorstore.as_retriever(search_kwargs={"k": 10})
                    upload_to_s3(file_name, file_name)
                    st.session_state['s3_file_name'] = file_name
                    os.remove(file_name)
                    st.success("Wikipedia content loaded and chatbot initialized!")
                else:
                    st.error("No content file found after scraping.")
            except Exception as e:
                st.error(f"Scraper failed: {e}")

# Use Cohere API from Streamlit secrets
os.environ["COHERE_API_KEY"] = st.secrets["COHERE_API_KEY"]
llm = ChatCohere(model="command-r-plus", temperature=0)

prompt_template = PromptTemplate.from_template(
    "Answer the following question based on the context.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
)

if st.session_state['retriever'] is not None:
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=st.session_state['retriever'],
        memory=st.session_state['memory'],
        combine_docs_chain_kwargs={"prompt": prompt_template},
        return_source_documents=False
    )
    user_question = st.text_input("Ask a question about the person:", key='user_question')
    if user_question:
        with st.spinner("Thinking..."):
            person_name = f"{first_name} {last_name}".strip()
            full_question = f"Tell me, based on the information about {person_name}, {user_question}"
            response = qa_chain.invoke({"question": full_question})
            st.markdown(f"**You:** {user_question}")
            st.markdown(f"**Bot:** {response['answer']}")

def clear_vector_db(path):
    if os.path.exists(path):
        shutil.rmtree(path)

if st.button("Clear Chatbot"):
    st.session_state['memory'].clear()
    st.session_state['retriever'] = None
    st.session_state['vectorstore'] = None
    clear_vector_db(vector_space_dir)
    if 's3_file_name' in st.session_state:
        try:
            delete_from_s3(st.session_state['s3_file_name'])
            st.success(f"Deleted {st.session_state['s3_file_name']} from AWS S3.")
        except Exception as e:
            st.warning(f"Failed to delete file from S3: {e}")
        del st.session_state['s3_file_name']
    for key in ['user_question', 'upload_txt']:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Chatbot and memory cleared.")
    st.rerun()
