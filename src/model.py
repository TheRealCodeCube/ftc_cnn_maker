import lmdb
import matplotlib.pyplot as mp
import numpy as np
import os.path
import random
import re
import subprocess as s
import util
from caffe.proto import caffe_pb2
from caffe.io import datum_to_array, array_to_datum
from glob import glob
from threading import Thread
from time import sleep

def resize_image(source_path, out_path='/tmp/resized.jpg', geometry='256x256!'):
    '''
    Resizes an image at source_path using geometry as the geometry specifier to the file at
    out_path. This is used for converting training data to the size that the network needs.
    '''
    s.call(['convert', source_path, '-resize', geometry, out_path])
    
class ModelTrainer(Thread):
    def __init__(self, model, resume):
        super().__init__()
        self.setDaemon(True)
        self.model = model
        self.resume = resume
        self.last_test_accuracy = '?'
        self.last_test_loss = '?'
        self.last_train_loss = '?'
        self.last_iter = '?'
        self.last_snapshot = 'none'
        self.callback = lambda a: None
        self.running = True
        
    def run(self):
        resume_args = []
        if(self.resume):
            snapshot = self.model.get_last_snapshot()
            if(snapshot is not None):
                resume_args = ['--snapshot', snapshot]
                start = snapshot.find('iter_') + len('iter_')
                end = snapshot.find('.solverstate', start)
                self.last_snapshot = int(snapshot[start:end])
        trainer = self.trainer = s.Popen(['caffe', 'train', '--solver', os.path.join(self.model.get_folder(), 'solver.prototext')] + resume_args,
                          stdin=s.PIPE, stdout=s.PIPE, stderr=s.PIPE, cwd=self.model.get_folder())
        while self.running:
            line = trainer.stderr.readline().decode('utf-8')
            if(line.strip() == ''):
                return
            print('[CAFFE]', line.replace('\n', ''))
            #Parse log messages to find out what is going on.
            if('Test' in line):
                if('accuracy' in line):
                    start = line.find('accuracy = ') + len('accuracy = ')
                    self.last_test_accuracy = float(line[start:])
                elif('loss' in line):
                    start = line.find('loss = ') + len('loss = ')
                    end = line.find('(', start)
                    self.last_test_loss = float(line[start:end])
            elif('Train' in line):
                if('loss' in line):
                    start = line.find('loss = ') + len('loss = ')
                    end = line.find('(', start)
                    self.last_train_loss = float(line[start:end])
            elif('Iteration' in line):
                start = line.find('Iteration ') + len('Iteration ')
                end = min([line.find(i, start) for i in '(,' if i in line] + [len(line) - 1])
                self.last_iter = int(line[start:end])
            elif('Snapshotting' in line):
                if('caffemodel' in line):
                    start = line.find('iter_') + len('iter_')
                    end = line.find('.caffemodel', start)
                    self.last_snapshot = int(line[start:end])
            else:
                continue
            self.callback(self)
            
    def set_callback(self, new_callback):
        self.callback = new_callback
        
    def stop_soon(self):
        self.running = False
        self.trainer.kill()
    
class CaffeModel:
    def __init__(self):
        self.name = ''
        self.path = ''
        self.db_up_to_date = True
        
    @staticmethod
    def load_from_models_folder(name):
        model = CaffeModel()
        model.name = name
        model.path = util.get_model_folder(name) 
        return model
    
    @staticmethod
    def load_all_from_models_folder():
        return [CaffeModel.load_from_models_folder(path.split('/')[-1]) for path in 
                glob(os.path.join(util.get_model_folder(), '*'))]
    
    def get_folder(self):
        '''
        Returns the folder containing files for this model.
        '''
        return self.path
    
    def get_name(self):
        '''
        Returns the name of this model.
        '''
        return self.name
    
    def is_db_up_to_date(self):
        '''
        Returns true if any changes in the raw_data folder have been written to databases. 
        (NOTE: THIS IS ONLY PERSISTENT ACROSS THE OBJECT'S LIFETIME. IF THIS OBJECT IS DE-
        STROYED AND RECREATED, IT WILL BE RESET TO TRUE, EVEN IF IT USED TO BE FALSE.)
        '''
        return self.db_up_to_date

    def write_images_to_db(self, db_name, images, callback=lambda a:0):
        '''
        Writes images to a lmdb database inside this model's folder. db_name is the name of the
        database. If a database by that name already exists, it will be overwritten. images is a
        list of 2-element tuples. The first elemnt of each tuple should be a path to an image, and
        the second element should be the label of that image.
        '''
        random.shuffle(images) #Shuffle input data to improve training.
        p = os.path.join(self.get_folder(), db_name)
        s.call(['rm', '-r', p])
        map_size = 256*256*3*2*len(images)
        env = lmdb.Environment(p, map_size = map_size)
        write_to = env.begin(write=True, buffers=True)
        i = 0
        num_images = len(images)
        update_interval = int(num_images/100+1) 
        for image in images:
            try:
                resize_image(image[0])
                input = np.transpose(mp.imread('/tmp/resized.jpg'), (2, 1, 0)) #Caffe wants CxHxW, not the standard WxHxC.
                datum = array_to_datum(input, image[1])
                write_to.put('{:08}'.format(i).encode('ascii'), datum.SerializeToString())
                i += 1
            except:
                pass
            if(i % update_interval == 0):
                callback([(i/num_images, '')])
        write_to.commit()
        env.close()
        
    validation_percent = 0.1
    min_images = (1 / validation_percent) * 5
    def write_raw_data_to_dbs(self, callback=lambda a:0):
        '''
        Takes images in this model's raw_data folder, splits them into training and validation batches,
        and writes the resulting batches to databases named training_data and validation_data, respectively.
        '''
        callback([(1/3, 'Finding files...')])
        images = [[] for i in range(10)]
        model_folder = self.get_folder()
        raw_data_folder = os.path.join(model_folder, 'raw_data')
        for filename in glob(os.path.join(raw_data_folder, '*')):
            bits = re.split(r'\_|\.', filename)
            lindex = bits.index('LABEL')
            label = int(bits[lindex+1])
            images[label].append(filename)
        for i in range(10):
            random.shuffle(images[i])
            
        training = []
        validation = []
        for i in range(10):
            if(len(images[i]) > CaffeModel.min_images):
                validation_size = int(len(images[i]) * CaffeModel.validation_percent)
                validation += [(name, i) for name in images[i][:validation_size]]
                training += [(name, i) for name in images[i][validation_size:]]
            else:
                print('There are not enough images for category ' + str(i) + ' for it to be included.')
        
        def lift_callback(db_prog):
            callback(prog + db_prog)
        prog = [(2/3, 'Writing training batch...')]
        self.write_images_to_db('training_data', training, lift_callback)
        prog = [(3/3, 'Writing validation batch...')]
        self.write_images_to_db('validation_data', validation, lift_callback)
        self.db_up_to_date = True
        
    def import_raw_data(self, source_folder, overwrite=False, callback=lambda a:0):
        '''
        Modifies the contents of this model's raw_data folder based on images from another folder. If
        overwrite is False (default), the pictures will be added to the current folder. If it is True,
        the old pictures already in raw_data will be deleted before adding the new ones.
        '''
        raw_data_folder = os.path.join(self.get_folder(), 'raw_data') + '/'
        if(overwrite):
            s.call(['rm', '-r'] + glob(os.path.join(raw_data_folder, '*')))
        i = 0
        image_paths = glob(os.path.join(source_folder, '*'))
        num_images = len(image_paths)
        update_interval = int(num_images / 100 + 1)
        for image_path in image_paths:
            s.call(['cp', image_path, raw_data_folder])
            i += 1
            if(i % update_interval == 0):
                callback([(i/num_images, 'Copying images...')])
        self.db_up_to_date = False
        
    def import_via_adb(self, callback=lambda a:0):
        '''
        Appends the contents of the currently connected phone's /sdcard/caffe_files/training_images folder
        to the input database.
        '''
        source = '/sdcard/caffe_files/training_images'
        raw_data_folder = os.path.join(self.get_folder(), 'raw_data') + '/'
        files = []
        for line in s.check_output(['adb', 'shell', 'ls', source]).decode('ascii').split('\n'):
            files += [i.strip() for i in line.split(' ') if i.strip() != '']
        total = len(files)
        done = 0
        for file in files:
            s.call(['adb', 'pull', source + '/' + file, raw_data_folder])
            done += 1
            callback([('Copying files...', done/total)])
        
    def get_num_pictures_in_raw_data(self):
        '''
        Returns the number of pictures stored in this model's raw_data folder.
        '''
        return len(glob(os.path.join(self.get_folder(), 'raw_data', '*')))
    
    def create_trainer_thread(self, resume=True):
        '''
        Returns a ModelTrainer thread that, when started, will train this network.
        '''
        if(not resume):
            s.call(['rm'] + glob(os.path.join(self.get_folder(), 'snapshots', '*')))
        return ModelTrainer(self, resume=resume)
    
    def rename(self, new_name):
        models_path = util.get_model_folder()
        s.call(['mv', os.path.join(models_path, self.name), os.path.join(models_path, new_name)])
        self.name = new_name
        self.path = util.get_model_folder(self.name)
        
    def get_last_snapshot(self):
        snapshots = glob(os.path.join(self.path, 'snapshots', '*.solverstate'))
        if(len(snapshots) == 0):
            return None
        snapshots.sort(key=lambda e: -int(e.split('.')[-2].split('/')[-1].split('_')[-1]))
        return snapshots[0]

#import subprocess as s
#s.call(['caffe', 'train', '-solver', 'solver.prototext'])
#print('done!')
