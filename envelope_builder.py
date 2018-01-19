# This module carry the envelope builder code which is no more than an converter for armatures into metabals
# so the user can use armatures like a sort of Basemesh builder.

# The basic idea is to take advantage of the envelope data in an armature and convert it in to a mesh
import os
import bmesh
import mathutils
import math
import bpy


# A simple linear interpolation function
# This is needed for interpolate the radius of the envelope bones
# while adding metabals.
def flerp(a, b, c):
    return a * c + (1 - c) * b


class BoneProfile:
    def __init__(self):
        rn = os.path.realpath(os.path.dirname(__file__))
        path = os.path.join(rn, "bone_profiles", "icosphere.blend")
        with bpy.types.BlendDataLibraries.load(path) as (data_from, data_to):
            data_to.meshes.append("Icosphere")

        self.profiles = {}

        for mesh in data_to.meshes:
            if mesh is None:
                continue
            bm = bmesh.new()
            bm.from_mesh(mesh)

            self.__bm = bm
            self.saved_data_to = data_to

    def bone_to_mesh(self, bone, step_size, min_steps, to_bm, type=None):

        bm = self.__bm

        if bone.parent:
            head_radius = bone.parent.tail_radius
        else:
            head_radius = bone.head_radius

        tail_radius = bone.tail_radius
        length = bone.length
        head = bone.head
        tail = bone.tail

        steps = round(length / step_size)
        if steps < min_steps:
            steps = min_steps

        for step in range(steps + 1):
            new_verts = []

            for vert in bm.verts:
                co = vert.co
                co *= flerp(head_radius, tail_radius, step / steps)
                co += head.lerp(tail, step / steps)
                new_verts.append(to_bm.verts.new(co))

            for edge in bm.edges:
                to_bm.edges.new([new_verts[vert.index] for vert in edge.verts])

            for face in bm.faces:
                to_bm.faces.new([new_verts[vert.index] for vert in face.verts])

        return bm if not to_bm else to_bm


profiles = BoneProfile()


def del_loaded_profile_meshes(scene):
    for mesh in profiles.saved_data_to.meshes:
        bpy.data.meshes.remove(mesh)
    bpy.app.handlers.scene_update_pre.remove(del_loaded_profile_meshes)


@bpy.app.handlers.persistent
def update_envelope_preview(scene):
    ob = scene.objects.active
    if not ob:
        return
    if not "test" in scene.objects:
        return
    test_ob = scene.objects["test"]
    if ob.type == "ARMATURE":
        if ob.mode == "EDIT":
            if ob.data.custom_preview_envelope:
                bm = bmesh.new()
                for bone in ob.data.edit_bones:
                    profiles.bone_to_mesh(bone, 0.05, 10, to_bm=bm)
                bm.to_mesh(test_ob.data)


class EnvelopeAdvancedPreview(bpy.types.Operator):
    bl_idname = "flow_tools.envelope_preview"
    bl_label = "Envelope Preview Toggle"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if context.object.type == "ARMATURE":
            context.object.data.custom_preview_envelope = not context.object.data.custom_preview_envelope
            return {"FINISHED"}


# Add an armature and set it display mode to envelope
class AddEnvelopeArmature(bpy.types.Operator):
    bl_idname = "flow_tools.add_envelope"
    bl_label = "Add Envelope Armature"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    radius = bpy.props.FloatProperty(name="Radius", min=0, default=1)  # The size of the initial bone
    x_mirror = bpy.props.BoolProperty(name="X Mirror", default=True)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.object.armature_add(radius=self.radius)  # Add the armature
        bpy.context.active_object.data.draw_type = "ENVELOPE"  # Set it to envelope display mode
        bpy.context.active_object.data.use_mirror_x = self.x_mirror  # Optionaly enable Mirror option
        return {"FINISHED"}


# Operator that converts bones into chains of metabals
class EnvelopeToMetaball(bpy.types.Operator):
    bl_idname = "flow_tools.envelope_metaball_convert"
    bl_label = "Convert To Metaball"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    step_size = bpy.props.FloatProperty(name="Step Size", default=0.05)  # The size of the steps betwen metabals
    min_steps = bpy.props.IntProperty(name="Minimun Steps", default=10)  # The minimun amount of steps per bone
    resolution = bpy.props.FloatProperty(name="Metabals Resolution", default=20.0)  # Resolution of final mesh
    radius_multiplier = bpy.props.FloatProperty(name="Radius Multiplier", default=1.0)
    metaball_stiffness = bpy.props.FloatProperty(name="Metabals Stifness", default=10)  # The metabal stifness
    theshold = bpy.props.FloatProperty(name="Metabals Threshold", default=0.01)  # Metabal Hardness
    remove_original = bpy.props.BoolProperty(name="Remove original", default=True)  # Optionaly delete original armature

    @classmethod
    def poll(cls, context):
        if context.active_object:
            # only enable This operator if an armature is elected
            return context.active_object.type in ["ARMATURE", "META"]

    def execute(self, context):

        if not context.active_object.type == "ARMATURE":
            return {"CANCELLED"}

        armature = context.active_object  # This is the armature stored in the armature variable
        bpy.ops.object.metaball_add(location=armature.location)  # Add the metabal object
        # So now the active object is the added metabal
        meta = context.active_object  # Store it in an variable for easy handling
        meta.data.elements.remove(meta.data.elements[0])  # So we need to remove the initial element

        # Set some properties mentioned ago.
        meta.data.threshold = self.theshold
        meta.data.resolution = 1 / self.resolution

        for bone in armature.data.bones:  # So we start looping thought the bones

            length = bone.length  # This is the bone length
            # Using the length we can find the number of metas we need to fill it acording to the step size
            step_number = round(length / self.step_size)
            if step_number < self.min_steps:
                step_number = self.min_steps

            # So we start looping thought the steps
            for step in range(step_number + 1):

                # A simple interpolation resolves the next metaball position on the bone
                loc = bone.head_local.lerp(bone.tail_local, step / step_number)

                # We put an metaelement there
                element = meta.data.elements.new()
                element.co = loc

                # get the bone tail radius
                r1 = bone.tail_radius
                # An tricky part is to interpolate the bone head radius,
                # since the bones actualy uses the tail radius of its parent when there is one
                if bone.parent:
                    r2 = bone.parent.tail_radius
                else:
                    r2 = bone.head_radius

                # Use the lerp function created previously to interpolate the radius of the bones
                radius = flerp(r1, r2, step / step_number)
                element.radius = radius * self.radius_multiplier  # Then we set the meta element tadius

                # An final per-element property
                element.stiffness = self.metaball_stiffness

                # If the user wants so, delete the original armature.
        if self.remove_original:
            context.scene.objects.unlink(armature)
            bpy.data.armatures.remove(armature.data)
            bpy.data.objects.remove(armature)

        return {"FINISHED"}
