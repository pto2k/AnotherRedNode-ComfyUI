import logging
import folder_paths
import torch
import hashlib
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
register_heif_opener()
import numpy as np

class ReadHEICImage:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "extensions": [".heic"]
                })
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "read_heic_image"
    CATEGORY = "Image Processing"

    def read_heic_image(self, file_path):
        try:
            logging.info(f"Reading HEIC file: {file_path}")
            
            # Open the HEIC file
            image = Image.open(file_path)
            logging.info("Converting HEIC to JPEG...")
            image = image.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            logging.info("Image read and converted successfully.")
            return (image,)
        except Exception as e:
            logging.error(f"Error reading HEIC file: {e}")
            return (None,)
   
# Dictionary to map node class names to their respective classes
NODE_CLASS_MAPPINGS = {
    "ReadHEICImage": ReadHEICImage
}

# Dictionary to map node class names to their display names in the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "ReadHEICImage": "Read HEIC Image"
}
