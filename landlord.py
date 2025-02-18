import time
import os
import streamlit as st
import google.generativeai as genai
import typing_extensions as typing
from dotenv import load_dotenv


load_dotenv()
my_api_key = os.getenv('GOOGLE_API_KEY')


genai.configure(api_key=my_api_key)


instruction = """
You are a LetAFlat chatbot, a virtual realtor that helps to create rental ads for houses and apartments in Ukraine and Poland.
Your goal is to find out the main characteristics of the property and what the rental conditions are. 
Do not perform any tasks other than those of a realtor helping lanlords.
This means that if the user asks questions that are not related to the apartment for rent, do not answer them.

Do not say hello if you have already said hello.

In the beginning ask the questions, user must answer:


1. Location
Say that for now only Lviv available. (!!!Save this in settings!!!). Just inform the user.
Ask about the address of the property. User must enter the district, street, and house number. 
**This question is required. So if the user has not answered the question, ask again until he/she does.
**Should follow house number pattern, i.e 116/7, 22B, etc.

2. Apartment characteristics
2.1. Ask how many rooms there are in the apartment (min 1, max 5).
**This question is required. So if the user has not answered the question, ask again until he/she does.

2.2. Ask about the floor where the apartment is located (min 1st, max 20th floor)
**This question is required. So if the user has not answered the question, ask again until he/she does.

3. Available period
Ask when the apartment will be available. The value can not be in the past.
**This question is required. So if the user has not answered the question, ask again until he/she does.

4. Additional characteristics.
Ask whether there are any additional features in the user's apartment: shelter, furniture, autonomous power source, fiber optic, etc. 
**It's okay if the user do not answer any questions from part 4. In such case, move to the next question.


5. Price & Payment
Ask the user what kind of payment they expect. Also ask if the price includes utilities and guarantee. 
Ask again, if you need required attributes:
- Monthly rental payment (UAH) (min 5000, max 60 000) **required
- If utilities are included into the monthly payment 
- Average monthly utilities bill
- Guarantee payment amount (UAH) (min 0, max 60 000) **required

6.
Ask the user whether it is okay if students, or childern, or pets live in the apartment.
(Pet-friendliness, child-friendliness, student-friendliness)
Ask again to clarify (if there is a nacessarity).
**It's okay if the user has no such prefferences and didn't answer any questions from part 6. In such case, move to the next question.

7. End of the conversation
Say user thank you for his/her time and say that they would find the accomodation which suits the best.
Conclude and structure information, your receive from user.

P.S. Take into account the information you already receive, so you do not need to ask the question if it is not necessarily.


After function calling just say to user smth like "Okay, thank you for your time. We noted everything and start to search for the apartment which best suits you"

"""


class Settings(typing.TypedDict):
    city: str
    district: str
    street: str
    house_number: str
    rooms_number: int
    floor: int
    available_from: str #datetime #.date
    renovation_state: str
    has_furniture: bool
    has_autonomous_light: bool
    has_autonomous_internet: bool
    has_shelter: bool
    rental_payment: int
    utilities_included: bool
    utilities_bill: int
    guarantee_payment: int
    pets_friendly: bool
    child_friendly: bool
    students_friendly: bool


def save_settings():
    """
    Function to conclude the conversation.
    Call it whenever the user has aswered all questionns and there is all necessary info.
    If user did not give clear answer, save that answer, do not create anything else.
    """
    prompt = f"""From the chat history (conversation between chat-bot and user) extract \
necessary information:
{st.session_state.chat_history}


**The required attributes (you must find information about them in conversation): 
city, district, street, house_number, rooms_number, floor, available_from, rental_payment, guarantee_payment,
pets_friendly, child_friendly
You must provide these attributes.

**If the user didn't provide corresponding information, do not save the null values in the output."""
    print('START OF FUNCTION CALLING')

    model_1 = genai.GenerativeModel("gemini-1.5-flash")
    result = model_1.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", response_schema=list[Settings]
        ),
    )

    print('RESULT OF FUNCTION CALLING')

    if result.candidates:
        generated_text = result.candidates[0].content.parts[0].text

    else:
        generated_text = ""


    with open("settings.txt", "w", encoding="utf-8") as text:
        text.write(generated_text)

    # return generated_text

def typing_effect(text, container):
    """
    Function for typing effect
    """
    output = ""
    for char in text:
        output += char
        container.markdown(output)
        time.sleep(0.02)  # Adjust speed of typing here


model = genai.GenerativeModel("gemini-1.5-flash",
                                    system_instruction=instruction,
                                    tools=[save_settings]
                                    )

chat = model.start_chat(enable_automatic_function_calling=True)


if "chat_end" not in st.session_state:
    st.session_state.chat_end = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chat_history_model" not in st.session_state:
    st.session_state.chat_history_model = []
    greetings = "Hello! I'm LetAFlat chat-bot. I'm here to help you \
to promote your apartment for rent."
    st.session_state.chat_history.append({"role": "assistant",
                                                "content": greetings})
    chat.history = st.session_state.chat_history_model

st.title("LetAFlat")


for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def run_chat():
    if not st.session_state.chat_end:
        chat.history = st.session_state.chat_history_model
        user_input = st.chat_input("Say something")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            response = chat.send_message(
                user_input
            )
            with st.chat_message("assistant"):
                assistant_placeholder = st.empty()
                typing_effect(response.candidates[0].content.parts[0].text, assistant_placeholder)
                st.session_state.chat_history.append({"role": "assistant",
                                                      "content":
                                                      response.candidates[0].content.parts[0].text})

        st.session_state.chat_history_model = chat.history


run_chat()
