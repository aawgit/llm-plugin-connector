from datetime import datetime


def get_question_prompt(prompt, api_doc):
    messages = [{
        "role": "user",
        "content": """
        Current date and time is {}
        Host is http://127.0.0.1:5000
        You are a resourceful personal assistant. You are given the below API Documentation:
{}

Using this documentation, send following request data in JSON format for making a request to call for answering the user question.
Use the following as JSON object keys "host", "method", "headers", "parameters", "parameter_location".

You should build the request data object in order to get a response that is as short as possible, while still getting the necessary 
information to answer the question. 
First check if you have all the information to generate the request. If not, ask for them and do not try to 
generate the request data object.
Pay attention to deliberately exclude any unnecessary pieces of data in the response.

Question:{}
Request data:{{
url:
method:
headers:
parameters:
parameter_location: 
}}
""".format(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), api_doc, prompt)

    },
    ]
    return messages


def get_intention_prompt(prompt, plugin_list):
    messages = [{
        "role": "user",
        "content": """This is a list of intentions. 
        {}
        select the matching intention of the following phrase from the above list:
        The phrase: {}
                                                     
        Respond only with the number of the matching option. If there is no match, say 'no match'. 
        Do not return more than one intention.
                                                      """.format(plugin_list, prompt)
    }]
    return messages


def get_user_input_with_context_prompt(user_input, api_response):
    messages = [{
        "role": "user",
        "content": """
        {}
        Answer the following in natural language with the above information. Keep it brief.:
        {}
     """.format(api_response, user_input)
    }]
    return messages
