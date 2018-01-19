'''
Copyright (C) jean Da Costa Machado
Jean3dimensional@gmail.com

Created by Jean Da Costa Machado

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Flow tools",
    "description": "",
    "author": "jean Da Costa Machado",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "View3D",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    "category": "Object"}

# load and reload submodules
##################################

modules = ["remesh",
           "panels",
           "booleans",
           "deform",
           "envelope_builder"]

import importlib

for module in modules:
    if module in locals():
        importlib.reload(locals()[module])
    else:
        exec("from . import %s" % module)
import bpy

# register
##################################

import traceback


def register():
    try:
        bpy.utils.register_module(__name__)
        bpy.app.handlers.scene_update_pre.append(envelope_builder.del_loaded_profile_meshes)
        bpy.app.handlers.scene_update_pre.append(envelope_builder.update_envelope_preview)
        bpy.types.Armature.custom_preview_envelope = bpy.props.BoolProperty()
    except:
        traceback.print_exc()


def unregister():
    try:
        bpy.utils.unregister_module(__name__)
        del bpy.types.Armature.custom_preview_envelope
    except:
        traceback.print_exc()
