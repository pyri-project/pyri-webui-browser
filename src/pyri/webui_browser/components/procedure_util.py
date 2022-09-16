import traceback
import js
from ..util import to_js2
import random
import uuid

async def run_procedure(device_manager, name, vue_py_obj):
    try:
        c = device_manager.get_device_subscription("sandbox").GetDefaultClient()
        gen = await c.async_execute_procedure(name, [], None)

        res = await gen.AsyncNext(None,None)
        await gen.AsyncClose(None)

        if len(res.printed) > 12:
            res_printed = '\n'.join(res.printed[0:12] + ["..."])
        else:
            res_printed = '\n'.join(res.printed)
        if vue_py_obj is None:
            js.window.alert(f"Run procedure {name} complete:\n\n{res_printed}")
        else:
            vue_py_obj.bv_toast.toast(f"Run procedure {name} complete:\n\n{res_printed}",
                to_js2({
                    "title": "Run Procedure Complete",
                    "autoHideDelay": 5000,
                    "appendToToast": True,
                    "variant": "success",
                    "toaster": "b-toaster-bottom-center"
                })
            )
        
    except Exception as e:

        msg = f"Run procedure {name} failed:\n\n{traceback.format_exc()}"
        msg1 = msg.splitlines()
        if len(msg1) > 14:
            msg = "\n".join(msg1[0:14] + ["..."])
        if vue_py_obj is None:
            js.window.alert(msg )
        else:
            vue_py_obj.bv_toast.toast(msg,
                to_js2({
                    "title": "Run Procedure Failed",
                    "autoHideDelay": 5000,
                    "appendToToast": True,
                    "variant": "danger",
                    "toaster": "b-toaster-bottom-center"
                })
            )

async def stop_all_procedure(device_manager):
    try:
        c = device_manager.get_device_subscription("sandbox").GetDefaultClient()
        await c.async_stop_all(None)
       
    except Exception as e:
        
        js.window.alert(f"Stop all procedures failed:\n\n{traceback.format_exc()}" )

async def stop_program_master(device_manager):
    try:
        c = device_manager.get_device_subscription("program_master").GetDefaultClient()
        await c.async_stop(None)
       
    except Exception as e:
        
        js.window.alert(f"Stop program master failed:\n\n{traceback.format_exc()}" )

def do_stop_all(core,device_manager):
    core.create_task(stop_all_procedure(device_manager))
    core.create_task(stop_program_master(device_manager))

def gen_block_uid():

    genUid_soup_ = '!#$%()*+,-./:;=?@[]^_`{|}~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    length = 20
    soupLength = len(genUid_soup_)
    id_ = []
    for i in range(length):
        id_.append(genUid_soup_[random.randrange(0,soupLength)])
    return ''.join(id_)


def new_blockly_procedure(procedure_name, comment):

    block_id = gen_block_uid()
    new_blockly = {
        "blocks": {
            "languageVersion": 0,
            "blocks": [
            {
                "type": "procedures_defnoreturn",
                "id": block_id,
                "x": 20,
                "y": 20,
                "icons": {
                "comment": {
                    "text": comment,
                    "pinned": False,
                    "height": 80,
                    "width": 160
                }
                },
                "fields": {
                "NAME": procedure_name
                }
            }
            ]
        }
    }
    return new_blockly

def rr_uuid_to_py_uuid(rr_uuid):
    uuid_bytes = rr_uuid["uuid_bytes"].tobytes()
    return uuid.UUID(bytes=uuid_bytes)