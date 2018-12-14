# Copyright (c) 2018 Dell Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
# FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
#
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.

import cps
import cps_utils
import cps_object

import sys


###########################################################################
#
# Do CPS API get request
#

def cps_get(q, obj, attrs={}):
    resp = []
    return resp if cps.get([cps_object.CPSObject(obj,
                                                 qual=q,
                                                 data=attrs
                                             ).get()
                        ], resp
    ) else None

###########################################################################
#
# Extract the given attribute from a CPS API get response
#

def cps_attr_data_get(obj, attr):
    d = obj['data']
    if attr not in d:
        return None
    a = d[attr]
    if type(a) == list:
        return map(lambda x: cps_utils.cps_attr_types_map.from_data(attr, x), a)
    return cps_utils.cps_attr_types_map.from_data(attr, d[attr])

###########################################################################
#
# Extract the given key attribute from a CPS API get response
#

def cps_key_attr_data_get(obj, attr):
    d = obj['data']
    if 'cps/key_data' in d and attr in d['cps/key_data']:
        return cps_utils.cps_attr_types_map.from_data(attr, d['cps/key_data'][attr])
    if attr not in d:
        return None
    return cps_utils.cps_attr_types_map.from_data(attr, d[attr])


def cps_set(obj, qual, data):
    return (cps_utils.CPSTransaction([('set',
                cps_object.CPSObject(obj, qual=qual, data=data).get())]).commit()
            )


class Struct:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def port_name_to_type(nm):
    li = nm.split('.')
    n = len(li)
    if n < 1 or n > 2:
        return None
    if n == 2:
        return 'vlan' if port_name_to_type(li[0]) in ['e', 'bond'] else None
    n = len(nm)
    if n > 1 and nm[0] == 'e':
        return 'e'
    if n > 2 and nm[0:2] == 'br':
        return 'br'
    if n > 4 and nm[0:4] == 'bond':
        return 'bond'
    return None


def port_name_canonical(nm):
    t = port_name_to_type(nm)
    if t == 'e':
        s = nm[1:].split('-')
        if len(s) != 3:
            return None
        try:
            n = map(lambda x: int(x), s)
        except:
            return None
        return 'e{:03d}-{:03d}-{:1d}'.format(n[0], n[1], n[2])
    if t == 'br':
        try:
            n = int(nm[2:])
        except:
            return None
        return 'br{}'.format(n)
    if t == 'bond':
        try:
            n = int(nm[4:])
        except:
            return None
        return 'bond{}'.format(n)
    if t == 'vlan':
        s = nm.split('.')
        parent = port_name_canonical(s[0])
        if parent is None:
            return None
        try:
            vid = int(s[1])
        except:
            return None
        return '{}.{}'.format(parent, vid)
    return None


def _port_range_str_to_port_list(s, port_types):
    resp = cps_get('target',
                   'dell-base-if-cmn/if/interfaces/interface',
                   {}
                   )
    if resp is None or len(resp) == 0:
        return []
    port_names = []
    port_idxs = {}
    for r in resp:
        nm = cps_key_attr_data_get(r, 'if/interfaces/interface/name')
        t  = port_name_to_type(nm)
        if t == 'br' and (port_types is None or 'vlan' in port_types):
            vid = int(nm[2:])
            d = r['data']
            port_names += map(lambda x: '{}.{}'.format(str(x)[:-1], vid), d.get('dell-if/if/interfaces/interface/tagged-ports', []))
            port_names += map(lambda x: '{}.{}'.format(str(x)[:-1], vid), d.get('dell-if/if/interfaces/interface/untagged-ports', []))
        if port_types is not None and t not in port_types:
            continue
        port_names.append(nm)
        port_idxs[nm] = cps_key_attr_data_get(r, 'dell-base-if-cmn/if/interfaces/interface/if-index')
    port_names.sort()
    result = []
    if s is None:
        for nm in port_names:
            s = Struct(name=nm)
            if nm in port_idxs:
                s.idx = port_idxs[nm]
            result.append(s)
    else:
        for r in s.split(','):
            rr = r.split('..')
            if len(rr) < 1 or len(rr) > 2:
                return None
            if len(rr) == 1:
                rr = [rr[0], rr[0]]
            t1 = port_name_to_type(rr[0])
            t2 = port_name_to_type(rr[1])
            if t1 is None or t2 is None or t2 != t1:
                return None
            c1 = port_name_canonical(rr[0])
            c2 = port_name_canonical(rr[1])
            if c1 not in port_names or c2 not in port_names:
                return None
            i1 = port_names.index(c1)
            i2 = port_names.index(c2)
            while i1 <= i2:
                nm = port_names[i1]
                s = Struct(name=nm)
                if nm in port_idxs:
                    s.idx = port_idxs[nm]
                result.append(s)
                i1 += 1
    return result


###########################################################################
#
# Convert a string into a list of instances of Struct, each instance having
#   .name  (required) Interface name, string
#   .index (optional) Interface index, integer
# s         - Input string, of the form 'aaa,bbb..ccc, ...'
# port_type - List of acceptable port types, each type is a string, one of:
#   'e'    - Ethernet interfaces
#   'bond' - LAG intefaces
#   'br'   - Bridges
#   'vlan' - Bridge (VLAN) member interfaces

def port_range_str_to_port_list(s, port_types):
    result = _port_range_str_to_port_list(s, port_types)
    if result is None:
        print  >> sys.stderr, 'Syntax error in port list, or invalid port(s)'
        sys.exit(1)
    return result


def cjoin(s1, sep, s2):
    return s2 if s1 == '' else s1 + sep + s2


def _attr_val_to_str(val, fmt=None, map=None, func=None):
    if map is not None:
        val = map.get(val, 'UNKNOWN')
    elif func is not None:
        val = func(val)
    if fmt is None:
        fmt = '{}'
    return fmt.format(val)


def attr_val_to_str(val, fmt=None, map=None, func=None):
    if type(val) == list:
        result = ''
        for x in val:
            result = cjoin(result, ' ', _attr_val_to_str(x, fmt, map, func))
        return result
    return _attr_val_to_str(val, fmt, map, func)
    

_indent_width = 4
_indent_str   = _indent_width * ' '

def print_indent(lvl):
    sys.stdout.write(lvl * _indent_str)
        

def print_section_attr(lvl, heading, heading_width, val, map=None, func=None, suffix=None):
    heading += ':'
    ldr = lvl * _indent_str
    vldr = ldr + heading_width * ' '
    out = ('{}{:' + str(heading_width - 1) +'}').format(ldr, heading)
    for w in attr_val_to_str(val, None, map, func).split(' '):
        out2 = out + ' ' + w
        if len(out2) > 80:
            sys.stdout.write(out)
            print
            out = vldr + w
        else:
            out = out2
    sys.stdout.write(out)
    if suffix is not None:
        sys.stdout.write(' ')
        sys.stdout.write(suffix)
    print


def print_section_heading(lvl, s):
    print_indent(lvl)
    print s
    

###########################################################################
#
# Print a section of non-summary output
#
# lvl           - Indentation level, non-negative integer
# heading       - Section heading, string
# li            - List of instances of Struct, each instance having
#                 attribute(s):
#                   .heading (required) Value heading
#                   .value   (required) Value to print
#                   .outmap  (optional) Dictionary to map value to output
#                   .func    (optional) Function to map value to output
#                   .suffix  (optional) Suffix, typically units
# heading_width - Optional width for value headings, calculated if not given

def print_section(lvl, heading, li, heading_width=None):
    print_section_heading(lvl, heading)
    if heading_width is None:
        heading_width = max(map(lambda x: len(x.heading), li)) + 2
    lvl += 1
    for x in li:
        print_section_attr(lvl, x.heading, heading_width, x.value, getattr(x, 'outmap', None), getattr(x, 'func', None), getattr(x, 'suffix', None))


def _split(s, n, d):
    li = s.split(d)
    s = ''
    while len(li) > 0:
        if d == ' ':
            ss = cjoin(s, ' ', li[0])
        else:
            ss = s + li[0]
            if len(li) > 1:
                ss += d
        if len(ss) > n:
            break
        s = ss
        li.pop(0)
    return [s, d.join(li)]
            

def print_summary_line(r, fs):
    ncol = len(fs)
    while reduce(lambda u, v: u + v, map(lambda x: len(x), r)) > 0:
        i = 0
        while  i < ncol:
            if i >  0:
                sys.stdout.write(' | ')
            n = fs[i]
            s = ''
            for d in [' ', '-', ':']:
                li = _split(r[i], n, d)
                if len(li[0]) > len(s):
                    s   = li[0]
                    rem = li[1]
            if s != '':
                r[i] = rem
            else:
                s = r[i][0:n]
                r[i] = r[i][n:]
            sys.stdout.write(('{:' + str(n) + '}').format(s))
            i += 1
        print
        

###########################################################################
#
# Print a summary table
#
# headings - List of column headings (strings)
# values   - 2D array (list of lists) of values to print, rows are lines of
#            output
# outmaps  - List of dictionaries for mapping values to output, one
#            dictionary per column
# funcs    - List of functions for mapping values to output, one function
#            per column

def print_summary(headings, values, outmaps=None, funcs=None):
    nf = len(headings)
    a = [nf * [''] for i in range(len(values))]
    fs = map(lambda x: len(x), headings)
    om = nf * [None] if outmaps is None else outmaps
    ff = nf * [None] if funcs is None else funcs
    i = 0
    for v in values:
        j = 0
        while j < nf:
            s = attr_val_to_str(v[j], None, om[j], ff[j])
            a[i][j] = s
            n = len(s)
            if n > fs[j]:
                fs[j] = n
            j += 1
        i += 1
    while True:
        w = reduce(lambda x, y: x + y, fs) + 3 * (nf - 1)
        if w <= 80:
            break
        fsmax = max(fs)
        li = fs
        i = None
        while fsmax in li:
            i = li.index(fsmax)
            li = li[(i + 1):]
        fs[i] /= 2
    print_summary_line(headings, fs)
    print w * '-'
    for r in a:
        print_summary_line(r, fs)


def chk_set(str, _set):
    li2 = str.split(',')
    set2 = set(li2)
    return len(set2) == len(li2) and set2 <= _set
