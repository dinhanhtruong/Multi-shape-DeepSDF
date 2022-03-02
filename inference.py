import tensorflow as tf
import tensorflow.keras as keras
from matplotlib import pyplot
import numpy as np
from deepsdf_model import DeepSDFDecoder
from sdf import sdf3
from train import extract_mesh_from_sdf, visualize_sdf_points
from preprocess import get_mesh_files
from mesh_to_sdf import sample_sdf_near_surface
import trimesh
import pyrender
from sdf import *
from hyperparams import *

# mesh = trimesh.load_mesh('out.stl')
# mesh.show()

model_dir = 'trained_models/scaled_output'
save_dir = 'output/' + 'scaled_output/550_epochs_high' + '.stl'

# load model
model = keras.models.load_model(model_dir)
model.summary()
# try marching cubes
print("extracting")

extract_mesh_from_sdf(0, model, save_dir, occupancy=False, num_samples=2**25) #2**25 HI, 2**22 default
