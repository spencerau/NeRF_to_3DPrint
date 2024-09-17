import bpy
import os
import dotenv
import sys
import math
#import argparse
import glob
import random
from mathutils import Vector


# load environment variables
dotenv.load_dotenv()
EXPORT_DIR = os.getenv("EXPORT_DIR")
MODEL_DIR = os.getenv("MODEL_DIR")
MODEL_NAME = os.getenv("MODEL_NAME")

NUM_IMAGES = int(os.getenv("NUM_IMAGES"))
IMAGE_RES_V = int(os.getenv("IMAGE_RESOLUTION_V"))
IMAGE_RES_H = int(os.getenv("IMAGE_RESOLUTION_H"))

FOCAL_LENGTH = float(os.getenv("FOCAL_LENGTH"))
CAMERA_DISTANCE = float(os.getenv("CAMERA_DISTANCE"))



def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.outliner.orphans_purge()

    # Set background to transparent
    bpy.context.scene.render.film_transparent = True


# def import_model(model_path):
#     file_extension = os.path.splitext(model_path)[1].lower()
    
#     if file_extension == ".blend":
#         bpy.ops.wm.open_mainfile(filepath=model_path)
#         # Print all objects to debug
#         print("Objects in the scene after loading the blend file:")
#         for obj in bpy.context.scene.objects:
#             print(obj.name)
#         obj = bpy.context.view_layer.objects.active
#         if obj is None:
#             print("No active object found after loading the blend file. Exiting.")
#             sys.exit(1)
#     else:
#         if file_extension == ".obj":
#             bpy.ops.import_scene.obj(filepath=model_path)
#         elif file_extension == ".fbx":
#             bpy.ops.import_scene.fbx(filepath=model_path)
#         elif file_extension in [".dae", ".gltf", ".glb"]:
#             bpy.ops.import_scene.gltf(filepath=model_path)
#         else:
#             print(f"Unsupported file format: {file_extension}")
#             sys.exit(1)

#         # Explicitly select all objects and set the active object
#         imported_objects = bpy.context.selected_objects
#         if imported_objects:
#             obj = imported_objects[0]
#             for obj in imported_objects:
#                 obj.select_set(True)
#             bpy.context.view_layer.objects.active = imported_objects[0]
#         else:
#             print("No objects selected after import. Exiting.")
#             sys.exit(1)

#     bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='BOUNDS')
#     obj.location = (0, 0, 0)
    
#     return obj


def import_model(model_path):
    file_extension = os.path.splitext(model_path)[1].lower()
    
    if file_extension == ".blend":
        bpy.ops.wm.open_mainfile(filepath=model_path)
        obj = bpy.context.selected_objects[0]
    elif file_extension == ".obj":
        bpy.ops.import_scene.obj(filepath=model_path)
    elif file_extension == ".fbx":
        bpy.ops.import_scene.fbx(filepath=model_path)
    elif file_extension in [".dae", ".gltf", ".glb"]:
        bpy.ops.import_scene.gltf(filepath=model_path)
    else:
        print(f"Unsupported file format: {file_extension}")
        sys.exit(1)
    
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='BOUNDS')
    obj.location = (0, 0, 0)
    
    return obj


def add_lights():
    # Sun light
    bpy.ops.object.light_add(type='SUN', align='WORLD', location=(10, -10, 10))
    sun = bpy.context.object
    sun.data.energy = 20 

    # Overhead point light
    bpy.ops.object.light_add(type='POINT', align='WORLD', location=(0, 0, 10))
    point = bpy.context.object
    point.data.energy = 1500

    # Area light to the side
    bpy.ops.object.light_add(type='AREA', align='WORLD', location=(5, 5, 5))
    area = bpy.context.object
    area.data.energy = 1000
    area.data.size = 10

    # Additional point light to the left
    bpy.ops.object.light_add(type='POINT', align='WORLD', location=(-5, -5, 5))
    point2 = bpy.context.object
    point2.data.energy = 1000 

    # Additional point light to the right
    bpy.ops.object.light_add(type='POINT', align='WORLD', location=(5, -5, 5))
    point3 = bpy.context.object
    point3.data.energy = 1000 

    # Additional point light from the front
    bpy.ops.object.light_add(type='POINT', align='WORLD', location=(0, -10, 5))
    point4 = bpy.context.object
    point4.data.energy = 1000

    # Additional point light from the back
    bpy.ops.object.light_add(type='POINT', align='WORLD', location=(0, 10, 5))
    point5 = bpy.context.object
    point5.data.energy = 1000


def apply_textures(obj, texture_dir):
    texture_types = ["albedo", "diffuse", "color", "normal", "roughness", "metallic", "emissive", "ao", "ambient_occlusion", "opacity", "alpha"]

    for mat_slot in obj.material_slots:
        if mat_slot.material:
            mat = mat_slot.material
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")

            if not bsdf:
                continue

            for tex_type in texture_types:
                tex_files = glob.glob(os.path.join(texture_dir, f"*{tex_type}*"))
                if tex_files:
                    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    tex_image.image = bpy.data.images.load(tex_files[0])  # Load the first matching file
                    if tex_type in ['normal']:
                        normal_map = mat.node_tree.nodes.new('ShaderNodeNormalMap')
                        mat.node_tree.links.new(normal_map.inputs['Color'], tex_image.outputs['Color'])
                        mat.node_tree.links.new(bsdf.inputs['Normal'], normal_map.outputs['Normal'])
                    elif tex_type in ['ao', 'ambient_occlusion']:
                        # No direct slot for ambient occlusion in Principled BSDF
                        # Connect to Base Color for illustration purposes
                        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
                    elif tex_type in ['opacity', 'alpha']:
                        mat.blend_method = 'CLIP'
                        mat.node_tree.links.new(bsdf.inputs['Alpha'], tex_image.outputs['Color'])
                    else:
                        mat.node_tree.links.new(bsdf.inputs[tex_type.capitalize()], tex_image.outputs['Color'])


def add_camera(model):
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.context.scene.camera = camera

    # Set the camera location directly
    #camera.location = (7.3589, -6.92579, 4.95831)
    
    # Set the camera rotation directly
    #camera.rotation_euler = (63.5593, 0, 46.692)
    #camera.rotation_euler = (math.radians(63.559), 0, math.radians(46.692))

    # Add Track To constraint to keep the camera focused on the model
    track_to_constraint = camera.constraints.new(type='TRACK_TO')
    track_to_constraint.target = model
    track_to_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    track_to_constraint.up_axis = 'UP_Y'

    # Adjust the focal length 
    camera.data.lens = FOCAL_LENGTH

    # Debugging prints
    print(f"Camera location: {camera.location}")
    print(f"Camera rotation: {camera.rotation_euler}")

    return camera


def render_images(output_dir, camera, model, total_images):
    def update_camera_position(camera, model, h_angle, v_angle, distance, z_offset):
        bbox_corners = [model.matrix_world @ Vector(corner) for corner in model.bound_box]
        bbox_center = sum((Vector(b) for b in bbox_corners), Vector()) / 8
        
        # Calculate new camera position based on spherical coordinates
        x = bbox_center.x + distance * math.cos(math.radians(v_angle)) * math.cos(math.radians(h_angle))
        y = bbox_center.y + distance * math.cos(math.radians(v_angle)) * math.sin(math.radians(h_angle))
        z = bbox_center.z + distance * math.sin(math.radians(v_angle)) + z_offset
        
        camera.location = (x, y, z)

        # Point the camera towards the object center
        direction = bbox_center - camera.location
        rot_quat = direction.to_track_quat('Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()

    distance = CAMERA_DISTANCE  # Distance of the camera from the model
    index = 0

    h_angle = 0
    v_angle = 0

    # Define the vertical angle range (e.g., 0° to 80°)
    vertical_angle_range = 80

    # Calculate the number of vertical and horizontal steps
    vertical_step_count = math.ceil(math.sqrt(NUM_IMAGES))  # e.g., 6
    horizontal_step_count = math.ceil(NUM_IMAGES / vertical_step_count)  # e.g., 5

    # Calculate the step size for vertical and horizontal movements
    vertical_step = vertical_angle_range / (vertical_step_count - 1)
    horizontal_step = 360 / horizontal_step_count

    print(f"VERTICAL STEP: {vertical_step}") 
    print(f"HORIZONTAL STEP: {horizontal_step}") 

    # horizontal_step = 15
    # vertical_step = 15

    # Set output format to PNG with RGBA
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    
    bpy.context.scene.render.resolution_x = IMAGE_RES_H
    bpy.context.scene.render.resolution_y = IMAGE_RES_V

    z_offset = 0.5

    while index < total_images:
        update_camera_position(camera, model, h_angle, v_angle, distance, z_offset)
        bpy.context.view_layer.update()
        output_path = os.path.join(output_dir, f'r_{index:d}.png')
        bpy.context.scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        index += 1

        # Move horizontally
        h_angle += horizontal_step
        if h_angle >= 360:  # Completed a full horizontal circle
            h_angle -= 360  # Reset horizontal angle
            v_angle += vertical_step  # Move up vertically

            # Ensure the vertical angle stays within a reasonable range and below 90 degrees
            if v_angle > 80:
                break 


def main():
    # args parser is deprecated
    # args = sys.argv
    # args = args[args.index("--") + 1:]
    
    # model_path = args[args.index("--model") + 1]
    # texture_dir = args[args.index("--textures") + 1] if "--textures" in args else None
    # total_images = int(args[args.index("--total_images") + 1]) if "--total_images" in args else 100

    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    base_output_dir = os.path.join(EXPORT_DIR)
    output_dir = os.path.join(base_output_dir, MODEL_NAME.split(".")[0], "images")

    os.makedirs(output_dir, exist_ok=True)
    clear_scene()

    model = import_model(model_path)
    if model:
        add_lights()
        camera = add_camera(model)
        render_images(output_dir, camera, model, NUM_IMAGES)
    else:
        print("Model could not be imported. Exiting.")


if __name__ == '__main__':
    main()

