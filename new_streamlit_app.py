import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from typing import List, Dict, Any
import json
from pydantic import BaseModel
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from typing import List
from pprint import pprint
import os
os.environ["AZURE_OPENAI_API_KEY"] = '1dfeeaf8f4e945e5a461f82fd08169b3'
from openai import AzureOpenAI

client = AzureOpenAI(
    api_version="2023-07-01-preview",
    azure_endpoint="https://disprz-originals.openai.azure.com/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"]
)

if 'page' not in st.session_state:
    st.session_state.page = 'page1'
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'dbPointer' not in st.session_state:
    st.session_state.dbPointer = ''
if 'journey_desc' not in st.session_state:
    st.session_state['journey_desc'] = ""

def go_to_page2():
    st.session_state.page = 'page2'
    st.rerun()

def go_to_page1():
    st.session_state.page = 'page1'
    st.rerun()

class journeyitems(BaseModel):
    providerContentId: str = Field(..., alias='providerContentId', description='providerContentId')
    Title: str = Field(..., alias='Title', description='Title of the chosen item')
    Description: str = Field(..., alias='Description', description='Description of the chosen item')
    duration: str = Field(..., alias='duration', description='duration of the chosen item')
    content_type: str = Field(..., alias='content_type', description='content_type of the chosen item')
    reason: str = Field(..., alias='reason', description='reason why the item was chosen')

class ExtractedInfo(BaseModel):
    journey: List[journeyitems] = Field(..., description='Give the learning journey in sequence of contents')

def searchapi(accessToken, skillName, duration, language, content_type, artefact_type, provider_type):
    searchApiUrl = 'https://searchservice-msvc-india.disprz.com/v1/trainer-search/learning-items'
    
    headers = {
        'Content-Type': 'application/json',  
        'Access-Token': accessToken  
    }

    language_filter = {
        "fieldName":"language_codes",
            "options":[
                ],
                "searchTerm":"",
                "isTruncated":False
    }
    for language_f in language:
        if language_f == 'en':
            language_option={"count":0,"from":0,"to":0,"type":"normal","label":"English (UK)","value":"en"}
        elif language_f == 'ar':
            language_option={"count":0,"from":0,"to":0,"type":"normal","label":"Arabic (العربية)","value":"ar"}
        elif language_f == 'bh-ind':
            language_option={"count":0,"from":0,"to":0,"type":"normal","label":"Bahasa Indonesia","value":"bh-ind"}
        language_filter['options'].append(language_option)


    duration_filter={
            "fieldName":"duration_in_sec",
            "options":[
                ],
                "searchTerm":"",
                "isTruncated":False
            }
    for duration_f in duration:
        if duration_f == '1200 - 0':
            duration_option={"count":0,"from":1200,"to":0,"type":"range","label":"Long 20+ mins","value":"1200 - 0"}
        elif duration_f == '240 - 1200':
            duration_option={"count":0,"from":240,"to":1200,"type":"range","label":"Medium 4-20mins","value":"240 - 1200"}
        elif duration_f == '0-240':
            duration_option={"count":0,"from":0,"to":240,"type":"normal","label":"Short 0-4mins","value":"0-240"}
        duration_filter['options'].append(duration_option)
    

    artefact_filter={
        "fieldName":"content_type.keyword",
        "options":[
            ]
            }
    for artefact_f in artefact_type:
        if artefact_f == 'article':
            artefact_option={"count":0,"from":0,"to":0,"type":"normal","label":"article","value":"article"}
        elif artefact_f == 'podcast':
            artefact_option={"count":0,"from":0,"to":0,"type":"normal","label":"podcast","value":"podcast"}
        elif artefact_f == 'video':
            artefact_option={"count":0,"from":0,"to":0,"type":"normal","label":"video","value":"video"}
        artefact_filter['options'].append(artefact_option)

    if len(content_type)==1:
        if content_type[0]=='artifact':
            type_content = {
            "fieldName":"type",
            "options":[
                {
                "type":"normal",
                 "label":"Artifacts",
                 "value":"artifact"
                 }
                ],
                "searchTerm":"",
                "isTruncated":False
            }
        elif content_type[0]=='module':
            type_content = {
            "fieldName":"type",
            "options":[
                {
                "type":"normal",
                 "label":"modules",
                 "value":"module"
                 }
                ],
                "searchTerm":"",
                "isTruncated":False
            }
    provider_filter={
        "fieldName":"provider_name.keyword",
        "options":[
            ]
            }
    for provider_f in provider_type:
        if provider_f == 'linkedin':
            provider_option={"count": 14, "from": 0, "to": 0, "type": "normal", "label": "linkedin", "value": "linkedin"}
        provider_filter['options'].append(provider_option)

    data = {
        "term":skillName,
        "size":50,
        "skip":0,
        "sortDirection":"asc",
        "includeFacets":True,
        "sortBy":"relevance",
        "filters":
        []
        }
    if len(language_filter['options']) >=1:
        data['filters'].append(language_filter)
    if len(duration_filter['options']) >=1:
        data['filters'].append(duration_filter)
    if len(content_type)==1:
        data['filters'].append(type_content)
    if len(artefact_filter['options']) >=1:
        data['filters'].append(artefact_filter)
    if len(provider_filter['options']) >=1:
        data['filters'].append(provider_filter)
    
    response = requests.post(searchApiUrl, headers=headers, json=data)

    if response.status_code == 200:
        data=(response.json()['hits'])
        filtered_data = []
        for item in data:
            description = item.get("description", None)
            removedOn = item.get("removedOn", None)
            if removedOn is None:
                filtered_data.append({
                    "id": item["id"],
                    "name": item["name"],
                    "description": description,
                    "duration": item["duration"],
                    "providerName": item["providerName"],
                    "content_type": item['type']
                })

        json_data = json.dumps(filtered_data, indent=4)
        # with open("search_results.json", "w") as outfile:
        #     outfile.write(json_data)
        return json_data
    else:
        print(f'Error: {response.status_code} - {response.text}')


def get_completion(context, prompt):
    messages = [{"role":"system", "content": context},{"role":"user" ,"content":prompt}]
    response = client.chat.completions.create(model="GPT4o",messages=messages,temperature=0.5,functions=[
                {
                    "name": "Learning_Journey_Curator",
                    "parameters": ExtractedInfo.model_json_schema()
                }
            ],
        function_call={"name":"Learning_Journey_Curator"})
    return response.choices[0].message.function_call.arguments

def get_completion_desc(context, prompt):
    messages = [{"role":"system", "content": context},{"role":"user" ,"content":prompt}]
    response = client.chat.completions.create(model="GPT4o",messages=messages,temperature=0.5)
    return response.choices[0].message.content

def page1():
    st.title("AI-Powered Learning Journey Curator")
    dbPointer = st.text_input("Enter the DbPointer:", value=st.session_state.dbPointer)
    username = st.text_input("Enter the UserName:", value=st.session_state.username)
    if st.button("Submit"):
        # db_pointer = "DepartmentofFin1"
        url = f"https://disprzexternalapi.disprz.com/api/user-authentication/clients/{dbPointer}/users/by-username/{username}"

        headers = {
            'Content-Type': 'application/json',
            'API-ACCESS-KEY': '36yyyty0Cg3vsodwEv3ecg=='
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            st.session_state.username = username
            st.session_state.accessToken = response.json()['accessToken']
            go_to_page2()
        else:
            st.error('Invalid Username or DbPointer, Please try again', icon="🚨")

def page2():
    st.title('AI-Powered Learning Journey Curator')

    if 'form_data' not in st.session_state:
        st.session_state.form_data = None
    if 'final_jour_dict' not in st.session_state:
        st.session_state.final_jour_dict = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'excel_file' not in st.session_state:
        st.session_state.excel_file = None

    with st.form(key='query_form'):
        st.subheader("Learning Journey Details")
        skill_name = st.text_input("Skill Name / Topic Name", "")
        length = st.number_input("Length of Learning Journeys", min_value=1)
        
        duration_options = {
            "Long 20+ mins": "1200 - 0",
            "Medium 4-20 mins": "240 - 1200",
            "Short 0-4 mins": "0-240"
        }
        content_type_options = {
            "Artefact": "artifact",
            "Module": "module"
        }
        language_options = {
            "English": "en",
            "Arabic": "ar",
            "Bahasa Indonesia": "bh-ind"
        }
        artefact_type_options = {
            "Article": "article",
            "Podcast": "podcast",
            "Video": "video"
        }
        provider_type_options = {
            "Linkedin": "linkedin"
        }

        duration = st.multiselect(
            "Duration of each item (mins)",
            options=list(duration_options.keys())
        )
        
        content_type = st.multiselect(
            "Content Type",
            options=list(content_type_options.keys())
        )
        
        language = st.multiselect(
            "Language",
            options=list(language_options.keys())
        )
        
        artefact_type = st.multiselect(
            "Artefact Type",
            options=list(artefact_type_options.keys())
        )
        provider_type = st.multiselect(
            "Provider Type (use only when Linkedin Learning is required)",
            options=list(provider_type_options.keys())
        )

        designation = st.text_input("Designation")
        industry = st.text_input("Industry")
        
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            # Convert selected options to their corresponding values
            selected_durations = [duration_options[opt] for opt in duration]
            selected_content_types = [content_type_options[opt] for opt in content_type]
            selected_languages = [language_options[opt] for opt in language]
            selected_artefact_types = [artefact_type_options[opt] for opt in artefact_type]
            selected_provider_types = [provider_type_options[opt] for opt in provider_type]
            # st.session_state.form_data = {
            #     "skill_name": skill_name,
            #     "length": length,
            #     "duration": selected_durations,
            #     "content_type": selected_content_types,
            #     "language": selected_languages,
            #     "artefact_type": selected_artefact_types,
            #     "Designation": designation,
            #     "Industry": industry,
            #     "InstanceURL": instance_url
            # }
            # headers = {
            #         'accessToken': st.session_state.accessToken
            #     }
            json_data=searchapi(st.session_state.accessToken, skill_name, selected_durations, selected_languages, selected_content_types, selected_artefact_types, selected_provider_types)
            length=str(length)
            Designation = str(designation)
            Industry = str(industry)
            prompt="Give me the learning journey"
            if Designation and Industry:
                print("Trying with Designation and Industry inputs")
                context= """
                            Create a journey consisting of {length} learning modules from the content library provided below, delimited by ###, for the skill {skill_name} aligned to the '{Designation}' designation working in the '{Industry}' industry. 
                            Strictly follow these rules:
                            1. Parse through the entire content library in JSON format (from first to last) and select only content from the provided content library.
                            2. Ensure that the content is actually relevant to the skill {skill_name}, {Designation} designation and {Industry} industry. Sometimes the content library has irrelevant content. Include only content that is highly and directly relevant to the skill in the journey.
                            3. Provide a good progression of learning content.
                            4. Shuffle and pick the learning content; do not give content exactly in the order it appears in the content library.
                            5. The learning journey should have a good mix of content from all the content providers in the ContentLibrary.
                            6. Ensure you do not return content with the same title names in the journey.
                            7. Ensure that you pick {length} different modules. Do not return duplicate content even if they have different content IDs. If {length} highly relevant content modules are not available, then you can return fewer.
                            8. If none of the content in the content library matches the skill {skill_name}, {Designation} designation and {Industry} industry return null.
                            9. Do not hallucinate and provide random courses that are not present in the content library.
                            10. The response should strictly be in this format: [{{"providerContentId": , "Title": , "Description": , "duration": , "content_type": , "reason": }}]. Do not return any additional text.
                            
                            ### 
                            {json_data}
                            ###
                        """
                context_formatted=context.format(length=length, skill_name=skill_name, Designation=Designation, Industry=Industry, json_data=json_data)
            elif Designation:
                print("Trying with Designation input")
                context="""
                            Create a journey consisting of {length} learning modules from the content library provided below, delimited by ###, for the skill {skill_name} aligned to the '{Designation}' designation. 
                            Strictly follow these rules:
                            1. Parse through the entire content library in JSON format (from first to last) and select only content from the provided content library.
                            2. Ensure that the content is actually relevant to the skill {skill_name} and {Designation} designation. Sometimes the content library has irrelevant content. Include only content that is highly and directly relevant to the skill in the journey.
                            3. Provide a good progression of learning content.
                            4. Shuffle and pick the learning content; do not give content exactly in the order it appears in the content library.
                            5. The learning journey should have a good mix of content from all the content providers in the ContentLibrary.
                            6. Ensure you do not return content with the same title names in the journey.
                            7. Ensure that you pick {length} different modules. Do not return duplicate content even if they have different content IDs. If {length} highly relevant content modules are not available, then you can return fewer.
                            8. If none of the content in the content library matches the skill {skill_name} and {Designation} designation, return null.
                            9. Do not hallucinate and provide random courses that are not present in the content library.
                            10. The response should strictly be in this format: [{{"providerContentId": , "Title": , "Description": , "duration": , "content_type": , "reason": }}]. Do not return any additional text.

                            ### 
                            {json_data}
                            ###
                        """
                context_formatted=context.format(length=length, skill_name=skill_name, Designation=Designation, json_data=json_data)
            elif Industry:
                print("Trying with Industry input")
                context="""
                            Create a journey consisting of {length} learning modules from the content library provided below, delimited by ###, for the skill {skill_name} targeted in the '{Industry}' industry. 
                            Strictly follow these rules:
                            1. Parse through the entire content library in JSON format (from first to last) and select only content from the provided content library.
                            2. Ensure that the content is actually relevant to the skill {skill_name}. Sometimes the content library has irrelevant content. Include only content that is highly and directly relevant to the skill in the journey.
                            3. Provide a good progression of learning content.
                            4. Shuffle and pick the learning content; do not give content exactly in the order it appears in the content library.
                            5. The learning journey should have a good mix of content from the ContentLibrary.
                            6. Ensure you do not return content with the same title names in the journey.
                            7. Ensure that you pick {length} different modules. Do not return duplicate content even if they have different content IDs. If {length} highly relevant content modules are not available, then you can return fewer.
                            8. If none of the content in the content library matches the skill {skill_name}, return null.
                            9. Do not hallucinate and provide random courses that are not present in the content library.
                            10. The response should strictly be in this format: [{{"providerContentId": , "Title": , "Description": , "duration": ,"content_type", "reason": }}]. Do not return any additional text.
                            
                            ###
                            {json_data}
                            ###
                        """
                context_formatted=context.format(length=length, skill_name=skill_name, Industry=Industry, json_data=json_data)
            else:
                print("Trying with neither industry or designation input")
                context="""
                            Create a journey consisting of {length} learning modules from the content library provided below, delimited by ###, for the skill {skill_name}. 
                            Strictly follow these rules:
                            1. Parse through the entire content library in JSON format (from first to last) and select only content from the provided content library.
                            2. Ensure that the content is actually relevant to the skill {skill_name}. Sometimes the content library has irrelevant content. Include only content that is highly and directly relevant to the skill in the journey.
                            3. Provide a good progression of learning content.
                            4. Shuffle and pick the learning content; do not give content exactly in the order it appears in the content library.
                            5. The learning journey should have a good mix of content from the ContentLibrary.
                            6. Ensure you do not return content with the same title names in the journey.
                            7. Ensure that you pick {length} different modules. Do not return duplicate content even if they have different content IDs. If {length} highly relevant content modules are not available, then you can return fewer.
                            8. If none of the content in the content library matches the skill {skill_name}, return null.
                            9. Do not hallucinate and provide random courses that are not present in the content library.
                            10. The response should strictly be in this format: [{{"providerContentId": , "Title": , "Description": , "duration": , "content_type": , "reason": }}]. Do not return any additional text.

                            ###
                            {json_data}
                            ###
                        """
                context_formatted=context.format(length=length, skill_name=skill_name, json_data=json_data)
            final_jour=get_completion(context_formatted,prompt)
            print(final_jour)
            journey = json.loads(final_jour)
            if journey:
                st.session_state.final_jour_dict = journey['journey']
                df = pd.DataFrame(st.session_state.final_jour_dict)
                df['duration'] = df['duration'].astype(int)
                df['Duration (mins)'] = df['duration'].apply(lambda x: round(x / 60, 2))
                df['Description'] = df['Description'].apply(lambda x: x[:170] + '...' if len(x) > 170 else x)
                total_minutes = df['Duration (mins)'].sum()
                hours, minutes = divmod(total_minutes, 60)

                st.write(f"Your Learning Journey consists of {len(df)} items and the total learning duration is {int(hours)} hours and {int(minutes)} minutes.")
                
                # Display DataFrame as table
                st.dataframe(df[['providerContentId', 'Title', 'Description', 'Duration (mins)', 'reason']])
                
                # Create Excel file
                excel_file = BytesIO()
                with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Learning Journey')
                
                # Reset file pointer to the beginning
                excel_file.seek(0)
                
                # Store the Excel file in session state
                st.session_state.excel_file = excel_file.getvalue()
            else:
                st.error('Internal error occured', icon="🚨")

    # Display download button outside of the form
    if st.session_state.excel_file:
        st.download_button(
            label="Download as Excel",
            data=st.session_state.excel_file,
            file_name="LearningJourneyData.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.warning("No file available to download.")

    #Form to publish journey
    with st.form(key='publish_form'):
        st.subheader("Publish")
        journey_name = st.text_input("Journey Name", "")
        # journey_desc = st.text_area("Journey Description", st.session_state['journey_desc'], height=150)
        generate_description = st.form_submit_button(label='Generate Journey Description')
        if generate_description:
            context = f'''The learning journey suggested by GPT for the topic - "{skill_name}" for a user working as - "Manager" in "Finance" Industry is provided below delimited by ###. Provide a description in about 50-65 words for the users to understand about the learning journey before they start learning it based on the learning journey provided, Suggest the description based on the reason key in learning journey json, the reason was suggested by GPT when suggesting a learning journey, the output should be in this format - [{{"description": description}}]. Do not return any additional text. This is the learning journey ### {st.session_state.final_jour_dict}'''
            prompt = "Provide the description"
            response=get_completion_desc(context,prompt)
            response_list = json.loads(response)  # Convert string to a list
            description = response_list[0]['description']
            st.session_state['journey_desc'] = description
            st.text_area("Journey Description", st.session_state['journey_desc'], height=150)
        publish_button = st.form_submit_button(label='Publish as Journey')

        if publish_button:
            if st.session_state.access_token is None:
                st.error("Access Token is not available. Please submit the form first.")
            else:
                request_data = {
                    "accessToken": st.session_state.access_token,
                    "Journey_Name": journey_name,
                    "contentIdList": [item['providerContentId'] for item in st.session_state.final_jour_dict]
                }
                publish_response = requests.post('https://searchservice-msvc-india.disprz.com/v1/trainer-search/learning-items/publish', json=request_data)
                if publish_response.status_code == 200:
                    st.success(f"Learning Journey {publish_response.json()['message']}")
                else:
                    st.error(f"Error: {publish_response.text}")

if st.session_state.page == 'page1':
    page1()
else:
    page2()