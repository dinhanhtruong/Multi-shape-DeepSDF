import random
import tensorflow as tf
import tensorflow.keras as keras
import numpy as np
from deepsdf_model import *
from multi_res_hashtable import MultiResolutionHashEncoding
from hyperparams import *
from sdf import sdf3
from preprocess import get_mesh_files
from mesh_to_sdf import sample_sdf_near_surface, mesh_to_sdf
import trimesh
import pyrender
# import mcubes
from sdf import *
import os
# for SDF sampling via SSH
os.environ['DISPLAY'] = ':1'

# ====== TRAINING STEP FOR SINGLE IMAGE ===============
@tf.function
def train_step(shape_idx, positions, sdf_true):
    """Trains the model for a SINGLE shape using the positions given as queries to the SDF
    
    :param shape_idx: 
    :param positions: batch of query positions at which the SDF is queried for training
    :param sdf_true: true SDF values of the shape at positions
    :return: None
    """
    with tf.GradientTape(persistent=True) as tape:
        encoded_positions = hashtable_enc(positions)
        # shape_code = shape_codes(shape_idx)
        # sdf_pred = model([positions, encoded_positions, shape_code], training=True)
        sdf_pred = model(encoded_positions, training=True)
        # print("model: ", sdf_pred.numpy()[:10])
        # print("actual: ", sdf_true[:10])
        loss = model.loss(sdf_pred, sdf_true)
    # print("loss: ", loss)

    # train hashtables entries, model params and latent codes jointly
    hashtable_grads = tape.gradient(loss, hashtable_enc.trainable_variables)
    hashtable_optimizer.apply_gradients(zip(hashtable_grads, hashtable_enc.trainable_variables))
    MLP_grads = tape.gradient(loss, model.trainable_variables)
    MLP_optimizer.apply_gradients(zip(MLP_grads, model.trainable_variables))
    # shape_code_grads = tape.gradient(loss, shape_codes.trainable_variables)
    # shape_code_optimizer.apply_gradients(zip(shape_code_grads, shape_codes.trainable_variables))
    return loss

# ====== MAIN TRAINING LOOP ===============
def train(data_dir, hashtable_save_path, model_save_path, shape_code_save_path):
    

    # get lexicographically ordered filepaths
    shape_filepaths = get_mesh_files(data_dir)
    print(shape_filepaths)
    # temporarily overfit to 1st plane
    shape_idx=1
    filepath = shape_filepaths[shape_idx]
    mesh = trimesh.load(filepath)
    

    # convert to sdf
    # TODO: check for bad mash exceptions? exception can be thrown if < 1.5% of uniformly sampled points have negative SDFs (ie occupied)
    print("resampling")
    positions, sdf_vals = sample_sdf_near_surface(mesh, num_sample_points)
    # query_positions = random_ball(num_sample_points, dimension=3, radius=0.5)
    # rescale points to be in half unit ball (radius=0.5)
    # sdf_vals = mesh_to_sdf(mesh, query_positions)

    # move object to first octant (bounding sphere center at 0.5,0.5,0.5)
    positions = 0.5*positions + 0.5
    
    # visualize_sdf_points(positions, sdf_vals)


    for epoch in range(epochs):
        print("======= epoch: ", epoch)
        
        # =====================================================================================TODO===========================
        
        # convert to occupancy (1 if inside, 0 outside shape)
        # occupancy_vals = np.where(sdf_vals < 0, 1.0, 0.0)
        
        dataset_positions = tf.data.Dataset.from_tensor_slices(positions)
        dataset_sdf = tf.data.Dataset.from_tensor_slices(sdf_vals)
        dataset = tf.data.Dataset.zip((dataset_positions, dataset_sdf)).shuffle(buffer_size=num_sample_points).batch(batch_sz, drop_remainder=True)
        
        # dataset = dataset.shuffle(buffer_size=num_sample_points)
        
        # # pick random shape 
        # shape_idx = random.randint(0,num_shapes-1)
        # print("shape idx: ", shape_idx)
        # filepath = shape_filepaths[shape_idx]
        # mesh = trimesh.load(filepath)

        losses = []
        # batch
        for batch_positions, batch_occupancy_vals in dataset:
            losses.append(train_step(shape_idx, batch_positions, batch_occupancy_vals).numpy())
        print("epoch loss: ", np.mean(losses))

        # if epoch % 3 == 0:
        #     # save model every few epochs
        #     print("saving...")
        #     hashtable_enc.save(hashtable_save_path)
        #     model.save(model_save_path)
        #     # shape_codes.save(shape_code_save_path)
        #     print("saved to: ", model_save_path)
        if epoch % 3 == 2:
            print("saving checkpoint at ", str(epoch), " epochs")
            hashtable_enc.save(hashtable_save_path+"_"+ str(epoch)+"epochs")
            model.save(model_save_path+"_"+ str(epoch)+"epochs")
            # shape_codes.save(shape_code_save_path+"_"+ str(epoch)+"epochs")
            print("saved to: ", model_save_path+"_"+ str(epoch)+"epochs")
        # hashtable_enc.summary()
        # model.summary()
        # shape_codes.summary()
    # extract_mesh_from_sdf(0, model, 'output/out4.stl')

def visualize_sdf_points(points, sdf_vals):
    colors = np.zeros(points.shape)
    colors[sdf_vals < 0, 2] = 1
    colors[sdf_vals > 0, 0] = 1
    cloud = pyrender.Mesh.from_points(points, colors=colors)
    scene = pyrender.Scene()
    scene.add(cloud)
    viewer = pyrender.Viewer(scene, use_raymond_lighting=True, point_size=2)


def random_ball(num_points, dimension, radius=1):
    # First generate random directions by normalizing the length of a
    # vector of random-normal values (these distribute evenly on ball).
    random_directions = np.random.normal(size=(dimension,num_points))
    random_directions /= np.linalg.norm(random_directions, axis=0)
    # Second generate a random radius with probability proportional to
    # the surface area of a ball with a given radius.
    random_radii = np.random.random(num_points) ** (1/dimension)
    # Return the list of random (direction & length) points.
    return radius * (random_directions * random_radii).T

def random_cube_coords(num_points, lower_bound, upper_bound):
    # generate rand points in bounds
    return np.random.uniform(low=lower_bound, high=upper_bound, size=(num_points, 3))


if __name__ == "__main__":
    data_dir = "plane_data"
    trained_model_dir = 'hashtable/base5/2layers_sdf_shifted_2e18res_2e18table'
    save_dir = 'hashtable/base5/2layers_sdf_shifted_2e18res_2e18table'

    trained_model_path = 'trained_models/' + trained_model_dir + '_model'
    trained_shape_code_path = 'trained_models/' + trained_model_dir + '_emb'
    trained_hashtable_path = 'trained_models/' + trained_model_dir + '_table'
    model_save_path = 'trained_models/' + save_dir + '_model'
    shape_code_save_path = 'trained_models/' + save_dir + '_emb'
    hashtable_save_path = 'trained_models/' + save_dir + '_table'

    hashtable_enc = MultiResolutionHashEncoding(table_sz, max_resolution)
    model = DeepSDFDecoder(shape_code_dim, encoded_position_dim, hidden_dim, MLP_dropout_rate)
    shape_codes = ShapeCodeEmbedding(num_shapes, shape_code_dim)

    
    # hashtable_enc = keras.models.load_model(hashtable_save_path)
    # model = keras.models.load_model(model_save_path)
    # shape_codes = keras.models.load_model(shape_code_save_path)

    train(data_dir, hashtable_save_path, model_save_path, shape_code_save_path)
    