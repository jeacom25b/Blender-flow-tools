import bpy
import bmesh

class BoolKnife(bpy.types.Operator):
    bl_idname = "flol_tools.boolean_knife"
    bl_label = "Boolean Knife"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        ob = context.active_object
        gp = context.active_gpencil_layer
        print(gp)
        if gp:
            strokes = gp.active_frame.strokes
            if len(strokes) > 0:
                bm = bmesh.new()
                last_point = None
                for point in strokes[0].points:
                    point = bm.verts.new(point.co)
                    if last_point:
                        bm.edges.new(last_point, point)
                        last_point = point


        return {"FINISHED"}

class Booleans(bpy.types.Operator):
    bl_idname = "flow_tools.booleans"
    bl_label = ""
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    items = (("INTERSECT", "Intersection", "Intersection"),
             ("UNION", "Union", "Union"),
             ("DIFFERENCE", "Difference", "Differenco"))

    type = bpy.props.EnumProperty(items=items,
                                  name="Type",
                                  default="UNION")
    remove_original = bpy.props.BoolProperty(name="Delete Objects", default=True)

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return [ob.type for ob in context.selected_objects].count("MESH") >= 2 and \
                   context.active_object.type == "MESH"

    def execute(self, context):
        ob = context.active_object
        bpy.ops.object.convert(target="MESH")
        delete = []
        for ob2 in context.selected_objects:
            if ob2.type == "MESH" and ob2 != ob:
                bool = ob.modifiers.new(name="bollad", type="BOOLEAN")
                bool.object = ob2
                bool.operation = self.type
                delete.append(ob2)

        bpy.ops.object.convert(target="MESH")

        if self.remove_original:
            for ob in delete:
                dt = ob.data
                bpy.data.meshes.remove(dt)
                bpy.data.objects.remove(ob)

        return {"FINISHED"}
