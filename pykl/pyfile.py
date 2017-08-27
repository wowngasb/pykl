#-*- coding: utf-8 -*-
import os
import marshal

def get_dict_of_dir(str_dir, filter_func=None, encode='gb2312'):
    str_dir = str_dir.encode(encode, 'ignore') if isinstance(str_dir, unicode) else str_dir
    if not os.path.isdir(str_dir):
        return {}
    filter_func = filter_func if hasattr(filter_func, '__call__') else lambda s_full_name: True
    all_files, current_files = {}, os.listdir(str_dir)
    for file_name in current_files:
        if file_name=='.' or file_name=='..':
            continue
        full_name = os.path.join(str_dir, file_name)
        if os.path.isfile(full_name):
            if filter_func(full_name):
                all_files.setdefault(full_name, file_name)
        elif os.path.isdir(full_name):
            next_files = get_dict_of_dir(full_name, filter_func)
            for n_full_name, n_file_name in next_files.items():
                all_files.setdefault(n_full_name, n_file_name)

    return all_files
    
def dump_obj(obj, file_name):
    with open(file_name, 'wb') as wf:
        marshal.dump(obj, wf)

def load_obj(file_name):
    with open(file_name, 'rb') as rf:
        return marshal.load(rf)

       
def load_str(filename):
    ret_str = ''
    if os.path.isfile(filename):
        with open(filename, 'r') as rf:
            ret_str = rf.read()
    return ret_str

def dump_str(strin, filename):
    with open(filename, 'w') as wf:
        wf.write(strin)
        
def main():
    pass

if __name__ == '__main__':
    main()

