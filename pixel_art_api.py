from dotenv import load_dotenv
import os
import PIL
import requests

from transformers import pipeline
from openai import OpenAI

# Load api keys
load_dotenv()

"""
This is the main api.
Input: PIL Image
Output: 
   Valid Input (picture has a cat): Original PIL Image, New PIL Image
   Invalid input (picture has no cat): Return False
"""
def img2img(original_image_path, user_id):
   # First convert to PIL Image for processing
   original_image = PIL.Image.open(original_image_path)

   # First get a caption of the original image
   caption = img2text(original_image)
   print(caption)

   # If the image does not contain a cat, exit and return False
   if (not check_if_cat(caption)):
      return False, None, None
   
   # Else use the text prompt to create a pixel-art avatar
   new_image_url = text2img(f"make a cute 8-bit render of this cat {caption}").data[0].url
   new_image = download_image(new_image_url).resize((512, 512))
   new_image.save("Photo/8bit-" + user_id + ".png")
   return True, original_image, new_image

"""Module for captioning the image"""
def img2text(img):
   image_to_text = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
   text = image_to_text(img)[0]["generated_text"]
   return text

"""Module for converting the caption to pixel art"""
def text2img(text_prompt):
   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   response = client.images.generate(
      model="dall-e-3",
      prompt=text_prompt,
      size="1024x1024",
      quality="standard",
      n=1,
   )
   return response

"""
These are just some utility functions.
"""
def check_if_cat(prompt): # Check if the prompt includes a cat (and by proxy the original image)
   if "cat" in prompt or "kitten" in prompt:
      print("has cat")
      return True
   return False

def download_image(url): # Download an image from a given URL
    image = PIL.Image.open(requests.get(url, stream=True).raw)
    image = PIL.ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    return image