#  Copyright (c) 2021 Richard Smith and others
#
#  This program and the accompanying materials are made available under the
#  terms of the Eclipse Public License 2.0 which is available at
#  http://www.eclipse.org/legal/epl-2.0.
#
#  This Source Code may also be made available under the following Secondary
#  licenses when the conditions for such availability set forth in the Eclipse
#  Public License, v. 2.0 are satisfied: GNU General Public License, version 2
#  with the GNU Classpath Exception which is
#  available at https://www.gnu.org/software/classpath/license.html.
#
#  SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0

from raylib import rl, ffi

from inspect import ismethod, getmembers, isbuiltin
import inflection, sys, json

f = open("raylib.json", "r")
js = json.load(f)




def ctype_to_python_type(t):
    if t == '_Bool':
        return "bool"
    elif t == 'void':
        return 'None'
    elif t == "long":
        return "int"
    elif t == "unsigned long long":
        return "int"
    elif t == "double":
        return "float"
    elif "char *" in t:
        return "str"
    elif "char" in t:
        return "str"  # not sure about this one
    elif "*" in t:
        return "Any"
    elif t.startswith("struct"):
        return t.replace("struct ","")
    elif t.startswith("unsigned"):
        return t.replace("unsigned ", "")
    else:
        return t


print("""from typing import Any

class struct: ...

""")

for name, attr in getmembers(rl):
    uname = name
    if isbuiltin(attr) or str(type(attr)) == "<class '_cffi_backend.__FFIFunctionWrapper'>":
        json_array = [x for x in js['functions'] if x['name'] == name]
        json_object = {}
        if json_array:
            json_object = json_array[0]
        sig = ""
        for i, arg in enumerate(ffi.typeof(attr).args):
            param_name = arg.cname.replace("struct", "").replace("char *", "str").replace("*",
                                                                                          "_pointer").replace(
                " ", "")+"_"+str(i)
            if 'params' in json_object:
                p = json_object['params']
                #print("param_name: ", param_name, "i", i, "params: ",p,file=sys.stderr)
                param_name = list(p)[i]['name']
            param_type = ctype_to_python_type(arg.cname)
            sig += f"{param_name}: {param_type},"

        return_type = ffi.typeof(attr).result.cname
        description = attr.__doc__

        if 'description' in json_object:
            description = json_object['description']

        print(
            f'def {uname}({sig}) -> {ctype_to_python_type(return_type)}:\n        """{description}"""\n        ...')

    elif str(type(attr)) == "<class '_cffi_backend._CDataBase'>":
        return_type = ffi.typeof(attr).result.cname
        print(
            f'def {uname}(*args) -> {ctype_to_python_type(return_type)}:\n        """VARARG FUNCTION - MAY NOT BE SUPPORTED BY CFFI"""\n        ...')
    else:
        #print("*****", str(type(attr)))
        print(f"{name}: {str(type(attr))[8:-2]}")  # this isolates the type

for struct in ffi.list_types()[0]:
    print("processing", struct, file=sys.stderr)
    if ffi.typeof(struct).kind == "struct":
        # if ffi.typeof(struct).fields is None:
        #     print("weird empty struct, skipping", file=sys.stderr)
        #     continue
        print(f"{struct}: struct")
        # sig = ""
        # for arg in ffi.typeof(struct).fields:
        #     sig += ", " + arg[0]
        # print(f"        def __init__(self{sig}):")
        #
        # for arg in ffi.typeof(struct).fields:
        #     print(f"            self.{arg[0]}={arg[0]}")

    elif ffi.typeof(struct).kind == "enum":
        print(f"{struct}: int")
    else:
        print("ERROR UNKNOWN TYPE", ffi.typeof(struct), file=sys.stderr)


