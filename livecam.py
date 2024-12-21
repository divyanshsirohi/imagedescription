import warnings
import google.generativeai as genai
from IPython.display import Image as IPImage, display
from PIL import Image
from time import time, sleep
import os
import pafy
import cv2
import io
from PIL import Image
from yt_dlp import YoutubeDL
from twilio.rest import Client as TwilioClient

os.environ["PAFY_BACKEND"] = "internal"

BOLD_BEGIN = "\033[1m"
BOLD_END = "\033[0m"

s1= (
    "You are an advanced AI system specialized in generating detailed, context-rich descriptions of images. "
    "Your task is to analyze the provided image and create a comprehensive narrative that clearly communicates what’s happening in it. "
    "Focus on identifying objects, their relationships, and any significant interactions or activities. Pay attention to the environment, "
    "mood, and the context in which the image is set. The description should include the following:\n"
    "1. tObjects and People: Identify key elements in the image, including any people, animals, objects, or landmarks. "
    "Mention their appearance, placement, and any noteworthy characteristics.\n"
    "2. Actions and Interactions: If applicable, describe what people or objects are doing. Highlight any interactions between individuals "
    "or objects, including movements, gestures, and emotional expressions.\n"
    "3. Context and Environment: Provide context about the scene, including the location (e.g., indoors, outdoors), time of day, "
    "weather conditions, and the setting (e.g., home, park, street).\n"
    "4. Overall Narrative: Create a clear, coherent story or description that ties all these elements together in a logical flow, "
    "focusing on clarity and precision.\n"
    "do not give me any sort of priority here"
    "Your goal is to provide a description that not only identifies what is in the image but also captures its essence, giving the reader "
    "a vivid understanding of the scene. Ensure the description is informative, engaging, and useful, especially for individuals relying on it "
    "to gain insights into the content."
)

s2 = (
    "You are an advanced AI surveillance analyst. Your task is to analyze images from security cameras and "
    "generate detailed yet concise incident reports. Focus on identifying movements, anomalies, suspicious activities, "
    "and any notable events. Reports should be actionable and prioritize critical observations. Limit your responses "
    "Additionally, based on the urgency and significance of the detected event, assign any one priority level from the following options:\n"
     "- high_priority: Critical incidents, such as potential security breaches, unauthorized access, or immediate threats.\n"
    "- mid_priority: Notable events that may require attention but are not immediately threatening.\n"
    "- low_priority: Minor or inconsequential events that are unlikely to cause harm.\n"
    "to 150 words while ensuring clarity and precision."
    "You do not make descriptions."
)

system_content = s2

api_key = ""
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
        "temperature": 0.45,
        "top_p": 0.7
    },
    
    "system_instruction": system_content,
}

client = client_factory.create_client('google', **client_kwargs)

account_sid = ''
auth_token = ''
twilio_client = TwilioClient(account_sid, auth_token)

# Twilio phone numbers
from_phone_number = ''
to_phone_number = ''

def display_image(img_path):
    display(IPImage(filename=img_path))

def process_media_from_directory(directory_path):
    media_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif', 'mp4', 'avi', 'mov', 'mkv')):
                media_files.append(os.path.join(root, file))
    return media_files

def frame_to_image_bytes(frame):
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    byte_array = io.BytesIO()
    pil_image.save(byte_array, format="JPEG")
    return byte_array.getvalue()

def extract_frames_from_video(video_path):
    frames = []
    cap = cv2.VideoCapture(video_path)
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = max(1, frame_rate // 2)  # Extract 2 frames per second
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = f"temp_frame_{frame_count}.jpg"
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)

        frame_count += 1

    cap.release()
    return frames

media_directory = "images/"
media_files = process_media_from_directory(media_directory)

c1 = (
    "You are an AI-powered system tasked with analyzing images and generating detailed, context-rich descriptions. "
    "For each provided image, you should identify the objects, people, and elements present, along with their interactions and relationships. "
    "Focus on the following aspects:\n"
    "1. Objects and People: Describe the key elements in the image, including any individuals, animals, objects, or landmarks. "
    "Note their appearance, positions, and any significant details.\n"
    "2. Actions and Interactions: If applicable, explain what actions are taking place in the image. Describe any interactions, "
    "movements, or emotional expressions among people or objects.\n"
    "3. Context and Environment: Offer insight into the surroundings, including the time of day, location (indoor/outdoor), "
    "weather conditions, and the environment (e.g., a park, street, home).\n"
    "4. Narrative Summary: Craft a clear and coherent description that ties all elements together, providing a concise and "
    "engaging overview of the scene.\n"
    "Your goal is to generate a description that is informative, clear, and visually engaging, giving the reader a thorough understanding "
    "of what is happening in the image. Keep the description actionable and insightful."
)

c2 = (
    "You are an AI-powered system tasked with analyzing images and generating detailed, context-rich descriptions. "
    "For each provided image, you should identify the objects, people, and elements present, along with their interactions and relationships. "
    "Focus on the following aspects:\n"
    "1. Objects and People: Describe the key elements in the image, including any individuals, animals, objects, or landmarks. "
    "Note their appearance, positions, and any significant details. If the image quality is low, mention the reduced visibility or clarity but still provide as much detail as possible.\n"
    "2. Actions and Interactions: If applicable, explain what actions are taking place in the image. Describe any interactions, "
    "movements, or emotional expressions among people or objects. If the image is blurry or unclear, note that the lack of clarity may hinder interpretation, but identify any visible elements.\n"
    "3. Context and Environment: Offer insight into the surroundings, including the time of day, location (indoor/outdoor), "
    "weather conditions, and the environment (e.g., a park, street, home). If the image quality hinders recognition of the context, mention this limitation and focus on any identifiable features.\n"
    "4. Priority: Based on the importance of the image content, assign a priority level from the following options:\n"
    "   - high_priority: For critical, urgent events or suspicious activities that require immediate attention.\n"
    "   - mid_priority: For notable activities or events that may require further review.\n"
    "   - low_priority: For less significant, routine activities that do not need immediate attention. If the image is of low quality but involves potential concerns, err on the side of caution and assign the appropriate priority.\n"
    "5. Brief Summary: Provide a brief summary (about 10 words) of the key events taking place in the image. This summary should "
    "highlight the most important action or event in a concise manner, even if the image quality is low.\n"
    "Your goal is to generate a description that is informative, clear, and visually engaging, giving the reader a thorough understanding without pointing out what could be done to improve the image"
    "of what is happening in the image. Even for low-quality images, focus on extracting useful details while acknowledging any limitations due to poor image clarity."
)


user_content = c2

# Security level settings
security_level = "low"  # Options: "high", "mid", "low"

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

# Ensure the output directory exists
OUTPUT_DIR = "live_stream_frames"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Function to save frame as an image file
def save_frame_to_folder(frame, frame_index):
    file_path = os.path.join(OUTPUT_DIR, f"frame_{frame_index}.png")
    cv2.imwrite(file_path, frame)
    return file_path

# Function to get stream URL from YouTube live video URL
def get_stream_url(youtube_live_url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_live_url, download=False)
            print(f"Stream URL: {info['url']}")  # Debug print to check stream URL
            return info['url']
    except Exception as e:
        print(f"Error fetching stream URL: {str(e)}")
        return None

# Function to process live video, save frames, and describe
def process_live_video(youtube_live_url, user_content, security_level="high", c2="c2"):
    stream_url = get_stream_url(youtube_live_url)
    if not stream_url:
        print("Error: Unable to retrieve stream URL.")
        return

    # Open video stream
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        return

    frame_count = 0
    last_captured_time = time()

    while cap.isOpened():
        current_time = time()

        # Capture one frame every 2 seconds
        if current_time - last_captured_time >= 2:
            last_captured_time = current_time

            # Force frame position update
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)

            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            try:
                # Save frame to folder
                frame_path = save_frame_to_folder(frame, frame_count)
                print(f"Saved frame {frame_count} to {frame_path}")

                # Open saved image with PIL
                img = Image.open(frame_path)

                # Send to Gemini API
                response = client.generate_content([user_content, img], stream=True)
                response.resolve()

                # Extract description from the response
                description = response.text
                print(f"Description for frame {frame_count}: {description}")

                # Determine priority tag
                priority_tag = "low_priority"
                if "high_priority" in description:
                    priority_tag = "high_priority"
                elif "mid_priority" in description:
                    priority_tag = "mid_priority"
                elif "low_priority" in description:
                    priority_tag = "low_priority"

                # Act based on priority and security level
                if user_content == c2:
                    if priority_tag == "high_priority":
                        if security_level == "high":
                            send_message("High priority incident detected!")
                            make_call()
                        elif security_level == "mid":
                            send_message("High priority incident detected!")
                        elif security_level == "low":
                            send_message("High priority incident detected!")

                    elif priority_tag == "mid_priority":
                        if security_level in ["high", "mid"]:
                            send_message("Mid priority incident detected!")

                    elif priority_tag == "low_priority" and security_level == "high":
                        send_message("Low priority incident detected!")

                frame_count += 1

            except Exception as e:
                print(f"Error processing frame {frame_count}: {str(e)}")

    cap.release()
    cv2.destroyAllWindows()

process_live_video(
    "https://www.youtube.com/watch?v=z7SiAaN4ogw",
    user_content="c2",
    security_level="high"
)
