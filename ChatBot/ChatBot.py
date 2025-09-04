
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
import requests

safety_settings = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}


class collectable_info(BaseModel):
    name: str = Field(description="Name of the user.")
    location: str = Field(description="Location where user is at.")
    is_weather_request: bool = Field(description="True if user is queries about weather at the location.")

def get_api():
    with open("API_KEY.txt", "r") as f:
        google_api_key = f.read().strip()
    with open("WEATHER_API_KEY.txt") as f2:
        weather_api_key = f2.read().strip()
    
    # print(google_api_key, weather_api_key)
    return google_api_key, weather_api_key

def load_model(api_key):
    # global model
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=api_key,safety_settings=safety_settings)
    return model


class ChatBot:
    def __init__(self):
        self.name = ""
        self.location = ""
        self.api_key, self.weather_api_key = get_api()
        self.model = load_model(api_key=self.api_key)

        self.weather_base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.loc_url = "http://api.openweathermap.org/geo/1.0/direct"


    def get_weather_info(self, location):
        # try:
            params = {
                "q": location,
                "appid": self.weather_api_key,
            }
            response = requests.get(self.loc_url, params=params)
            lat, lon =  response.json()[0].get('lat'), response.json()[0].get('lon')
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.weather_api_key,
            }
            response = requests.get(self.weather_base_url, params=params)
            # print(response.json())
            return response.json()
    
        # except requests.exceptions.RequestException as e:
        #     return False



    def information_extractor(self, query):
        template = '''
You are an information extraction AI. 
Your sole purpose is to analyze the user query and extract information from the user.

Currently available informations: 
name:{name}
location:{location}

{format_instructions}

If no new information is provided, use the existing information.
user query: {query}
'''
        
        parser = JsonOutputParser(pydantic_object=collectable_info)
    
        template = template.format(
            query=query,
            format_instructions=parser.get_format_instructions(),
            name = self.name,
            location = self.location,
        )
        response = self.model.invoke(template,safety_settings=safety_settings)
        result = response.content
        # print(result)

        
        result = parser.parse(result)

        self.name = result.get('name') if len(result.get('name','')) > 0 else self.name
        self.location = result.get('location') if len(result.get('location',"")) > 0 else self.location
        print(f"Current info name = {self.name}, location = {self.location}")
        if result.get('is_weather_request'):
            return True
        else:
            return False


    def conversational_Query(self,query):

        is_weather = self.information_extractor(query)


        template = '''
{name_prompt}

You are a conversational Assistant AI.

You have following roles:
- Answer the query from user and make small conversations.
- Help find sites based on user provided location.
- Provide Weather info based on the provided response

{location_prompt}  

user query: {query}
    '''

        name_prompt = ""
        if self.name:
            name_prompt = f"You can address user with the name {self.name}"
        
        loc_prompt = ""
        if self.location:
            loc_prompt = f"User is refering to the location {self.location} in the query."
        
            if is_weather:
                weather_info = self.get_weather_info(self.location)

                
                print(weather_info)
                if weather_info:
                    loc_prompt = '''User is refering to the weather of {location} in the query.
                    
                    Live weather info at the location is:
                    {weather_info}
                    
                    '''
                    loc_prompt = loc_prompt.format(
                        location=self.location,
                        weather_info=weather_info,
                    )


        template = template.format(
            name_prompt=name_prompt,
            location_prompt=loc_prompt,
            query=query,
        )

        response = self.model.invoke(template,safety_settings=safety_settings)      
        return response.content
        
