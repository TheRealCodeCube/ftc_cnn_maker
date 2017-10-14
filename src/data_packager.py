import lmdb
import matplotlib.pyplot as mp
import numpy as np
import os.path as path
import random
import re
import subprocess as s
import util
from caffe.proto import caffe_pb2
from caffe.io import datum_to_array, array_to_datum
from glob import glob

def resize_image(source_path, out_path='/tmp/resized.jpg', geometry='256x256!'):
    s.call(['convert', source_path, '-resize', geometry, out_path])

def write_images_to_db(db_folder, db_name, images):
    random.shuffle(images) #Shuffle input data to improve training.
    p = path.join(db_folder, db_name)
    s.call(['rm', '-r', p])
    map_size = 256*256*3*2*len(images)
    env = lmdb.Environment(p, map_size = map_size)
    write_to = env.begin(write=True, buffers=True)
    for i, image in enumerate(images):
        resize_image(image[0])
        input = np.transpose(mp.imread('/tmp/resized.jpg'), (2, 1, 0)) #Caffe wants CxHxW, not the standard WxHxC.
        datum = array_to_datum(input, image[1])
        print('Finished image', i+1, 'which had label', image[1])
        write_to.put('{:08}'.format(i).encode('ascii'), datum.SerializeToString())
    write_to.commit()
    env.close()
    
validation_percent = 0.1
min_images = (1 / validation_percent) * 5
def write_to_database(model_name):
    images = [[] for i in range(10)]
    p = path.join(util.get_model_folder(), model_name)
    source_folder = path.join(p, 'raw_data')
    for filename in glob(path.join(source_folder, '*')):
        bits = re.split(r'\_|\.', filename)
        lindex = bits.index('LABEL')
        label = int(bits[lindex+1])
        images[label].append(filename)
        
    training = []
    validation = []
    for i in range(10):
        if(len(images[i]) > min_images):
            validation_size = int(len(images[i]) * validation_percent)
            validation += [(name, i) for name in images[i][:validation_size]]
            training += [(name, i) for name in images[i][validation_size:]]
        else:
            print('There are not enough images for category ' + str(i) + ' for it to be included.')
    
    write_images_to_db(path.join(p, 'training_data'), training)
    write_images_to_db(path.join(p, 'validation_data'), validation)
        
def import_raw_data(source_folder, model_name, overwrite=False):
    p = path.join(util.get_model_folder(), model_name, 'raw_data') + '/'
    if(overwrite):
        s.call(['rm', '-r'] + glob(path.join(p, 'raw_data', '*')))
    for image_path in glob(path.join(source_folder, '*')):
        s.call(['cp', image_path, p])
        


