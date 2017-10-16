import tkinter as tk

root = tk.Tk()
root.geometry('800x600')
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1, uniform='a')

splash_label = tk.Label(root, text="Loading...")
splash_label.grid(row=0, column=0, sticky=tk.NSEW)
root.update()

import os.path
import subprocess as s
from tkinter import filedialog as filedialog
from tkinter import ttk
from model import CaffeModel

models = CaffeModel.load_all_from_models_folder()

splash_label.grid_forget()
root.columnconfigure(1, weight=2, uniform='a')
    
class InformationDialog:
    '''
    Used to inform the user of information.
    '''
    def __init__(self, message, callback=lambda:0):
        self.top = tk.Toplevel(root)
        self.top.geometry('280x120')
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)
        tk.Label(self.top, text=message, wraplength=280).grid(row=0, column=0)
        self.button = tk.Button(self.top, text='Okay', command=self.pressed)
        self.button.grid(row=1, column=0)
        self.callback = callback
        
    def pressed(self):
        self.top.destroy()
        self.callback()
    
class TextInputDialog:
    '''
    Used to ask the user for a line of text input.
    '''
    def __init__(self, message, callback=lambda a:0):
        self.top = tk.Toplevel(root)
        self.top.geometry('280x120')
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)
        tk.Label(self.top, text=message, wraplength=280).grid(row=0, column=0)
        self.svar = tk.StringVar()
        self.entry = tk.Entry(self.top, textvariable=self.svar)
        self.entry.grid(row=1, column=0)
        self.button = tk.Button(self.top, text='Submit', command=self.pressed)
        self.button.grid(row=2, column=0)
        self.callback = callback
        
    def pressed(self):
        self.top.destroy()
        self.callback(self.svar.get())
        
class ProgressDialog:
    '''
    Used to inform the user of the progress of an operation.
    '''
    def __init__(self, num_layers):
        self.top = tk.Toplevel(root)
        self.layers = []
        for i in range(num_layers):
            label = tk.Label(self.top, text='')
            label.grid(row=i*2, column=0)
            bar = ttk.Progressbar(self.top, orient='horizontal', length=280, mode='determinate')
            bar.grid(row=i*2+1, column=0)
            self.layers.append((label, bar))
            
    def show_progress(self, progress_list):
        for element, layer in zip(progress_list, self.layers):
            layer[0].config(text=element[1])
            layer[1].config(value=element[0]*100)
        root.update()
            
    def close(self):
        self.top.destroy()
    
class ModelDetailFrame:
    '''
    All the buttons you can push to change parts of the model.
    '''
    def __init__(self):
        model_details = tk.Frame(root)
        model_details.grid(row=0, column=1, sticky=tk.NSEW)
        model_details.columnconfigure(0, weight=1)
        
        self.model_name = tk.Label(model_details, text="NO MODEL SELECTED (SELECT ONE BEFORE USING ANY OF THESE BUTTONS)")
        self.model_name.grid(row=0, column=0, sticky=tk.W)
        model_stuff = tk.Frame(model_details)
        model_stuff.grid(row=1, column=0, sticky=tk.EW)
        
        tk.Button(model_stuff, text="Rename", command=self.rename_pressed).grid(row=0, column=0)
        tk.Button(model_stuff, text="Edit Model", command=self.edit_model_pressed).grid(row=0, column=1)
        tk.Button(model_stuff, text="Edit Solver", command=self.edit_solver_pressed).grid(row=0, column=2)
        tk.Button(model_stuff, text="Upload via ADB", command=self.upload_to_phone_pressed).grid(row=0, column=3)
        
        self.raw_data_label = tk.Label(model_details, text="0 pictures in dataset. (DB up to date.)")
        self.raw_data_label.grid(row=2, column=0, sticky=tk.W)
        raw_data_stuff = tk.Frame(model_details)
        raw_data_stuff.grid(row=3, column=0, sticky=tk.EW)
        
        overwrite_raw_data_button = tk.Button(raw_data_stuff, text="Overwrite", command=self.overwrite_raw_data_pressed)
        overwrite_raw_data_button.grid(row=0, column=1)
        append_raw_data_button = tk.Button(raw_data_stuff, text="Append", command=self.append_raw_data_pressed)
        append_raw_data_button.grid(row=0, column=2)
        write_raw_data_to_db_button = tk.Button(raw_data_stuff, text="Write to DB", command=self.write_raw_data_to_db_pressed)
        write_raw_data_to_db_button.grid(row=0, column=3)
        
        self.training_label = tk.Label(model_details, text="Training")
        self.training_label.grid(row=4, column=0, sticky=tk.W)
        training_stuff = tk.Frame(model_details)
        training_stuff.grid(row=5, column=0, sticky=tk.EW)
        
        self.start_training_button = tk.Button(training_stuff, text="Start Training", command=self.start_training_pressed)
        self.start_training_button.grid(row=0, column=1)
        
        self.current_model = None
        
    def update_dataset_text(self):
        '''
        Updates the status of the dataset shown to the user (how many pics, whether or not they have
        been written to the DB, etc.
        '''
        text = str(self.current_model.get_num_pictures_in_raw_data())
        text += ' picture(s) in dataset. '
        text += '(DB is ' + ['not ', ''][self.current_model.is_db_up_to_date()] + 'up to date.)'
        self.raw_data_label.config(text=text)
        
    def set_current_model(self, model):
        '''
        Sets which model is currently being edited by this panel.
        '''
        self.current_model = model
        self.model_name.config(text=model.get_name())
        self.update_dataset_text()
        
    def rename_pressed(self):
        '''
        Renames the model currently being edited.
        '''
        if(self.current_model is not None):
            TextInputDialog('New model name:', self.rename)
            
    def rename(self, new_name):
        self.current_model.rename(new_name)
        self.model_name.config(text=new_name)
        refresh_model_list()
    
    default_editor = 'gedit'
    def edit_model_pressed(self):
        '''
        Opens a text editor (gedit by default) to edit the model's model.prototext.
        TODO: make this also update production.prototext when it is finished.
        '''
        if(self.current_model is not None):
            proc = s.Popen([ModelDetailFrame.default_editor, os.path.join(self.current_model.get_folder(), 'model.prototext')])
    
    def edit_solver_pressed(self):
        '''
        Opens a text editor (gedit by default) to edit the model's solver.prototext.
        '''
        if(self.current_model is not None):
            proc = s.Popen([ModelDetailFrame.default_editor, os.path.join(self.current_model.get_folder(), 'solver.prototext')])
        
    def upload_to_phone_pressed(self):
        '''
        Uploads the model's production.prototext and most recent snapshot.caffemodel to a phone 
        connected via ADB. The files will be in /sdcard/caffe_files/model_name.prototext and 
        /sdcard/caffe_files/model_name.caffemodel
        '''
        if((self.current_model is not None)):
            snapshot = self.current_model.get_last_snapshot()
            if(snapshot is None):
                InformationDialog('There is no available snapshot to upload! Train the network before uploading it.')
                return
            else:
                start = snapshot.find('iter_') + len('iter_')
                end = snapshot.find('.solverstate', start)
                InformationDialog('Finished uploading the state of this model as of training iteration #' + snapshot[start:end])
            s.call(['adb', 'shell', 'mkdir', '/sdcard/caffe_files'])
            s.call(['adb', 'push', os.path.join(self.current_model.get_folder(), 'production.prototext'), 
                    '/sdcard/caffe_files/' + self.current_model.get_name() + '.prototext'])
            s.call(['adb', 'push', snapshot.replace('solverstate', 'caffemodel'), 
                    '/sdcard/caffe_files/' + self.current_model.get_name() + '.caffemodel'])
        
    def overwrite_raw_data_pressed(self):
        '''
        Overwrites the images used to train the network from a user-selected folder.
        '''
        dialog = InformationDialog('Pick the folder containing the images that should overwrite the current data set.', 
                                   lambda: self.import_raw_data(True))
    
    def append_raw_data_pressed(self):
        '''
        Adds images to be used for training the network from a user-selected folder.
        '''
        dialog = InformationDialog('Pick the folder containing the images that should be added to the current data set.', 
                                   lambda: self.import_raw_data(False))
        
    def import_raw_data(self, overwrite):
        '''
        Helper method for overwrite_raw_data_pressed and append_raw_data_pressed.
        '''
        path = filedialog.askdirectory()
        progress = ProgressDialog(1)
        if((path != '') and (self.current_model is not None)):
            self.current_model.import_raw_data(path, overwrite=overwrite, callback=progress.show_progress)
        self.update_dataset_text()
        progress.close()
    
    def write_raw_data_to_db_pressed(self):
        '''
        Writes the images used for training the network into training and validation databases.
        '''
        progress = ProgressDialog(2)
        if(self.current_model is not None):
            self.current_model.write_raw_data_to_dbs(callback=progress.show_progress)
        self.update_dataset_text()
        progress.close()
    
    def start_training_pressed(self):
        '''
        Starts training the selected model.
        '''
        start_training(self.current_model, True)
       
mdf = ModelDetailFrame()

model_list = tk.Listbox(root)
model_list.grid(row=0, column=0, sticky=tk.NSEW)
for model in models:
    model_list.insert(tk.END, model.get_name())

def select_model(event):
    index = model_list.curselection()[0]
    mdf.set_current_model(models[index])
model_list.bind('<Double-Button-1>', select_model)

def refresh_model_list():
    model_list.delete(0, tk.END)
    for model in models:
        model_list.insert(tk.END, model.get_name())

class TrainingFooter:
    '''
    It shows the progress of whatever model is currently being trained.
    '''
    def __init__(self):
        footer = tk.Frame(root)
        footer.grid(row=1, column=1, sticky=tk.EW)
        
        self.footer_label = tk.Label(footer, text='No training in progress.')
        self.footer_label.grid(row=1, column=1, sticky=tk.W)
        
    def update(self, model_trainer):
        lta = model_trainer.last_test_accuracy
        ltl = model_trainer.last_test_loss
        lrl = model_trainer.last_train_loss
        li = model_trainer.last_iter
        ls = model_trainer.last_snapshot
        
        message = 'Training ' + model_trainer.model.get_name()
        message += ', i: ' + str(li)
        message += ', loss: ' + str(lrl)
        if(type(lta) is str):
            message += ', acc: ' + lta + '%'
        else:
            message += ', acc: ' + str(lta*100) + '%'
        message += ', snap: ' + str(ls)
        
        self.footer_label.config(text=message)
tf = TrainingFooter()
        
current_trainer = None
def start_training(model, resume):
    global current_trainer
    if(model is not None):
        if(current_trainer is None):
            current_trainer = model.create_trainer_thread(resume=resume)
            current_trainer.set_callback(tf.update)
            current_trainer.start() 
            
def close():
    '''
    Called when the window should be closed.
    '''
    global current_trainer
    if((current_trainer is not None) and (current_trainer.running)):
        current_trainer.stop_soon()
        current_trainer.join()
    root.destroy()
        
root.protocol('WM_DELETE_WINDOW', close)

tk.mainloop()











