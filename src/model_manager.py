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
import util

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
    
class ConfirmationDialog:
    '''
    Used to ask the user if they really meant to type 'sudo rm -rf /'
    '''
    def __init__(self, message, callback=lambda:0, positive='Okay', negative='Cancel'):
        self.top = tk.Toplevel(root)
        self.top.geometry('280x120')
        self.top.columnconfigure(0, weight=1)
        self.top.columnconfigure(1, weight=1)
        self.top.rowconfigure(0, weight=1)
        tk.Label(self.top, text=message, wraplength=280).grid(row=0, column=0, columnspan=2)
        tk.Button(self.top, text=positive, command=self.pressed).grid(row=1, column=0)
        tk.Button(self.top, text=negative, command=lambda: self.top.destroy()).grid(row=1, column=1)
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
        
class SelectionDialog:
    '''
    Used to ask the user to select one of several options.
    '''
    def __init__(self, message, choices, callback=lambda a:0):
        self.top = tk.Toplevel(root)
        self.top.geometry('280x120')
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)
        self.top.rowconfigure(1, weight=1)
        tk.Label(self.top, text=message, wraplength=280).grid(row=0, column=0)
        self.svar = tk.StringVar()
        self.svar.set(choices[0])
        self.spinner = tk.OptionMenu(self.top, self.svar, *choices)
        self.spinner.grid(row=1, column=0)
        tk.Button(self.top, text='Submit', command=self.pressed).grid(row=2, column=0)
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
        model_details = self.model_details = tk.Frame(root)
        model_details.columnconfigure(0, weight=1)
        
        self.model_name = tk.Label(model_details, text="NO MODEL SELECTED (SELECT ONE BEFORE USING ANY OF THESE BUTTONS)")
        self.model_name.grid(row=0, column=0, sticky=tk.W)
        model_stuff = tk.Frame(model_details)
        model_stuff.grid(row=1, column=0, sticky=tk.EW)
        
        tk.Button(model_stuff, text="Rename", command=self.rename_pressed).grid(row=0, column=0)
        tk.Button(model_stuff, text="Delete", command=self.delete_pressed).grid(row=0, column=1)
        tk.Button(model_stuff, text="Edit Model", command=self.edit_model_pressed).grid(row=0, column=2)
        tk.Button(model_stuff, text="Edit Solver", command=self.edit_solver_pressed).grid(row=0, column=3)
        tk.Button(model_stuff, text="Upload To Android Device", command=self.upload_to_phone_pressed).grid(row=0, column=4)
        
        self.raw_data_label = tk.Label(model_details, text="0 pictures in dataset. (DB up to date.)")
        self.raw_data_label.grid(row=2, column=0, sticky=tk.W)
        raw_data_stuff = tk.Frame(model_details)
        raw_data_stuff.grid(row=3, column=0, sticky=tk.EW)
        
        tk.Button(raw_data_stuff, text="Browse", command=self.browse_data_pressed).grid(row=0, column=0)
        overwrite_raw_data_button = tk.Button(raw_data_stuff, text="Overwrite", command=self.overwrite_raw_data_pressed)
        overwrite_raw_data_button.grid(row=0, column=1)
        append_raw_data_button = tk.Button(raw_data_stuff, text="Append", command=self.append_raw_data_pressed)
        append_raw_data_button.grid(row=0, column=2)
        append_from_adb = tk.Button(raw_data_stuff, text="Append From Android Device", command=self.append_via_adb_pressed)
        append_from_adb.grid(row=0, column=3)
        #Updating the database was previously done manually. To avoid user error, it is now done whenever the user uses
        #the Overwrite or Append buttons.
        #write_raw_data_to_db_button = tk.Button(raw_data_stuff, text="Write to DB", command=self.write_raw_data_to_db_pressed)
        #write_raw_data_to_db_button.grid(row=0, column=3)
        
        self.training_label = tk.Label(model_details, text="Training")
        self.training_label.grid(row=4, column=0, sticky=tk.W)
        training_stuff = tk.Frame(model_details)
        training_stuff.grid(row=5, column=0, sticky=tk.EW)
        
        self.resume_training_button = tk.Button(training_stuff, text="Resume Training", command=lambda: self.start_training(True))
        self.resume_training_button.grid(row=0, column=0)
        self.start_training_button = tk.Button(training_stuff, text="Start Training From Scratch", command=lambda: self.start_training(False))
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
        
    def update_training_status(self):
        '''
        Grays out the Resume Training button if there are no snapshots, and grays out both buttons
        if this network is already being trained.
        '''
        if((current_trainer != None) and (current_trainer.model.get_folder() == self.current_model.get_folder())):
            self.resume_training_button.config(state=tk.DISABLED)
            self.start_training_button.config(state=tk.DISABLED)
        else:
            if(self.current_model.get_last_snapshot() is None):
                self.resume_training_button.config(state=tk.DISABLED)
            else:
                self.resume_training_button.config(state=tk.NORMAL)
            self.start_training_button.config(state=tk.NORMAL)
        
    def set_current_model(self, model):
        '''
        Sets which model is currently being edited by this panel.
        '''
        if(model is None):
            self.model_details.grid_forget()
        else:
            self.model_details.grid(row=0, column=1, sticky=tk.NSEW)
            self.current_model = model
            self.model_name.config(text=model.get_name())
            self.update_dataset_text()
            self.update_training_status()
        
    def delete_pressed(self):
        if(self.current_model is None):
            return
        def really_delete():
            s.call(['rm', '-r', self.current_model.get_folder()])
            models.remove(self.current_model)
            refresh_model_list()
            self.set_current_model(None)
        ConfirmationDialog('Are you sure? This will delete EVERYTHING about the network, including its structure, input, and training!', really_delete)
        
    def rename_pressed(self):
        if(self.current_model is not None):
            TextInputDialog('New model name:', self.rename)
            
    def rename(self, new_name):
        '''
        Renames the model currently being edited.
        '''
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
            
    default_browser = 'nautilus'
    def browse_data_pressed(self):
        '''
        Opens the input data in a file browser (nautilus by default).
        '''
        s.Popen([ModelDetailFrame.default_browser, os.path.join(self.current_model.get_folder(), 'raw_data')])
        InformationDialog('Press Okay when you are done making changes to the dataset.', callback=lambda: self.write_raw_data_to_db())
        
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
        
        #Update databases. Previously, this was done with a seperate button, but this way allows for less user error.
        self.write_raw_data_to_db()
        
    def append_via_adb_pressed(self):
        '''
        Appends images captured on an android device connected to the computer.
        '''
        if(self.current_model is None):
            return
        progress = ProgressDialog(1)
        self.current_model.import_via_adb(callback=progress.show_progress)
        progress.close()
        self.write_raw_data_to_db()
        def delete_via_adb():
            s.call(['adb', 'shell', 'rm', '/sdcard/caffe_files/training_images/*'])
            InformationDialog('The files have been deleted!')
        ConfirmationDialog('Would you like to delete the images off of the device to free up space?', 
                           positive='Yes', negative='No', callback=delete_via_adb)
    
    def write_raw_data_to_db(self):
        '''
        Writes the images used for training the network into training and validation databases.
        '''
        progress = ProgressDialog(2)
        if(self.current_model is not None):
            self.current_model.write_raw_data_to_dbs(callback=progress.show_progress)
        self.update_dataset_text()
        progress.close()
    
    def start_training(self, resume):
        '''
        Starts training the selected model.
        '''
        start_training(self.current_model, resume)
        self.update_training_status()
       
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
        if(current_trainer is not None):
            current_trainer.stop_soon()
            current_trainer.join()
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
    
def create_from_template():
    def do_copy(template_name, new_name):
        source = os.path.join(util.get_root_folder(), 'templates', template_name)
        dest = os.path.join(util.get_model_folder(new_name))
        s.call(['cp', '-r', source, dest])
        models.append(CaffeModel.load_from_models_folder(new_name))
        refresh_model_list()
    
    def template_name_callback(selected):
        TextInputDialog('Enter a name for the new model.', lambda result: do_copy(selected, result))
        
    templates = os.listdir(os.path.join(util.get_root_folder(), 'templates'))
    SelectionDialog('Select a template to base the new model off of.', templates, template_name_callback)
           
tk.Button(root, text='+ New Model +', command=create_from_template).grid(row=1, column=0)#, anchor=tk.W)
            
root.protocol('WM_DELETE_WINDOW', close)

tk.mainloop()











