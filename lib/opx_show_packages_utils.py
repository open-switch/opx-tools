#!/usr/bin/python
import sys
import json
import lib.opx_python_common_utils

cfg_file = "/etc/opx/manifest.json"

def parse_manifest():
    try:
        with open(cfg_file, 'r') as fd:
            data = json.load(fd)
        return data
    except Exception:
        print "Config file not present"
        sys.exit(1)


def get_dpkg_info(packages_cfg_info):

    packages_info = {}
    for elem in packages_cfg_info:        
        try:            
            package_name_cfg = elem['name']
            package_version_cfg = elem['version']
            
            cmd = "dpkg -s " + package_name_cfg
            ret = opx_python_common_utils.run_cmd_get_output([cmd])
            
            tmp_dict = {}
            for l in ret:
                if l:
                    try:
                        (k,v) = l.split(':',1)
                    except ValueError:
                        pass
                    
                    tmp_dict[k] = v
            # Fill the original version from the cfg file
            tmp_dict['orig_version'] =  package_version_cfg
            
            # Check the integrity of the package
            cmd = "dpkg -V " + package_name_cfg
            ret = opx_python_common_utils.run_cmd_get_output([cmd])
            if len(ret) == 1 and ret[0] == '':
                tmp_dict['Altered'] = 'No'
            else: tmp_dict['Altered'] = 'Yes'
            
            # If the package has been upgraded, mark them as Yes
            if tmp_dict['orig_version'] < tmp_dict['Version']:
                tmp_dict['Upgraded'] = 'Yes'
            else:
                tmp_dict['Upgraded'] = 'No'
            
            # Fill the package information
            packages_info[package_name_cfg] = tmp_dict
            
            
        except ValueError:
            pass
            
    return packages_info            

def get_packages_info():    
    data = parse_manifest()
    if 'packages' in data:
        packages_cfg_info = data['packages']
    else:
        return {}
    
    return get_dpkg_info(packages_cfg_info)
    

def get_specific_package_info(key):
    info = []
    packages_info = get_packages_info()    
    
    for p in packages_info:
        if key in packages_info[p]:
            if packages_info[p][key] == 'Yes':
                info.append(p)
    return info
    
            
def get_altered_packages():
    return get_specific_package_info('Altered')
            
            
def get_upgraded_packages():
    return get_specific_package_info('Upgraded')
