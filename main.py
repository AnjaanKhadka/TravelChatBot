import ChatBot
import streamlit as st

# result = DocsChat.query("What is the attention mechanism?")

# print(result)


st.title("Travel Chat Bot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask a question"):
    with st.chat_message("user"):
        st.write(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    
    response = ChatBot.query(prompt)
    
    with st.chat_message("assistant"):
        st.write(response)
        
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    
