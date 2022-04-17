from hyperparams import *
import torch
from torch import nn

class MultiResolutionHashEncoding(nn.Module):
    def __init__(self, table_sz=2**14, max_resolution=512, feature_dim=2):
        super(MultiResolutionHashEncoding, self).__init__()

        self.feature_dim = feature_dim
        self.min_resolution = 16
        self.max_resolution = max_resolution
        self.table_sz = table_sz
        

        self.table1 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table1.weight, -10**-4, 10**-4)
        self.table2 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table2.weight, -10**-4, 10**-4)
        self.table3 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table3.weight, -10**-4, 10**-4)
        self.table4 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table4.weight, -10**-4, 10**-4)
        self.table5 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table5.weight, -10**-4, 10**-4)
        self.table6 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table6.weight, -10**-4, 10**-4)
        self.table7 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table7.weight, -10**-4, 10**-4)
        self.table8 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table8.weight, -10**-4, 10**-4)
        self.table9 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table9.weight, -10**-4, 10**-4)
        self.table10 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table10.weight, -10**-4, 10**-4)
        self.table11 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table11.weight, -10**-4, 10**-4)
        self.table12 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table12.weight, -10**-4, 10**-4)
        self.table13 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table13.weight, -10**-4, 10**-4)
        self.table14 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table14.weight, -10**-4, 10**-4)
        self.table15 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table15.weight, -10**-4, 10**-4)
        self.table16 = nn.Embedding(table_sz, feature_dim)
        nn.init.uniform_(self.table16.weight, -10**-4, 10**-4)

        # list of above tables/embeddings to be iterated over
        self.hashtables = [self.table1, self.table2, self.table3, self.table4, self.table5, self.table6, 
        self.table7, self.table8, self.table9, self.table10,
        self.table11, self.table12, self.table13, self.table14, self.table15, self.table16]

        # num tables = fixed = 16
        self.num_levels = len(self.hashtables)

    def forward(self, x):
        '''
        Args:
            x: batch of normalized 3D coordinates between 0 and 1, [B, 3]
        Returns:
            Occupancy probability for each input, [B,]
        '''
        #TODO: append shape code to final input vec

        # get scaling factor for resolution 
        # max_res = tf.cast(self.max_resolution, tf.float32)
        # min_res = tf.cast(self.min_resolution, tf.float32)
        # b = tf.exp((tf.math.log(max_res) - tf.math.log(min_res)) / (self.num_levels-1)) #in [1.38, 2]
        b=1.38

        # for each res, find current voxel, hash corner indices, trilinearly interpolate features
        final_feature_list = []
        

        for curr_level, table in enumerate(self.hashtables):
            curr_resolution = torch.floor(torch.tensor(self.min_resolution * b**curr_level))
            verts = self.get_nearest_vertices_coords(x, curr_resolution) # [B, 8,3] = x/y/z for each of the 8 vertices
            hashed_feats = self.get_hashtable_features(verts, table) # [B,8,feat_dim]

            interpolated_feat = self.get_interpolated_feature(x, hashed_feats)  # [B,feat_dim] single interp feat per batch
            # concatenate current resolution's feature to final feature vec
            final_feature_list.append(interpolated_feat) # [B, current+feat_dim]

        return torch.cat(final_feature_list, dim=1) # [B, num_levels*feat_dim]
        
    def get_nearest_vertices_coords(self, unscaled_position, curr_resolution):
        ''' Gets the integer coordinates of the vertices of the bounding cube containing the position

        Args:
            unscaled_position: unit position with coordinates between 0 and 1, [B, 3]
            curr_resolution: scalar between min and max resolution
        Returns:
            integer coordinates of the bounding cube at the scale level determined by curr_resolution, [B, 8, 3],
            in counterclockwise and z-ascending order starting at the vertex nearest to the origin.
        '''
        # each vertex is a combination (triple) of floor/ceil(position_x), floor/ceil(pos_y), floor/ceil(pos_z)
        scaled_pos = curr_resolution*unscaled_position # [B,3]
        # get integer coordinates of opposite extrema of cube containing the position
        x_low, y_low, z_low = torch.split(torch.floor(scaled_pos).int(), split_size_or_sections=1, dim=1) ## [B,3] -> 3*[B,1]
        x_high, y_high, z_high = torch.split(torch.ceil(scaled_pos).int(), split_size_or_sections=1, dim=1) 
        # return vertices in clockwise order (about z-axis), starting with the first four along the z_low plane then moving up to the four on z_high 
        # along each plane, start at vertex nearest to the origin (x_low, y_low, z_low)
        v0 = torch.cat([x_low, y_low, z_low], dim=1) #[B,3]
        v1 = torch.cat([x_high, y_low, z_low], dim=1)
        v2 = torch.cat([x_high, y_high, z_low], dim=1)
        v3 = torch.cat([x_low, y_high, z_low], dim=1)
        # alotorch.catplane
        v4 = torch.cat([x_low, y_low, z_high], dim=1)
        v5 = torch.cat([x_high, y_low, z_high], dim=1)
        v6 = torch.cat([x_high, y_high, z_high], dim=1)
        v7 = torch.cat([x_low, y_high, z_high], dim=1)
        return torch.stack([v0,v1,v2,v3,v4,v5,v6,v7], dim=1) #[B,8,3]

    def get_hashtable_features(self, vertices, table):
        '''Indexes the given embedding table using indices given by a spatial hash function applied to the vertex coordinates.

        Args:
            vertices: integer coordinates of a (scaled) cude, [B, 8, 3]. Should be returned from get_nearest_vertices_coords
            table: Embedding layer to be indexed into
        Returns:
            features retrieved at the hashed coordinates, [B, 8, feat_dim]
        '''

        x, y, z = torch.unbind(vertices, dim=2) # [B, 8, 3] -> 3*[B,8]
        # apply xor to each x_i*prime 
        # a XOR b XOR c
        a = x
        b = 2654435761 * y
        c = 805459861 * z
        a_xor_b = torch.bitwise_xor(a, b)
        xor_product = torch.bitwise_xor(a_xor_b, c) # shapge unchanged
        # xor_product % T
        indices = torch.remainder(xor_product, self.table_sz) # [B, 8], one per vertex

        return table(indices) #[B, 8, feat], one per vertex

    def get_interpolated_feature(self, position, features):
        '''Given the 8 features corresponding to cube vertices, estimates the feature at position
        via trilinear interpolation. 
        
        Args:
            position: query position between 0 and 1, [B, 3]
            features: tensor of features stored at each vertex of the cube in the 
                order specified by get_nearest_vertices_coords(), [B,8,feat_dim]
        Returns:
            interpolated feature, [B, feat_dim]
        '''
        # get interpolation weights (one for each dim); between 0 and 1
        # lower interpolation weight == position is closer to vertex of cube nearest the origin
        interp_weights = position - torch.floor(position) # [B,3]
        x_weight, y_weight, z_weight = torch.split(interp_weights, split_size_or_sections=1, dim=1) # [B,3] -> 3*[B,1]
        v0,v1,v2,v3,v4,v5,v6,v7 = torch.unbind(features, dim=1) # [B,8,feat_dim] -> 8*[B, feat]
        # interpolate along x-axis along a plane defined by 4 points (check wikipedia article, "Method" section)
        c00 = v0*(1-x_weight) + v1*x_weight
        c01 = v4*(1-x_weight) + v5*x_weight
        c10 = v3*(1-x_weight) + v2*x_weight
        c11 = v7*(1-x_weight) + v6*x_weight

        # bilinearly inteprolate along y-axis restricted to the previous plane (i.e. along plane parallel to y-axis)
        c0 = c00*(1-y_weight) + c10*y_weight
        c1 = c01*(1-y_weight) + c11*y_weight
        # 1D linear interp 
        return c0*(1-z_weight) + c1*z_weight

# #=======TESTING ============

# model = MultiResolutionHashEncoding()
# x = [
#     [0.1, 0.5, 0.9],
#     [0.3, 0.35, 0.71]
# ]
# x = tf.convert_to_tensor(x)
# print(model(x))



# def get_nearest_vertices_coords(unscaled_position, curr_resolution):
#     # since corner coordinates are integers, get every floor/ceil triplet of x's coords (each triplet = corner)
#     # each vertex is a combination (triple) of floor/ceil(position_x), floor/ceil(pos_y), floor/ceil(pos_z)
#     scaled_pos = curr_resolution*unscaled_position # [B,3]
#     # get integer coordinates of opposite extrema of cube containing the position
#     x_low, y_low, z_low = torch.split(tf.cast(tf.math.floor(scaled_pos), dtype=tf.int32), num_or_size_splits=3, axis=1) ## [B,3] -> 3*[B,1]
#     x_high, y_high, z_high = torch.split(tf.cast(tf.math.ceil(scaled_pos), dtype=tf.int32), num_or_size_splits=3, axis=1) 
#     # return vertices in clockwise order (about z-axis), starting with the first four along the z_low plane then moving up to the four on z_high 
#     # along each plane, start at vertex nearest to the origin (x_low, y_low, z_low)
#     v0 = tf.concat([x_low, y_low, z_low], axis=1) #[B,3]
#     v1 = tf.concat([x_high, y_low, z_low], axis=1)
#     v2 = tf.concat([x_high, y_high, z_low], axis=1)
#     v3 = tf.concat([x_low, y_high, z_low], axis=1)
#     # along upper plane
#     v4 = tf.concat([x_low, y_low, z_high], axis=1)
#     v5 = tf.concat([x_high, y_low, z_high], axis=1)
#     v6 = tf.concat([x_high, y_high, z_high], axis=1)
#     v7 = tf.concat([x_low, y_high, z_high], axis=1)
#     return tf.stack([v0,v1,v2,v3,v4,v5,v6,v7], axis=1) #[B,8,3]

# def get_hashtable_features(vertices, table):
#         '''Indexes the given embedding table using indices given by a spatial hash function applied to the vertex coordinates.

#         Args:
#             vertices: integer coordinates of a (scaled) cude, [B, 8, 3]. Should be returned from get_nearest_vertices_coords
#             table: Embedding layer to be indexed into
#         Returns:
#             features retrieved at the hashed coordinates, [B, 8, feat_dim]
#         '''
#         x, y, z = tf.unstack(vertices,  num=3, axis=2) # [B, 8, 3] -> 3*[B,8]

#         print("x: ", x.shape)
#         # apply xor to each x_i*prime 
#         # a XOR b XOR c
#         a = x
#         b = 2654435761 * y
#         c = 805459861 * z
#         a_xor_b = tf.bitwise.bitwise_xor(a, b)
#         xor_product = tf.bitwise.bitwise_xor(a_xor_b, c) # shape unchanged
#         # xor_product % T
#         indices = tf.math.floormod(xor_product, 2**14) # [B, 8], one per vertex
#         return table(indices) #[B, 8, feat], one per vertex

# def get_interpolated_feature(position, features):
#     '''Given the 8 features corresponding to cube vertices, estimates the feature at position
#     via trilinear interpolation. 
    
#     Args:
#         position: query position between 0 and 1, [B, 3]
#         features: tensor of features stored at each vertex of the cube in the 
#             order specified by get_nearest_vertices_coords(), [B,8,feat_dim]
#     Returns:
#         interpolated feature, [B, feat_dim]
#     '''
#     # get interpolation weights (one for each dim); between 0 and 1
#     # lower interpolation weight == position is closer to vertex of cube nearest the origin
#     interp_weights = position - tf.math.floor(position) # [B,3]
#     x_weight, y_weight, z_weight = torch.split(interp_weights, num_or_size_splits=3, axis=1) # [B,3] -> 3*[B,1]
#     v0,v1,v2,v3,v4,v5,v6,v7 = tf.unstack(features, num=8, axis=1) # [B,8,feat_dim] -> 8*[B, feat]
#     # interpolate along x-axis along a plane defined by 4 points (check wikipedia article, "Method")
#     c00 = v0*(1-x_weight) + v1*x_weight
#     c01 = v4*(1-x_weight) + v5*x_weight
#     c10 = v3*(1-x_weight) + v2*x_weight
#     c11 = v7*(1-x_weight) + v6*x_weight

#     # bilinearly inteprolate along y-axis restricted to the previous plane (i.e. along plane parallel to y-axis)
#     c0 = c00*(1-y_weight) + c10*y_weight
#     c1 = c01*(1-y_weight) + c11*y_weight
#     # 1D linear interp 
#     return c0*(1-z_weight) + c1*z_weight


# # === UNIT TESTING
# positions = [
#     [0.1, 0.5, 0.9],
#     [1.9, 1.9, 1.9]
# ]
# positions = tf.convert_to_tensor(positions)
# print("pos:", positions)
# verts = get_nearest_vertices_coords(positions, 2)  # [2, 8, 3]
# # print(coords)
# table = Embedding(2**14, 2)
# hashed_feats = get_hashtable_features(verts, table) # [B,8,feat_dim]
# print("hashed feats:", hashed_feats)

# # hashed_feats = [[
# #     [0.,0.,0.],
# #     [1.,0.,0.],
# #     [1.,1.,0.],
# #     [0.,1.,0.],
# #     [0.,0.,1.],
# #     [1.,0.,1.],
# #     [1.,1.,1.],
# #     [0.,1.,1.],
# # ]]
# # hashed_feats = tf.convert_to_tensor(hashed_feats)
# interpolated_feat = get_interpolated_feature(positions, hashed_feats)  # [B,feat_dim] single interp feat per batch
# print("interpolated: ", interpolated_feat)