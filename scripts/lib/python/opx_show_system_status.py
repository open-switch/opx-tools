#!/usr/bin/python
import opx_python_common_utils

def get_system_state():
    cmd = "systemctl status"
    ret = opx_python_common_utils.run_cmd_get_output([cmd])    
    for l in ret:
        try:
            (k,v) = l.split(':', 1)
            k = k.strip()
            if k == "State":
                return v.strip()
                
            
        except Exception:
            continue
    return ""
    
def get_failed_services():
    cmd = "systemctl --state=failed"
    ret = opx_python_common_utils.run_cmd_get_output([cmd])
    
    failed_services = []
    for l in ret:
        if '.service' in l:
            try:
                failed_services.append(l.split(' ')[1])
            except Exception:
                pass
    return failed_services           

def get_system_uptime():
    cmd = "/usr/bin/uptime --pretty"
    ret = opx_python_common_utils.run_cmd_get_output([cmd])
    
    for l in ret:
        try:
            uptime = l.split(' ', 1)[1]
            return uptime
            
        except Exception:
            pass
    return ''
