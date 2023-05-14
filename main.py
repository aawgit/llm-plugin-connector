# This does the following
# 1. Load the given plugins
#       - Read the plugin services /.well-known/ai-plugin.json, get the details and hold in the memory
# 2. When a user enters a prompt, first checks if it's related to task done by a plugin, and if so insert the plugin
# context to the message and send to the LLM
# 3. When the LLM respond includes a request to the a plugin, send the request and send the data back to the LLM with the original? prompt
# 4. When the LLM responds with the answer, return it to the user

import openai
import json
import urllib.request
import re
import collections
import requests
import logging
import os

from prompts import get_question_prompt, get_intention_prompt, get_user_input_with_context_prompt
from utils import extract_outermost

openai.api_key = os.getenv('OPEN_AI_API_KEY')


def get_plugin_info(hosts):
    all_info = []
    for host in hosts:
        url = host + '/.well-known/ai-plugin.json'
        with urllib.request.urlopen(url) as response:
            data = response.read()

        json_data = json.loads(data.decode('utf-8'))
        api_doc_url = json_data.get('api').get('url')
        with urllib.request.urlopen(api_doc_url) as response:
            data = response.read()
        json_data["api_doc"] = data
        all_info.append(json_data)
    return all_info


def init_plugins(plugin_hosts):
    plugin_info_list = get_plugin_info(plugin_hosts)
    api_docs = {}
    purposes = ""
    for idx, plugin_info in enumerate(plugin_info_list):
        desc = plugin_info.get("description_for_model")
        # TODO: Consider summarizing
        insensitive_plugin = re.compile(re.escape('plugin'), re.IGNORECASE)
        desc = insensitive_plugin.sub('', desc)
        purposes = purposes + "{}. {}\n".format(idx, desc)

        api_docs[idx] = plugin_info.get("api_doc")

    return purposes, api_docs


def ask_llm(messages, model="gpt-3.5-turbo", history=None):
    if history is None:
        history = []
    history.extend(messages)
    try:
        completion = openai.ChatCompletion.create(model=model,
                                                  messages=list(history))
        res = completion.choices[0].message.content
        history.append({"role": "assistant", "content": res})
        return res
    except Exception as e:
        print(e)


def extract_request_data(string):
    result = extract_outermost(string)
    request_data = json.loads("{" + result + "}")
    return request_data


def invoke_api(request_data):
    try:
        method = request_data.get('method')
        url = request_data.get('url')
        headers = request_data.get('headers')
        if method is None or url is None:
            raise Exception('Failed to generate the plugin API call')
        if method == 'GET':
            params = request_data.get('parameters')
            data = {}
        elif method == 'POST':
            params = None
            data = request_data.get('parameters')
        else:
            raise Exception('Not implemented')
        # make the request
        response = requests.request(method=method, url=url, headers=headers, params=params, data=json.dumps(data))

        # check response status code
        if response.status_code >= 200 and response.status_code < 300:
            # return JSON response if successful (with text encoding)
            return json.loads(response.content.decode('utf-8'))
        else:
            # raise an exception if unsuccessful (with error message)
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # raise an exception if connection error (with error message)
        raise e


def run_console(purposes, api_docs):
    history = collections.deque(maxlen=5)
    while True:
        user_input = input("Please enter your input ('q' to exit): ")
        if user_input.lower() == 'q':
            break
        else:
            try:
                print("Human: " + user_input)
                intention = ask_llm(get_intention_prompt(user_input, purposes))
                plugin_index = intention.strip("").split(".", 1)[0]
                if plugin_index.isdigit():
                    # User request is related to a plugin.
                    api_doc = api_docs.get(int(plugin_index))
                    answer = ask_llm(get_question_prompt(user_input, api_doc), history=history)
                    req_data = extract_request_data(answer)
                    logging.debug("Machine: {}".format(answer))
                    ans = invoke_api(req_data)
                    if req_data.get('method') == 'GET':
                        ans = ask_llm(get_user_input_with_context_prompt(user_input, ans))
                    print("Machine: {} \n".format(ans))
                else:
                    messages = [{"role": "user", "content": """{}""".format(user_input)}]
                    answer = ask_llm(messages, history=history)
                    print("Machine: " + answer + '\n')
            except Exception as e:
                logging.error(e)


if __name__ == '__main__':
    plugin_hosts = ["http://127.0.0.1:5000"]
    plugin_purposes, plugin_apis = init_plugins(plugin_hosts)
    run_console(plugin_purposes, plugin_apis)
