import warnings
import google.generativeai as genai
from IPython.display import Image as IPImage, display
from PIL import Image
import time
import os
import cv2
from twilio.rest import Client as TwilioClient

BOLD_BEGIN = "\033[1m"
BOLD_END = "\033[0m"

s1= (
    "You are an advanced AI system specialized in generating detailed, context-rich descriptions of images. "
    "Your task is to analyze the provided image and create a comprehensive narrative that clearly communicates what’s happening in it. "
    "Focus on identifying objects, their relationships, and any significant interactions or activities. Pay attention to the environment, "
    "mood, and the context in which the image is set. The description should include the following:\n"
    "1. **Objects and People**: Identify key elements in the image, including any people, animals, objects, or landmarks. "
    "Mention their appearance, placement, and any noteworthy characteristics.\n"
    "2. **Actions and Interactions**: If applicable, describe what people or objects are doing. Highlight any interactions between individuals "
    "or objects, including movements, gestures, and emotional expressions.\n"
    "3. **Context and Environment**: Provide context about the scene, including the location (e.g., indoors, outdoors), time of day, "
    "weather conditions, and the setting (e.g., home, park, street).\n"
    "4. **Overall Narrative**: Create a clear, coherent story or description that ties all these elements together in a logical flow, "
    "focusing on clarity and precision.\n"
    "Your goal is to provide a description that not only identifies what is in the image but also captures its essence, giving the reader "
    "a vivid understanding of the scene. Ensure the description is informative, engaging, and useful, especially for individuals relying on it "
    "to gain insights into the content."
)

s2 = (
    "You are an advanced AI surveillance analyst. Your task is to analyze images from security cameras and "
    "generate detailed yet concise incident reports. Focus on identifying movements, anomalies, suspicious activities, "
    "and any notable events. Reports should be actionable and prioritize critical observations. Limit your responses "
    "Additionally, based on the urgency and significance of the detected event, assign any one priority level from the following options:\n"
     "- **high_priority**: Critical incidents, such as potential security breaches, unauthorized access, or immediate threats.\n"
    "- **mid_priority**: Notable events that may require attention but are not immediately threatening.\n"
    "- **low_priority**: Minor or inconsequential events that are unlikely to cause harm.\n"
    "to 150 words while ensuring clarity and precision."
    "You do not make descriptions."
)

system_content = s2

api_key = "api_key_here"
model_name = "gemini-1.5-flash-latest"

if not api_key:
    raise ValueError("API_KEY must be set.")

genai.configure(api_key=api_key)

print(f"Using MODEL={model_name}")

class ClientFactory:
    def __init__(self):
        self.clients = {}
    
    def register_client(self, name, client_class):
        self.clients[name] = client_class
    
    def create_client(self, name, **kwargs):
        client_class = self.clients.get(name)
        if client_class:
            return client_class(**kwargs)
        raise ValueError(f"Client '{name}' is not registered.")

client_factory = ClientFactory()
client_factory.register_client('google', genai.GenerativeModel)

client_kwargs = {
    "model_name": model_name,
    "generation_config": {
        "temperature": 0.6,
        "top_p": 0.4
    },
    
    "system_instruction": system_content,
}

client = client_factory.create_client('google', **client_kwargs)

account_sid = 'sid'
auth_token = 'token'
twilio_client = TwilioClient(account_sid, auth_token)

# Twilio phone numbers
from_phone_number = 'num'
to_phone_number = 'num'

def display_image(img_path):
    display(IPImage(filename=img_path))

def process_images_from_directory(directory_path):
    images = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
                images.append(os.path.join(root, file))
    return images



image_directory = "images/"
image_paths= process_images_from_directory(image_directory)

c1 = (
    "You are an AI-powered system tasked with analyzing images and generating detailed, context-rich descriptions. "
    "For each provided image, you should identify the objects, people, and elements present, along with their interactions and relationships. "
    "Focus on the following aspects:\n"
    "1. **Objects and People**: Describe the key elements in the image, including any individuals, animals, objects, or landmarks. "
    "Note their appearance, positions, and any significant details.\n"
    "2. **Actions and Interactions**: If applicable, explain what actions are taking place in the image. Describe any interactions, "
    "movements, or emotional expressions among people or objects.\n"
    "3. **Context and Environment**: Offer insight into the surroundings, including the time of day, location (indoor/outdoor), "
    "weather conditions, and the environment (e.g., a park, street, home).\n"
    "4. **Narrative Summary**: Craft a clear and coherent description that ties all elements together, providing a concise and "
    "engaging overview of the scene.\n"
    "Your goal is to generate a description that is informative, clear, and visually engaging, giving the reader a thorough understanding "
    "of what is happening in the image. Keep the description actionable and insightful."
)

c2 = (
    "You are an AI-powered system tasked with analyzing images and generating detailed, context-rich descriptions. "
    "For each provided image, you should identify the objects, people, and elements present, along with their interactions and relationships. "
    "Focus on the following aspects:\n"
    "1. **Objects and People**: Describe the key elements in the image, including any individuals, animals, objects, or landmarks. "
    "Note their appearance, positions, and any significant details.\n"
    "2. **Actions and Interactions**: If applicable, explain what actions are taking place in the image. Describe any interactions, "
    "movements, or emotional expressions among people or objects.\n"
    "3. **Context and Environment**: Offer insight into the surroundings, including the time of day, location (indoor/outdoor), "
    "weather conditions, and the environment (e.g., a park, street, home).\n"
    "4. **Priority**: Based on the importance of the image content, assign a priority level from the following options:\n"
    "   - **high_priority**: For critical, urgent events or suspicious activities that require immediate attention.\n"
    "   - **mid_priority**: For notable activities or events that may require further review.\n"
    "   - **low_priority**: For less significant, routine activities that do not need immediate attention.\n"
    "5. **Brief Summary**: Provide a brief summary (about 10 words) of the key events taking place in the image. This summary should "
    "highlight the most important action or event in a concise manner.\n"
    "Your goal is to generate a description that is informative, clear, and visually engaging, giving the reader a thorough understanding "
    "of what is happening in the image. Focus on providing a single priority level based on the significance of the event or activity."
)


user_content = c2

# Security level settings
security_level = "high"  # Options: "high", "mid", "low"

# Function to send message
def send_message(body):
    message = twilio_client.messages.create(
        body=body,
        from_=from_phone_number,
        to=to_phone_number
    )
    print(f"Message sent: {body}")

# Function to make a call
def make_call():
    call = twilio_client.calls.create(
        to=to_phone_number,
        from_=from_phone_number,
        url='http://demo.twilio.com/docs/voice.xml'
    )
    print("Call initiated.")
    

i=0

for image_path in image_paths: 
    try:
        img = Image.open(image_path)
        display_image(image_path)

        response = client.generate_content([c1, img], stream=True)
        response.resolve()
        
        description = response.text
        priority_tag = "low_priority"  # Default tag
        if "high_priority" in description:
            priority_tag = "high_priority"
        elif "mid_priority" in description:
            priority_tag = "mid_priority"
        elif "low_priority" in description:
            priority_tag = "low_priority"
        print(f"{BOLD_BEGIN}Image description:{BOLD_END} {response.text}\n")
        if priority_tag == "high_priority":
            if security_level == "high":
                send_message("High priority incident detected!")
                make_call()
            elif security_level == "mid":
                send_message("High priority incident detected!")
            elif security_level == "low":
                send_message("High priority incident detected!")
        
        elif priority_tag == "mid_priority":
            if security_level == "high":
                send_message("Mid priority incident detected!")
            elif security_level == "mid":
                send_message("Mid priority incident detected!")
        
        elif priority_tag == "low_priority":
            if security_level == "high":
                send_message("Low priority incident detected!")
        i += 1
        if i % 3 == 0:
            time.sleep(30)

    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
