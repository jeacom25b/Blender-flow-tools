import bmesh
import bpy


class FieldSampler:
    def __init__(self, object):
        self.bm = bmesh.new()
        self.bm.from_mesh(object.data)
        self.object = object

    def sample_vert(self, vert, normalized=True, cross=False):
        vecs = [face.normal - vert.normal for face in vert.link_faces]
        if normalized or cross:
            bigest = sorted(vecs, key=lambda vec: vec.length_squared)[-1].normalized()
        else:
            bigest = sorted(vecs, key=lambda vec: vec.length_squared)[-1]
        if cross:
            v1 = bigest
            v2 = bigest.cross(vert.normal)
            return (v1, -v1, v2, -v2)

        return bigest

    def choose_verts(self, n):
        scores = []
        for vert in self.bm.verts:
            s = self.sample_vert(vert, normalized=False).length_squared
            scores.append((vert, s))
        scores = sorted(scores, key=lambda pair: pair[1])
        return [pair[0] for pair in scores][-n:]

    def sample_by_proximity(self, co):
        result, location, normal, face_index = self.object.closest_point_on_mesh(co)

        v0 = self.sample_vert(self.bm.faces[face_index].verts[0])

        for vert in self.bm.faces[face_index].verts[1]:
            vs = self.sample_vert(vert, cross=True)
            v0 += sorted(
                [(v, v.dot(v0)) for v in vs],
                key=lambda tuple: tuple[1]
            )[-1]

        return v0 / len(self.bm.faces[face_index].verts)


def copy_mesh(object, copy_data=True):
    cob = object.copy()
    if copy_data:
        cdt = object.data.copy()
        cob.data = cdt
    else:
        ndt = bpy.data.meshes.new(name=object.data.name)
        cob.data = ndt
    bpy.context.scene.objects.link(cob)


def test_field(object):
    sampler = FieldSampler(object)
    dt = bpy.data.meshes.new(name="test_mesh")
    bm = sampler.bm
    verts = sampler.choose_verts(1500)
    for vert in verts:
        vert.select = True

    bm.to_mesh(object.data)


class AutoRetopo(bpy.types.Operator):
    bl_idname = "sculpt_flow.auto_retopo"
    bl_label = "Auto Retopo"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        test_field(context.active_object)
        return {"FINISHED"}
