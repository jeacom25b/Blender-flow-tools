import bpy
import bmesh
import mathutils
from math import sqrt


class HandlerDeform(bpy.types.Operator):
    bl_idname = "flow_tools.handler_deform"
    bl_label = "Handler Deform"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def modal(self, context, event):
        if event.type == "RET":
            context.scene.objects.active = self.ob
            enpty = self.hook.object
            bpy.ops.object.modifier_apply(modifier=self.hook.name)
            self.ob.vertex_groups.remove(self.vg)
            if self.was_dyntopo:
                bpy.ops.sculpt.dynamic_topology_toggle()
            context.scene.objects.unlink(enpty)
            bpy.data.objects.remove(enpty)
            return {"FINISHED"}

        if event.type == "ESC":
            context.scene.objects.active = self.ob
            enpty = self.hook.object
            self.ob.modifiers.remove(self.hook)
            self.ob.vertex_groups.remove(self.vg)
            if self.was_dyntopo:
                bpy.ops.sculpt.dynamic_topology_toggle()
            context.scene.objects.unlink(enpty)
            bpy.data.objects.remove(enpty)
            return {"CANCELLED"}

        return {"PASS_THROUGH"}



    def execute(self, context):
        ob = context.active_object
        sculpt_mode = False

        was_dyntopo = False
        last_mode = ob.mode

        if ob.mode == "SCULPT":
            sculpt_mode = True
            if context.sculpt_object.use_dynamic_topology_sculpting:
                was_dyntopo = True
                bpy.ops.sculpt.dynamic_topology_toggle()

        bm = bmesh.new()
        bm.verts.ensure_lookup_table()
        bm.from_mesh(ob.data)

        mask = bm.verts.layers.paint_mask.verify()
        vg = ob.vertex_groups.new("sculpt_mask_vertex_group")

        center = mathutils.Vector()
        average_normalizer = 0

        for vert in bm.verts:
            weight = 1 - vert[mask]
            center += (vert.co * ob.matrix_world) * weight
            average_normalizer += weight
            vg.add([vert.index], weight, "REPLACE")

        center /= average_normalizer
        radius = 1
        gp = context.active_gpencil_layer

        if gp:
            strokes = gp.active_frame.strokes
            if len(strokes) > 0:
                center = mathutils.Vector()
                for point in strokes[0].points:
                    center += point.co
                center /= len(strokes[0].points)

                radius = 0
                for point in strokes[0].points:
                    radius += (point.co - center).length_squared
                radius /= len(strokes[0].points)
                radius = sqrt(radius)
                strokes.remove(strokes[0])

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=center, radius=radius)

        hook = ob.modifiers.new("handler", "HOOK")
        hook.object = context.active_object
        hook.vertex_group = vg.name
        context.scene.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.object.hook_assign(modifier=hook.name)
        bpy.ops.object.hook_reset(modifier=hook.name)
        bpy.ops.object.mode_set(mode=last_mode)
        context.scene.objects.active = hook.object
        ob.select = False

        self.ob = ob
        self.hook = hook
        self.last_mode = last_mode
        self.vg = vg
        self.was_dyntopo = was_dyntopo

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm= context.window_manager
        wm.event_timer_remove(self._timer)
