import base64
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()

def generate_answer(query, messages=None):
    """
    Translates the OpenAI function to LangChain using OpenAI's GPT models.

    Args:
        query (str): The question to be answered.
        messages (list): A list of previous messages as dictionaries with "role" and "content".

    Returns:
        str: The assistant's answer.
    """
    if messages is None:
        messages = []

    # Define the system prompt
    system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
    Use only the information from the context to answer the question.
    If you can't find relevant information in the context, say so."""

    # Initialize the LangChain OpenAI chat model
    chat = ChatOpenAI(model="gpt-4o", temperature=0.9)

    # Convert messages to LangChain's format
    formatted_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted_messages.append(AIMessage(content=msg["content"]))

    # Add the new user query
    formatted_messages.append(HumanMessage(content=f"Question: {query}"))

    # Call the OpenAI model and get the response
    response = chat.invoke(formatted_messages)

    return response.content

def generate_multimodal_answer(query, image_path, messages=None, temperature=0.9, api_key=None, model="gpt-4o-mini"):
    if messages is None:
        messages = []

    # Use provided API key if available and not empty, otherwise use default from env
    if api_key and api_key.strip():
        chat = ChatOpenAI(api_key=api_key, model=model, temperature=temperature)
    else:
        chat = ChatOpenAI(model=model, temperature=temperature)  # Uses default API key from env

    # Define the system prompt
    system_prompt = """You are a multi-modal assistant that answers questions based on the provided context. 
    Use the information from the context and the provided image to answer the question.
    If you can't find relevant information in the context, say so."""

    # Convert messages to LangChain's format
    formatted_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted_messages.append(SystemMessage(content=msg["content"]))

    ## Add the new query
    #formatted_messages.append(HumanMessage(content=query))

    # Encode the image in base64
    with open(image_path, "rb") as img_file:
        image_bytes = base64.b64encode(img_file.read()).decode("utf-8")

    prompt = HumanMessage(content=[
            {"type": "text", "text": query},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_bytes}"
                },
            },
        ])


    formatted_messages.append(prompt)

    # Call the multi-modal model
    response = chat.invoke(formatted_messages)

    return response.content