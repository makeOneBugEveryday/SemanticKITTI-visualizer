import open3d as o3d
import numpy as np
import yaml
import json
import os

class Visualizer:
    def __init__(self, cfg_path):
        self.pcd_extension = ['.bin']
        self.label_extension = ['.label']
        
        with open(cfg_path, 'r') as cfg_file:
            visual_cfg = yaml.safe_load(cfg_file)
        self.pcd_dir = [os.path.join(visual_cfg['pcd_dir'], item) 
                        for item in os.listdir(visual_cfg['pcd_dir'])]
        self.pcd_extension = visual_cfg['pcd_extension']
        self.label_dir = [os.path.join(visual_cfg['label_dir'], item) 
                        for item in os.listdir(visual_cfg['label_dir'])]
        self.label_extension = visual_cfg['label_extension']
        left = visual_cfg['position']['left']
        top = visual_cfg['position']['top']
        width = visual_cfg['position']['width']
        height = visual_cfg['position']['height']
        point_size = visual_cfg['point_size']
        
        dataset_cfg_path = visual_cfg['dataset_cfg_path']
        with open(dataset_cfg_path, 'r') as dataset_cfg_file:
            dataset_cfg = yaml.safe_load(dataset_cfg_file) 
        self.color_map = dataset_cfg['color_map']
        
        viewpoint_path = visual_cfg['viewpoint_cfg_path']
        with open(viewpoint_path, 'r') as viewpoint_file:
            viewpoint_cfg = json.load(viewpoint_file)
        front_vector = viewpoint_cfg['trajectory'][0]['front']
        lookat_vector = viewpoint_cfg['trajectory'][0]['lookat']
        up_vector = viewpoint_cfg['trajectory'][0]['up']
        zoom_vector = viewpoint_cfg['trajectory'][0]['zoom']
        
        self.index = 0
        self.pcd = o3d.geometry.PointCloud()
        self.vis = o3d.visualization.VisualizerWithKeyCallback()
        self.vis.create_window(window_name='semantic-kitti', width=width, height=height, left=left, top=top, visible=True)
        
        mesh_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1, origin=[0, 0, 0])
        self.vis.add_geometry(mesh_frame)
        
        self.__update_frame()
        self.vis.add_geometry(self.pcd)
        
        self.render_option = self.vis.get_render_option()
        self.render_option.background_color = np.asarray([0.05, 0.05, 0.05])      
        self.render_option.point_size = point_size
        
        self.view_control = self.vis.get_view_control()
        self.view_control.set_front(front_vector)
        self.view_control.set_lookat(lookat_vector)
        self.view_control.set_up(up_vector)
        self.view_control.set_zoom(zoom_vector)        
        # self.vis.add_geometry(mesh_frame) # viewpoint config will be initialized again after add_geometry() function
        
        self.vis.register_key_callback(ord('N'), self.__key_next_callback)
        self.vis.register_key_callback(ord('B'), self.__key_back_callback)
    
    def __load_pcd_bin(self, pcd_path):
        points = np.fromfile(pcd_path, dtype=np.float32)
        points = points.reshape((-1, 4))
        coordinate = points[:, 0:3]
        # remission = points[:, 3]
        self.pcd.points = o3d.utility.Vector3dVector(coordinate)
    
    def __load_label_lable(self, label_path):
        label = np.fromfile(label_path, dtype=np.int32)
        label = label.reshape((-1))
        semantic_label = label & 0x0000FFFF
        # instance_lable = label >> 16
        colors = np.asarray([self.color_map[item] for item in semantic_label])
        colors = colors/256
        self.pcd.colors = o3d.utility.Vector3dVector(colors)
        
    def __update_frame(self):
        if self.pcd_extension == '.bin':
            self.__load_pcd_bin(self.pcd_dir[self.index])
        else: 
            raise TypeError(f"point cloud data should end with in {self.pcd_extension}")
        if self.label_extension == '.label':
            self.__load_label_lable(self.label_dir[self.index])
        else: 
            raise TypeError(f"label data should end with in {self.label_extension}")
    
    def __key_next_callback(self, vis):
        self.index += 1
        self.__update_frame()
        self.vis.update_geometry(self.pcd)
        self.vis.update_renderer()
        self.vis.poll_events()
    
    def __key_back_callback(self, vis):
        self.index -= 1
        self.__update_frame()
        self.vis.update_geometry(self.pcd)
        self.vis.update_renderer()
        self.vis.poll_events()
    
    def run(self):
        if self.pcd_dir is None:
            raise RuntimeError("Visualizer object should be set config via set_config_file(filename) before run!")
        self.vis.run()
        self.vis.destroy_window()   
        
