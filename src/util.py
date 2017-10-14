import os
import os.path as path

def get_root_folder():
    '''
    Returns the root folder (usually called ftc_cnn_maker) that contains the folders for the
    python code, imported data, and models.
    '''
    p = os.getcwd()
    i = max(p.rfind('src'), p.rfind('models'), p.rfind('ftc_cnn_maker') + len('ftc_cnn_maker/'))
    i = min(i, len(p))
    return p[:i]

def get_model_folder(model_name=None):
    '''
    If model_name is not None, returns the folder containing the model by that name. If it is
    None, then the folder containing all models' folders is returned.
    '''
    if(model_name is None):
        return path.join(get_root_folder(), 'models')
    else:
        return path.join(get_root_folder(), 'models', model_name)
    