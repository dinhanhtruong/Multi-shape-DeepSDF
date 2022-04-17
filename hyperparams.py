import torch
from torch import nn

# ====== GLOBAL HYPERPARAMS ===========
epochs = 30
batch_sz = 512

# preprocess/data
num_sample_points_surface = 2**19 #500000
num_sample_points_cloud = 2**19 #500000

# Shape code embedding
num_shapes = 2
shape_code_dim = 128 #256 in paper

# hashtable 
table_sz = 2**19 # num entries per table, [2*14, 2**24]
max_resolution = 2**16 # max grid length sz [2^9=512, 512*1024=524288]

#MLP
hidden_dim = 64 # 512   must be at least shape_code_dim + encoded_pos_dim
MLP_dropout_rate = 0.2
encoded_position_dim = 16*2 #16 = num hashtable levels (fixed), 2=feature dimension of a table entry (fixed)

#training
# weights_learning_rate = 0.001 #1e-5 in DeepSDF paper for model weights, 1e-3 for embedding
# MLP_optimizer = keras.optimizers.Adam(weights_learning_rate, beta_1=0.9, beta_2=0.99, epsilon=10**(-15))
# shape_code_optimizer = keras.optimizers.Adam(shape_code_learning_rate)
# hashtable_optimizer = keras.optimizers.Adam(beta_1=0.9, beta_2=0.99, epsilon=10**(-15))
learning_rate=1e-4
beta_1=0.9
beta_2=0.99
epsilon=10**(-15)
weight_decay=1e-6


loss_fn = nn.L1Loss()