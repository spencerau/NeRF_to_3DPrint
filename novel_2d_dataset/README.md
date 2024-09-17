#  NeRF Novel 2D Dataset
 Create a novel 2d dataset for Neural Radiance Field model training from a 3d model using bpy (Blender)

## .env file setup
EXPORT_DIR = "dataset"  
MODEL_DIR = "dataset/3d_models"  
MODEL_NAME = "portal_gun.glb"  

NUM_IMAGES = "50"  
IMAGE_RESOLUTION_V = "1080"  
IMAGE_RESOLUTION_H = "1920"  

FOCAL_LENGTH = "50"  
CAMERA_DISTANCE = "350"  

## Requirements
- python-dotenv installed within the Blender python environment
- Example Command for MacOS and Blender 3.6: `/Applications/Blender.app/Contents/Resources/3.6/python/bin/python3.10 -m ensurepip && /Applications/Blender.app/Contents/Resources/3.6/python/bin/python3.10 -m pip install python-dotenv`

## Usage

1. Create a .env file with the above setup

2. Example Command for MacOS: `python render_wrapper.py --blender /Applications/Blender.app/Contents/MacOS/Blender`
