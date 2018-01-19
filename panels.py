import bpy

# Panels of the addon
class FlowPanel(bpy.types.Panel):
    bl_idname = "flow_tools.panel"
    bl_label = "Experimental Flow Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"

    # Nothing really intresting to coment here.
    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.label("mesh Building")
        col.separator()

        col.operator("flow_tools.optimized_remesh")
        
        row = col.row(align=True)
        row.operator("flow_tools.booleans", "Union").type = "UNION"
        row.operator("flow_tools.booleans", "Difference").type = "DIFFERENCE"
        row.operator("flow_tools.booleans", "intersection").type = "INTERSECT"

        col.separator()
        col.label("Envlope Builder")

        col.operator("flow_tools.add_envelope")
        col.operator("flow_tools.envelope_metaball_convert")
        col.operator("object.convert", "Convert To Mesh").target = "MESH"

        col.separator()
        col.label("Deform")
        col.operator("flow_tools.handler_deform")
