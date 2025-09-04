from .ChatBot import ChatBot


chat_bot = ChatBot()

def query(question =None):
    print(question)
    return chat_bot.conversational_Query(query=question)



