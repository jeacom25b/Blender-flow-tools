import bpy
import bmesh


class OptimizedRemesh(bpy.types.Operator):
    bl_idname = "flow_tools.optimized_remesh"
    bl_label = "Optimized Remesh"
    bl_description = ""
    bl_options = {"REGISTER"}

    mode_items = (("BLOCKS", "Blocks", "Blocks"),
                  ("SMOOTH", "Smooth", "Smooth"),
                  ("SHARP", "Sharp", "Sharp"))

    mode = bpy.props.EnumProperty(items=mode_items, name="Mode", description="Remesh mode", default="SMOOTH")
    depth = bpy.props.IntProperty(name="Depth", default=6)
    keep_original = bpy.props.BoolProperty(name="Keep Original", default=False)
    optimize = bpy.props.BoolProperty(name="Optimize Topology", default=True)
    subdivisions = bpy.props.IntProperty(name="Subdivisions", default=1)
    optimize_iterations = bpy.props.IntProperty(name="Optimize Iterations", default=6)
    smooth_iterations = bpy.props.IntProperty(name="Smooth Iterations", default=3)
    smooth_factor = bpy.props.FloatProperty(name="Smooth Factor", default=0.5)

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type in "MESH"

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        ob = context.active_object
        mode = ob.mode
        if ob.type == "MESH":
            n_ob = ob.copy()
            n_dt = n_ob.data.copy()
            n_ob.data = n_dt
            n_ob.modifiers.clear()
            n_ob.select = True
            context.scene.objects.link(n_ob)
            context.scene.objects.active = n_ob
            remesh = n_ob.modifiers.new(type="REMESH", name="Remesh")
            remesh.mode = self.mode
            remesh.octree_depth = self.depth
            bpy.ops.object.convert(target="MESH")

            if self.optimize:
                bm = bmesh.new()
                bm.from_mesh(n_ob.data)
                bm.faces.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.verts.ensure_lookup_table()

                merge_verts = set()
                for edge in bm.edges:
                    if len(edge.link_faces) > 2:
                        edge.verts[0].co = (edge.verts[0].co + edge.verts[1].co)/2
                        edge.verts[1].co = edge.verts[0].co
                        merge_verts.add(edge.verts[0])
                        merge_verts.add(edge.verts[1])

                bmesh.ops.remove_doubles(bm, verts=list(set(merge_verts)), dist=0)

                for _ in range(self.optimize_iterations):
                    merge_verts = set()
                    for face in bm.faces:
                        verts = [loop.vert for loop in face.loops]
                        link_counts = [len(vert.link_edges) for vert in verts]

                        if link_counts.count(3) > 1:
                            ok = True
                            if link_counts[0] == 3 and link_counts[2] == 3:
                                if len(verts[0].link_edges) > 5 or len(verts[2].link_edges) > 5:
                                    diff = verts[0].co - verts[2].co
                                    diff = diff*diff
                                    if diff.x < diff.z or diff.y < diff.z:
                                        ok = False
                                if ok:
                                    verts[0].co += verts[2].co
                                    verts[0].co /= 2
                                    verts[2].co = verts[0].co
                                    merge_verts.add(verts[0])
                                    merge_verts.add(verts[2])

                            elif link_counts[1] == 3 and link_counts[3] == 3:
                                ok = True
                                if link_counts[0] == 3 and link_counts[2] == 3:
                                    if len(verts[0].link_edges) > 5 or len(verts[2].link_edges) > 5:
                                        diff = verts[0].co - verts[2].co
                                        diff = diff * diff
                                        if diff.x < diff.z or diff.y < diff.z:
                                            ok = False
                                if ok:
                                    verts[1].co += verts[3].co
                                    verts[1].co /= 2
                                    verts[3].co = verts[1].co
                                    merge_verts.add(verts[1])
                                    merge_verts.add(verts[3])

                    bmesh.ops.remove_doubles(bm, verts=list(set(merge_verts)), dist=0)

                bm.to_mesh(n_ob.data)

                for _ in range(self.smooth_iterations):
                    sm = n_ob.modifiers.new(type="SMOOTH", name="Smth_mdfr")
                    sm.factor = self.smooth_factor
                    sk = n_ob.modifiers.new(type="SHRINKWRAP", name="srnk_wrp")
                    sk.target = ob
                    sk.wrap_method = "PROJECT"
                    sk.use_negative_direction = True
                    bpy.ops.object.convert(target="MESH")

                if self.subdivisions > 0:
                    n_ob.modifiers.new(type="MULTIRES", name="Multiresolution_0")
                    for _ in range(self.subdivisions):
                        print(bpy.ops.object.multires_subdivide(modifier="Multiresolution_0"))
                        sk = n_ob.modifiers.new(type="SHRINKWRAP", name="Subd_skrp")
                        sk.target = ob
                        sk.wrap_method = "PROJECT"
                        sk.use_negative_direction = True
                        bpy.ops.object.modifier_apply(modifier="Subd_skrp")
                    bpy.ops.object.multires_base_apply(modifier="Multiresolution_0")

            if not self.keep_original:
                dt = ob.data
                bpy.data.objects.remove(ob)
                bpy.data.meshes.remove(dt)

            bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}
