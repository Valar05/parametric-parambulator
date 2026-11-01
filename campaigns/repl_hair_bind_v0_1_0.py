#!/usr/bin/env python3
"""Repl hair-only automatic skinning campaign v0.1.0.

Respectful mission:
  1. Verify the exact owner's Repl.glb byte identity and GLB structure.
  2. Derive attachment-root-guided mane/tail weights from EXISTING axial bones.
  3. Preserve every original body vertex, body weight, texture and bone.
  4. Bake a gentle neck/head-only review animation, NOT a hoof or gait action.
  5. Check rest-pose parity, hoof stillness, seam continuity and finite motion.
  6. Publish a derived GLB, offline moving-mesh viewer and honest receipts.

No source overwrite, Blender requirement, new bones, cloth, shader or Git writes.
The script can run directly in Termux Python 3.10+ with only standard library.
Physical viewing and acceptance are NEVER inferred from numeric checks.
"""

from __future__ import annotations
import argparse
import datetime as datetime_module
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import traceback

VERSION = "0.1.0"
CAMPAIGN = "REPL_HAIR_AXIAL_BIND"
SOURCE_SHA256 = "d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f"
EXPECTED_BODY_VERTICES = 6082
EXPECTED_HAIR_VERTICES = 1819
EXPECTED_HAIR_TRIANGLES = 1207
EXPECTED_JOINTS = 43
MANE_BONES = ("Bone_001", "Bone_003", "Bone_002",
              "Bone_010", "Bone_009", "Bone_008", "Bone_007")
TAIL_BONES = ("Bone_001", "Bone_006", "Bone_005", "Bone_004")
MOTION_BONES = ("Bone_010", "Bone_009", "Bone_008", "Bone_007")
ROOT_RADIUS = {"mane": 0.115, "tail": 0.165}
MAX_ORPHAN_GAP = 0.26
WELD_DIGITS = 5
MAX_INFLUENCES = 4
POSE_TIMES = (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
SUPPORTED_PYTHON = (3, 10)


class Blocked(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def need(condition, code: str, explanation: str = "") -> None:
    if not condition:
        raise Blocked(code + (": " + explanation if explanation else ""))


def now_utc() -> str:
    return datetime_module.datetime.now(datetime_module.timezone.utc).isoformat()


def glb_load(path: Path):
    source = path.read_bytes()
    need(sha256(source) == SOURCE_SHA256, "SOURCE_SHA_MISMATCH",
         "Refusing to use an unrecognized or modified Repl.glb.")
    need(source[:4] == b"glTF", "INVALID_GLB_MAGIC")
    _magic, version, declared = struct.unpack_from("<4sII", source)
    need(version == 2 and declared == len(source), "INVALID_GLB_HEADER")
    pieces = []
    offset = 12
    while offset < len(source):
        need(offset + 8 <= len(source), "TRUNCATED_CHUNK_HEADER")
        size, typ = struct.unpack_from("<I4s", source, offset)
        offset += 8
        need(offset + size <= len(source), "TRUNCATED_CHUNK")
        pieces.append((typ, source[offset:offset + size]))
        offset += size
    need(len(pieces) == 2 and pieces[0][0] == b"JSON"
         and pieces[1][0] == b"BIN\x00", "UNSUPPORTED_GLB_CHUNKS")
    doc = json.loads(pieces[0][1])
    binary = pieces[1][1]
    need(len(doc.get("buffers", [])) == 1, "UNEXPECTED_BUFFER_COUNT")
    need(len(doc.get("nodes", [])) == 46, "NODE_COUNT_CHANGED")
    need(len(doc.get("skins", [])) == 1 and
         len(doc["skins"][0]["joints"]) == EXPECTED_JOINTS,
         "SKIN_IDENTITY_CHANGED")
    need(len(doc.get("meshes", [])) == 2, "MESH_COUNT_CHANGED")
    need(not doc.get("animations"), "UNEXPECTED_SOURCE_ANIMATIONS",
         "This campaign must not replace an existing animation.")
    body = doc["meshes"][0]["primitives"][0]
    hair = doc["meshes"][1]["primitives"][0]
    need(doc["nodes"][43].get("mesh") == 0
         and doc["nodes"][43].get("skin") == 0
         and doc["nodes"][45].get("mesh") == 1
         and doc["nodes"][45].get("skin") is None,
         "SOURCE_MESH_NODE_MAPPING_CHANGED")
    need("JOINTS_0" in body["attributes"] and
         "WEIGHTS_0" in body["attributes"] and
         "JOINTS_0" not in hair["attributes"] and
         "WEIGHTS_0" not in hair["attributes"],
         "SOURCE_SKIN_LAYOUT_CHANGED")
    return source, doc, binary


COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
             5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
          "MAT4": 16}


def accessor(doc, binary, number):
    a = doc["accessors"][number]
    need(not a.get("sparse"), "SPARSE_ACCESSOR_UNSUPPORTED")
    b = doc["bufferViews"][a["bufferView"]]
    fmt, item_size = COMPONENT[a["componentType"]]
    width = WIDTHS[a["type"]]
    stride = b.get("byteStride", item_size * width)
    base = b.get("byteOffset", 0) + a.get("byteOffset", 0)
    need(stride >= item_size * width, "BAD_ACCESSOR_STRIDE")
    need(base + max(0, a["count"] - 1) * stride + item_size * width
         <= len(binary), "ACCESSOR_OUT_OF_BOUNDS")
    unpacker = struct.Struct("<" + fmt * width)
    return [unpacker.unpack_from(binary, base + i * stride)
            for i in range(a["count"])]


def emit_accessor(doc, binary: bytearray, rows, component_type, kind,
                  target=None):
    fmt, size = COMPONENT[component_type]
    width = WIDTHS[kind]
    packer = struct.Struct("<" + fmt * width)
    while len(binary) % 4:
        binary.append(0)
    start = len(binary)
    for row in rows:
        need(len(row) == width, "ACCESSOR_WIDTH_ERROR")
        binary.extend(packer.pack(*row))
    view = {"buffer": 0, "byteOffset": start,
            "byteLength": len(binary) - start}
    if target:
        view["target"] = target
    view_id = len(doc["bufferViews"])
    doc["bufferViews"].append(view)
    acc = {"bufferView": view_id, "componentType": component_type,
           "count": len(rows), "type": kind}
    acc_id = len(doc["accessors"])
    doc["accessors"].append(acc)
    return acc_id


def glb_encode(doc, binary: bytes) -> bytes:
    doc["buffers"][0]["byteLength"] = len(binary)
    jb = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf8")
    jb += b" " * ((-len(jb)) % 4)
    bb = binary + b"\x00" * ((-len(binary)) % 4)
    size = 12 + 8 + len(jb) + 8 + len(bb)
    return (struct.pack("<4sII", b"glTF", 2, size)
            + struct.pack("<I4s", len(jb), b"JSON") + jb
            + struct.pack("<I4s", len(bb), b"BIN\x00") + bb)


def length2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def distance(a, b):
    return math.sqrt(length2(a, b))


def key3(p):
    return tuple(round(float(c), WELD_DIGITS) for c in p)


def normalize(weights):
    pairs = sorted(((int(k), float(v)) for k, v in weights.items()
                    if v > 1e-10), key=lambda pair: -pair[1])[:MAX_INFLUENCES]
    total = sum(v for _, v in pairs)
    need(total > 1e-10, "ZERO_AXIAL_INFLUENCE")
    return {k: v / total for k, v in pairs}


def select_pool(body_positions, body_joint_ids, body_weights, allowed):
    pool = []
    for i, point in enumerate(body_positions):
        weight = {}
        for joint, amount in zip(body_joint_ids[i], body_weights[i]):
            if joint in allowed and amount > 0:
                weight[joint] = weight.get(joint, 0.0) + float(amount)
        if sum(weight.values()) >= 0.65:
            pool.append((point, normalize(weight)))
    need(len(pool) >= 50, "AXIAL_SOURCE_POOL_TOO_SMALL",
         "The expected neck/spine body weights were not found.")
    return pool


def nearest_root_weights(point, pool):
    nearest = []
    for source_position, weights in pool:
        d2 = length2(point, source_position)
        if len(nearest) < 4:
            nearest.append((d2, weights))
            nearest.sort(key=lambda x: x[0])
        elif d2 < nearest[-1][0]:
            nearest[-1] = (d2, weights)
            nearest.sort(key=lambda x: x[0])
    need(bool(nearest), "NO_BODY_SOURCE")
    weighted = {}
    for d2, weights in nearest:
        factor = 1.0 / (d2 + 0.00005)
        for joint, value in weights.items():
            weighted[joint] = weighted.get(joint, 0.0) + factor * value
    return math.sqrt(nearest[0][0]), normalize(weighted)


def hair_graph(positions, indices):
    points = []
    mapping = {}
    vertex_to_weld = []
    for point in positions:
        key = key3(point)
        if key not in mapping:
            mapping[key] = len(points)
            points.append(tuple(float(x) for x in point))
        vertex_to_weld.append(mapping[key])
    edges = [dict() for _ in points]
    need(len(indices) % 3 == 0, "HAIR_INDEX_NOT_TRIANGLES")
    for start in range(0, len(indices), 3):
        ids = [vertex_to_weld[int(x)] for x in indices[start:start + 3]]
        for a, b in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            if a == b:
                continue
            d = max(distance(points[a], points[b]), 1e-6)
            edges[a][b] = min(edges[a].get(b, math.inf), d)
            edges[b][a] = min(edges[b].get(a, math.inf), d)
    return points, vertex_to_weld, edges


def assign_region(points, edges, members, pool, label):
    """Propagate actual axial body-skin influence from roots over hair sheets."""
    members = set(members)
    roots = {}
    for vertex_id in sorted(members):
        d, weights = nearest_root_weights(points[vertex_id], pool)
        if d <= ROOT_RADIUS[label]:
            roots[vertex_id] = weights
    need(len(roots) >= (15 if label == "tail" else 40),
         label.upper() + "_ROOTS_INSUFFICIENT",
         "The mesh/root association differs from the studied Repl source.")
    best = {i: math.inf for i in members}
    origin = {}
    heap = []
    for k in roots:
        best[k] = 0.0
        origin[k] = k
        heapq.heappush(heap, (0.0, k, k))
    while heap:
        travelled, i, root = heapq.heappop(heap)
        if travelled > best[i] + 1e-9:
            continue
        for neighbor, length in edges[i].items():
            if neighbor not in members:
                continue
            trial = travelled + length
            if trial + 1e-9 < best[neighbor]:
                best[neighbor] = trial
                origin[neighbor] = root
                heapq.heappush(heap, (trial, neighbor, root))
    disconnected = [i for i in members if i not in origin]
    # Original hair contains tiny isolated triangle islands. Give each a
    # nearest same-region ROOT witness only if genuinely spatially close.
    for i in disconnected:
        candidates = sorted((length2(points[i], points[j]), j)
                            for j in origin)
        need(bool(candidates) and
             math.sqrt(candidates[0][0]) <= MAX_ORPHAN_GAP,
             label.upper() + "_UNRESOLVED_HAIR_ISLAND",
             "An isolated piece has no trustworthy nearby root.")
        origin[i] = origin[candidates[0][1]]
        best[i] = math.sqrt(candidates[0][0])
    result = {i: dict(roots[origin[i]]) for i in members}
    # Gentle graph smoothing; roots stay immutable. Different regions
    # never share data and duplicated UV seam positions share one vertex ID.
    for _ in range(16):
        next_result = dict(result)
        for i in members:
            if i in roots or not edges[i]:
                continue
            accum = {}
            strength = 0.0
            for j, segment in edges[i].items():
                if j not in members:
                    continue
                influence = 1.0 / max(segment, 0.002)
                strength += influence
                for bone, amount in result[j].items():
                    accum[bone] = accum.get(bone, 0.0) + influence * amount
            if strength:
                next_result[i] = normalize({
                    bone: 0.6 * result[i].get(bone, 0.0)
                          + 0.4 * value / strength
                    for bone, value in
                    {**result[i], **accum}.items()
                    for value in [accum.get(bone, 0.0)]
                })
        result = next_result
    return result, {"seeds": len(roots),
                    "rootless_spatial_islands": len(disconnected),
                    "max_surface_distance": max(best.values()),
                    "welded_vertices": len(members)}


def bind_hair(doc, binary):
    body = doc["meshes"][0]["primitives"][0]
    hair = doc["meshes"][1]["primitives"][0]
    body_pos = accessor(doc, binary, body["attributes"]["POSITION"])
    body_joint_ids = accessor(doc, binary, body["attributes"]["JOINTS_0"])
    body_weights = accessor(doc, binary, body["attributes"]["WEIGHTS_0"])
    hair_pos = accessor(doc, binary, hair["attributes"]["POSITION"])
    hair_indices = [row[0] for row in accessor(doc, binary, hair["indices"])]
    need(len(body_pos) == EXPECTED_BODY_VERTICES
         and len(hair_pos) == EXPECTED_HAIR_VERTICES
         and len(hair_indices) == EXPECTED_HAIR_TRIANGLES * 3,
         "ASSET_GEOMETRY_COUNTS_CHANGED")
    skin_joint_nodes = doc["skins"][0]["joints"]
    names = {doc["nodes"][node]["name"]: i
             for i, node in enumerate(skin_joint_nodes)}
    need(all(name in names for name in MANE_BONES + TAIL_BONES + MOTION_BONES),
         "AXIAL_BONE_NAMES_CHANGED")
    pools = {}
    for label, allowed_names in (("mane", MANE_BONES), ("tail", TAIL_BONES)):
        pools[label] = select_pool(
            body_pos, body_joint_ids, body_weights,
            {names[n] for n in allowed_names})
    welded, lookup, edges = hair_graph(hair_pos, hair_indices)
    groups = {
        "mane": [i for i, p in enumerate(welded) if p[2] >= -0.65],
        "tail": [i for i, p in enumerate(welded) if p[2] < -0.65]
    }
    need(len(groups["mane"]) > 300 and len(groups["tail"]) > 300,
         "MANE_TAIL_REGIONS_CHANGED")
    weights = {}
    stats = {}
    for label, members in groups.items():
        local, info = assign_region(welded, edges, members, pools[label], label)
        weights.update(local)
        stats[label] = info
    rows_joints = []
    rows_weights = []
    counts = {"mane": {}, "tail": {}}
    for i, point in enumerate(hair_pos):
        w = weights[lookup[i]]
        row = sorted(w.items(), key=lambda p: -p[1])[:4]
        joint_row = [k for k, _ in row]
        weight_row = [v for _, v in row]
        while len(joint_row) < 4:
            joint_row.append(0)
            weight_row.append(0.0)
        need(abs(sum(weight_row) - 1) < 1e-5, "WEIGHT_SUM_INVALID")
        label = "mane" if point[2] >= -0.65 else "tail"
        allowed_names = MANE_BONES if label == "mane" else TAIL_BONES
        need(all(doc["nodes"][skin_joint_nodes[k]]["name"] in allowed_names
                 for k, v in row if v > 1e-8),
             "LEG_WEIGHT_CONTAMINATION")
        for j, v in row:
            name = doc["nodes"][skin_joint_nodes[j]]["name"]
            counts[label][name] = counts[label].get(name, 0) + v
        rows_joints.append(tuple(joint_row))
        rows_weights.append(tuple(weight_row))
    return rows_joints, rows_weights, stats, counts, hair_pos, body_pos


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by,
            aw*by - ax*bz + ay*bw + az*bx,
            aw*bz + ax*by - ay*bx + az*bw,
            aw*bw - ax*bx - ay*by - az*bz)


def axisq(axis, degrees):
    angle = math.radians(degrees) / 2
    s = math.sin(angle)
    return (axis[0]*s, axis[1]*s, axis[2]*s, math.cos(angle))


def node_rotation(node):
    return tuple(node.get("rotation", (0, 0, 0, 1)))


def make_animation(doc, binary, names_to_nodes):
    # No legs, limb parents or root transforms are keyed.
    pitch = (0, 4, 7, 0, -6, -3, 0)
    yaw = (0, 2, 0, -3, 0, 2, 0)
    multipliers = {"Bone_010": 0.40, "Bone_009": 0.72,
                   "Bone_008": 0.85, "Bone_007": 0.65}
    times_id = emit_accessor(doc, binary, [(x,) for x in POSE_TIMES],
                             5126, "SCALAR")
    samplers = []
    channels = []
    keyframes = {}
    for name in MOTION_BONES:
        node_id = names_to_nodes[name]
        baseline = node_rotation(doc["nodes"][node_id])
        q = []
        for pitch_deg, yaw_deg in zip(pitch, yaw):
            s = multipliers[name]
            rotation = qmul(baseline,
                            qmul(axisq((1, 0, 0), pitch_deg * s),
                                 axisq((0, 0, 1), yaw_deg * s)))
            norm = math.sqrt(sum(v*v for v in rotation))
            q.append(tuple(v / norm for v in rotation))
        keyframes[node_id] = q
        rotation_id = emit_accessor(doc, binary, q, 5126, "VEC4")
        sampler_index = len(samplers)
        samplers.append({"input": times_id, "output": rotation_id,
                         "interpolation": "LINEAR"})
        channels.append({"sampler": sampler_index,
                         "target": {"node": node_id, "path": "rotation"}})
    doc["animations"] = [{"name": "REPL_HAIR_BIND_NECK_REVIEW_NO_HOOF_MOTION",
                          "samplers": samplers, "channels": channels,
                          "extras": {
                              "intent": "Gentle neck/head range-of-motion only",
                              "no_hoof_animation": True,
                              "human_acceptance": "PENDING"}}]
    return keyframes


def matrix_mult(a, b):
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r*4+c] = sum(a[r*4+k] * b[k*4+c] for k in range(4))
    return out


def trs_matrix(node, rotation=None):
    x,y,z,w = rotation if rotation is not None else node_rotation(node)
    t = node.get("translation", (0,0,0))
    s = node.get("scale", (1,1,1))
    # glTF matrices are column major. Internally use row-major here.
    return [(1-2*(y*y+z*z))*s[0], 2*(x*y-z*w)*s[1],
             2*(x*z+y*w)*s[2], t[0],
            2*(x*y+z*w)*s[0], (1-2*(x*x+z*z))*s[1],
             2*(y*z-x*w)*s[2], t[1],
            2*(x*z-y*w)*s[0], 2*(y*z+x*w)*s[1],
             (1-2*(x*x+y*y))*s[2], t[2],
            0,0,0,1]


IDENTITY = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]


def parent_map(nodes):
    result = {}
    for i, n in enumerate(nodes):
        for child in n.get("children", []):
            need(child not in result, "MULTIPLE_NODE_PARENTS")
            result[child] = i
    return result


def quat_slerp(a, b, f):
    dot = sum(x*y for x,y in zip(a,b))
    if dot < 0:
        b = tuple(-v for v in b)
        dot = -dot
    if dot > 0.9995:
        q = [x*(1-f) + y*f for x,y in zip(a,b)]
    else:
        theta = math.acos(max(-1,min(1,dot)))
        den = math.sin(theta)
        q = [math.sin((1-f)*theta)/den*x
             + math.sin(f*theta)/den*y for x,y in zip(a,b)]
    scale = math.sqrt(sum(x*x for x in q))
    return tuple(x / scale for x in q)


def rotations_at(t, keyframes):
    low = max(i for i,x in enumerate(POSE_TIMES) if x <= t)
    high = min(low+1, len(POSE_TIMES)-1)
    f = 0.0 if low == high else (t-POSE_TIMES[low])/(POSE_TIMES[high]-POSE_TIMES[low])
    return {node: quat_slerp(q[low], q[high], f)
            for node,q in keyframes.items()}


def world_matrices(doc, overrides):
    nodes = doc["nodes"]
    parents = parent_map(nodes)
    cache = {}
    def visit(node_id):
        if node_id not in cache:
            node = nodes[node_id]
            if "matrix" in node:
                raw = node["matrix"]
                local = [raw[4*c+r] for r in range(4) for c in range(4)]
            else:
                local = trs_matrix(node, overrides.get(node_id))
            parent_id = parents.get(node_id)
            cache[node_id] = matrix_mult(
                visit(parent_id), local) if parent_id is not None else local
        return cache[node_id]
    for i in range(len(nodes)):
        visit(i)
    return cache


def apply_matrix(m, p):
    x,y,z = p
    return (m[0]*x+m[1]*y+m[2]*z+m[3],
            m[4]*x+m[5]*y+m[6]*z+m[7],
            m[8]*x+m[9]*y+m[10]*z+m[11])


def skin_matrices(doc, binary, worlds):
    skin = doc["skins"][0]
    inverse = accessor(doc, binary, skin["inverseBindMatrices"])
    need(len(inverse) == EXPECTED_JOINTS, "INVERSE_BIND_COUNT_CHANGED")
    out = []
    for node_id, packed in zip(skin["joints"], inverse):
        matrix = [packed[4*c+r] for r in range(4) for c in range(4)]
        out.append(matrix_mult(worlds[node_id], matrix))
    return out


def deform_vertex(point, joints, weights, matrices):
    xyz = [0.0, 0.0, 0.0]
    for j, w in zip(joints, weights):
        if w == 0:
            continue
        p = apply_matrix(matrices[j], point)
        for axis in range(3):
            xyz[axis] += w * p[axis]
    return tuple(xyz)


def validate_motion(doc, binary, rows_joints, rows_weights,
                    hair_positions, body_positions, keyframes):
    body = doc["meshes"][0]["primitives"][0]
    body_j = accessor(doc, binary, body["attributes"]["JOINTS_0"])
    body_w = accessor(doc, binary, body["attributes"]["WEIGHTS_0"])
    hoof_samples = [i for i,p in enumerate(body_positions) if p[1] < 0.12]
    need(len(hoof_samples) > 50, "HOOF_WITNESSES_MISSING")
    baseline_world = world_matrices(doc, {})
    baseline_mat = skin_matrices(doc, binary, baseline_world)
    max_rest_error = max(distance(
        hair_positions[i],
        deform_vertex(hair_positions[i], rows_joints[i], rows_weights[i], baseline_mat))
        for i in range(len(hair_positions)))
    need(max_rest_error < 0.0003, "HAIR_REST_POSE_DRIFT",
         "Binding changed the rest silhouette.")
    limb_node_names = ("Bone_011", "Bone_017", "Bone_033", "Bone_038")
    name_to_node = {n.get("name"):i for i,n in enumerate(doc["nodes"])}
    hoof_nodes = [name_to_node[n] for n in limb_node_names]
    hoof_original = {
        i:tuple(baseline_world[i][v] for v in (3,7,11))
        for i in hoof_nodes}
    sample_times = [k*0.125 for k in range(25)]
    max_hoof_vertex_drift = 0.0
    max_hoof_node_drift = 0.0
    max_hair_displacement = 0.0
    frames = []
    body_step = tuple(range(0, len(body_positions), 8))
    for t in sample_times:
        pose_world = world_matrices(doc, rotations_at(t,keyframes))
        matrices = skin_matrices(doc,binary,pose_world)
        for node_id in hoof_nodes:
            pos = tuple(pose_world[node_id][v] for v in (3,7,11))
            max_hoof_node_drift = max(max_hoof_node_drift,
                                      distance(pos,hoof_original[node_id]))
        for i in hoof_samples:
            p = deform_vertex(body_positions[i],body_j[i],body_w[i],matrices)
            max_hoof_vertex_drift = max(max_hoof_vertex_drift,
                                         distance(p,body_positions[i]))
        moving_hair = [
            deform_vertex(hair_positions[i],rows_joints[i],rows_weights[i],matrices)
            for i in range(len(hair_positions))]
        need(all(math.isfinite(v) for p in moving_hair for v in p),
             "NONFINITE_SKIN_MOTION")
        max_hair_displacement = max(max_hair_displacement,
            max(distance(a,b) for a,b in zip(hair_positions,moving_hair)))
        moving_body = [
            deform_vertex(body_positions[i],body_j[i],body_w[i],matrices)
            for i in body_step]
        # Store true skinned positions for a self-contained, OFFLINE diagnostic.
        frames.append({"time":round(t,3),
                       "body":[[round(v,4) for v in p] for p in moving_body],
                       "hair":[[round(v,4) for v in p] for p in moving_hair]})
    need(max_hoof_node_drift < 1e-6, "HOOF_BONE_MOVEMENT")
    need(max_hoof_vertex_drift < 0.0003, "HOOF_VERTEX_MOVEMENT")
    need(max_hair_displacement > 0.004, "HAIR_DOES_NOT_FOLLOW_NECK")
    need(max_hair_displacement < 0.35, "HAIR_EXPLOSION_LIMIT",
         "A small neck gesture produced unacceptable hair displacement.")
    return {
        "sampled_frames":len(sample_times),
        "rest_hair_error_max":max_rest_error,
        "hoof_bone_drift_max":max_hoof_node_drift,
        "hoof_vertex_drift_max":max_hoof_vertex_drift,
        "max_hair_vertex_displacement":max_hair_displacement,
        "hoof_surface_samples":len(hoof_samples),
        "leg_joint_rotation_channels":0,
        "root_translation_channels":0,
        "visual_acceptance":"PENDING",
    }, frames


PREVIEW_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1"><title>Repl hair bind v0.1.0</title>
<style>body{font:16px system-ui;background:#17191e;color:#f1eee9;margin:0;padding:14px}
main{max-width:1050px;margin:auto} canvas{background:#f0ede6;display:block;
max-width:100%;width:100%;border-radius:10px}button,select,input{font:inherit}
button,select{padding:8px;margin:4px}p{line-height:1.5;color:#c8c4ba}
label{margin:8px}</style></head><body><main><h2>Repl: hair-only bind diagnostic</h2>
<p>This is a real skeletal-motion diagnostic from the generated mesh, not a
textured beauty render or proof of human visual acceptance. Four hooves
are held still; only neck/head nodes rotate. Crimson marks are hair mesh vertices.</p>
<div><button id="toggle">Pause</button><label>Camera
<select id="camera"><option value="side">Side</option><option value="three">3/4</option>
<option value="front">Front</option></select></label>
<label>Frame <input id="frame" type="range" min="0" max="24" value="0"></label>
<span id="status"></span></div><canvas id="view" width="1000" height="630"></canvas>
<p>Use the accompanying GLB in a glTF-capable 3D viewer for the full textured result.
No cloth, wind shader or leg animation is present in this test.</p></main>
<script>
const data=__DATA__;
const canvas=document.getElementById("view"),ctx=canvas.getContext("2d");
let frame=0,playing=true;
function xy(p,cam) {
 let x=cam==="front"?p[0]:cam==="side"?p[2]:p[2]*.65+p[0]*.75;
 return [500+x*310,565-p[1]*300];
}
function draw(){
 let d=data.frames[frame],cam=document.getElementById("camera").value;
 ctx.clearRect(0,0,1000,630);
 ctx.strokeStyle="#b7b2a7";ctx.lineWidth=1;ctx.beginPath();
 ctx.moveTo(40,565);ctx.lineTo(960,565);ctx.stroke();
 ctx.fillStyle="#32343a";
 for(let p of d.body){let q=xy(p,cam);ctx.fillRect(q[0]-1.2,q[1]-1.2,2.4,2.4);}
 ctx.fillStyle="#a93e53";
 for(let p of d.hair){let q=xy(p,cam);ctx.fillRect(q[0]-1.35,q[1]-1.35,2.7,2.7);}
 document.getElementById("frame").value=frame;
 document.getElementById("status").textContent="t="+d.time.toFixed(3)+" sec, no hoof keys";
}
document.getElementById("toggle").onclick=function(){
 playing=!playing;this.textContent=playing?"Pause":"Play";};
document.getElementById("frame").oninput=e=>{frame=Number(e.target.value);draw();};
document.getElementById("camera").onchange=draw;
setInterval(()=>{if(playing){frame=(frame+1)%data.frames.length;draw();}},125);
draw();
</script></body></html>"""


def inspect_repo_revision():
    try:
        proc = subprocess.run(["git","rev-parse","HEAD"],text=True,
                              stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                              timeout=4,check=False,
                              cwd=Path(__file__).resolve().parent)
        if proc.returncode == 0:
            return proc.stdout.strip()
    except (OSError,subprocess.TimeoutExpired):
        pass
    return None


def make_candidate(path:Path):
    source,doc,binary=glb_load(path)
    before_node=doc["nodes"][45].copy()
    body_json=json.dumps(doc["meshes"][0],sort_keys=True)
    original_bin_hash=sha256(binary)
    rows_j,rows_w,stats,coverage,hair_pos,body_pos=bind_hair(doc,binary)
    outbin=bytearray(binary)
    hair=doc["meshes"][1]["primitives"][0]
    hair["attributes"]["JOINTS_0"]=emit_accessor(
        doc,outbin,rows_j,5123,"VEC4",34962)
    hair["attributes"]["WEIGHTS_0"]=emit_accessor(
        doc,outbin,rows_w,5126,"VEC4",34962)
    doc["nodes"][45]["skin"]=0
    name_to_node={node.get("name"):i for i,node in enumerate(doc["nodes"])}
    keyframes=make_animation(doc,outbin,name_to_node)
    need(json.dumps(doc["meshes"][0],sort_keys=True)==body_json,
         "BODY_MESH_JSON_CHANGED")
    need(sha256(bytes(outbin[:len(binary)]))==original_bin_hash,
         "SOURCE_BUFFER_PREFIX_CHANGED")
    need(all(k in doc["nodes"][45] and doc["nodes"][45][k]==v
             for k,v in before_node.items()),
         "HAIR_NODE_EXISTING_PROPERTIES_CHANGED")
    validation,frames=validate_motion(
        doc,bytes(outbin),rows_j,rows_w,hair_pos,body_pos,keyframes)
    doc.setdefault("asset",{}).setdefault("extras",{})["replHairCampaign"]={
        "version":VERSION,"sourceSha256":SOURCE_SHA256,
        "method":"root-seeded axial skin transfer, no new bones",
        "manualVerdict":"PENDING",
        "hooves":"static in this review clip"}
    output=glb_encode(doc,bytes(outbin))
    report={"campaign":CAMPAIGN,"version":VERSION,
            "status":"NUMERICAL_VALIDATION_PASS__HUMAN_VISUAL_PENDING",
            "timestamp_utc":now_utc(),"original_source_sha256":sha256(source),
            "git_revision":inspect_repo_revision(),
            "body_vertices":len(body_pos),"hair_vertices":len(hair_pos),
            "skin_joints":len(doc["skins"][0]["joints"]),
            "mane_tail":stats,"bone_contribution_sums":coverage,
            "validation":validation,
            "skin_bind_location":"original hair node 45",
            "modifications":["hair JOINTS_0/WEIGHTS_0",
                             "hair node skin reference",
                             "neck/head-only review animation"],
            "excluded":["source file overwrite","body edits","hoof motion",
                        "new bones","cloth","shader","wind physics"],
            "limitations":[
               "This creates a derived GLB, not an edit to Repl.blend.",
               "Offline preview is an untextured point-sample diagnostic.",
               "Actual 3D viewer, styling and human visual acceptance remain pending.",
               "No phone/gallery success is implied by a scan or viewer request."
            ]}
    html=PREVIEW_HTML.replace("__DATA__",json.dumps(
        {"frames":frames},separators=(",",":")))
    return output,report,html


def source_candidates(explicit):
    if explicit:
        return [Path(explicit).expanduser()]
    home=Path.home()
    locations=[
        home/"storage"/"downloads"/"Repl.glb",
        home/"storage"/"shared"/"Download"/"Repl.glb",
        home/"Downloads"/"Repl.glb",
        home/"GodotProjects"/"pose-lab-v2"/"Repl.glb",
        Path.cwd()/"Repl.glb",
    ]
    return locations


def resolve_source(explicit):
    paths=source_candidates(explicit)
    found=[p for p in paths if p.is_file()]
    if not found:
        raise Blocked("EXACT_REPL_GLB_NOT_FOUND: searched " +
                      " | ".join(str(p) for p in paths))
    valid=[p for p in found if file_sha(p)==SOURCE_SHA256]
    need(bool(valid),"ONLY_WRONG_REPL_GLB_FOUND",
         "Found file(s) with this name but NONE have the locked source SHA.")
    return valid[0].resolve()


def output_root(arg):
    if arg:
        return Path(arg).expanduser().resolve()
    home=Path.home()
    shared=home/"storage"/"downloads"
    if shared.is_dir():
        return shared/"Repl_HairBind_v0.1.0"
    return home/"Downloads"/"Repl_HairBind_v0.1.0"


def verify_delivery(root):
    receipt_file=root/"RECEIPT_v0.1.0.json"
    need(receipt_file.is_file(),"NO_VERIFIED_CAMPAIGN_RECEIPT")
    receipt=json.loads(receipt_file.read_text("utf8"))
    need(receipt.get("version")==VERSION
         and receipt.get("source_sha256")==SOURCE_SHA256,
         "RECEIPT_IDENTITY_MISMATCH")
    for name,digest in receipt.get("output_sha256",{}).items():
        p=root/name
        need(p.is_file() and file_sha(p)==digest,
             "DELIVERY_HASH_MISMATCH",str(p))
    return receipt


def publish(root,source):
    need(sys.version_info>=SUPPORTED_PYTHON,"PYTHON_VERSION_TOO_OLD")
    if root.exists():
        receipt=verify_delivery(root)
        print("CANDIDATE_ALREADY_VERIFIED=YES")
        print("DERIVED_GLB="+str(root/"Repl_HairBind_v0.1.0.glb"))
        print("OFFLINE_PREVIEW="+str(root/"Repl_HairBind_v0.1.0_preview.html"))
        print("SOURCE_SHA256="+receipt["source_sha256"])
        print("HUMAN_VERDICT=PENDING")
        return
    need(root.parent.exists(),"OUTPUT_PARENT_UNAVAILABLE",str(root.parent))
    work=Path(tempfile.mkdtemp(prefix=".repl-hair-v0.1.0-",
                               dir=str(root.parent)))
    try:
        glb,report,html=make_candidate(source)
        names={
          "Repl_HairBind_v0.1.0.glb":glb,
          "Repl_HairBind_v0.1.0_report.json":
              json.dumps(report,indent=2,sort_keys=True).encode("utf8"),
          "Repl_HairBind_v0.1.0_preview.html":html.encode("utf8"),
        }
        for name,content in names.items():
            (work/name).write_bytes(content)
        manifest={name:file_sha(work/name) for name in names}
        receipt={
            "campaign":CAMPAIGN,"version":VERSION,
            "status":"CANDIDATE_GENERATED_HUMAN_REVIEW_PENDING",
            "source_path":str(source),
            "source_sha256":SOURCE_SHA256,
            "source_size_bytes":source.stat().st_size,
            "output_sha256":manifest,
            "git_revision":inspect_repo_revision(),
            "timestamp_utc":now_utc(),
            "physical_phone_view":"NOT_VERIFIED",
            "viewer_open":"NOT_ATTEMPTED",
            "media_scan":"NOT_ATTEMPTED",
            "human_verdict":"PENDING"
        }
        (work/"RECEIPT_v0.1.0.json").write_text(
            json.dumps(receipt,indent=2,sort_keys=True),encoding="utf8")
        # Atomic same-filesystem directory publication, never overwrite.
        need(not root.exists(),"OUTPUT_RACE_OR_PREEXISTING")
        work.rename(root)
    finally:
        if work.exists():
            shutil.rmtree(work)
    verify_delivery(root)
    print("CANDIDATE_GENERATED=YES")
    print("SOURCE_SHA256="+SOURCE_SHA256)
    print("DERIVED_GLB="+str(root/"Repl_HairBind_v0.1.0.glb"))
    print("OFFLINE_PREVIEW="+str(root/"Repl_HairBind_v0.1.0_preview.html"))
    print("GLB_SHA256="+manifest["Repl_HairBind_v0.1.0.glb"])
    print("HUMAN_VERDICT=PENDING")
    # Never equate intent to open with a successful viewer display.
    preview=root/"Repl_HairBind_v0.1.0_preview.html"
    if shutil.which("mediarefresh"):
        result=subprocess.run(["mediarefresh",str(preview)],timeout=25,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,check=False)
        print("MEDIA_SCAN="+("REQUESTED" if result.returncode==0 else "FAILED"))
    elif shutil.which("termux-media-scan"):
        result=subprocess.run(["termux-media-scan",str(preview)],timeout=15,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,check=False)
        print("MEDIA_SCAN="+("REQUESTED" if result.returncode==0 else "FAILED"))
    else:
        print("MEDIA_SCAN=UNAVAILABLE")
    if shutil.which("termux-open"):
        try:
            subprocess.run(["termux-open",str(preview)],timeout=12,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,check=False)
            print("VIEWER_OPEN=REQUESTED_NOT_CONFIRMED")
        except (OSError,subprocess.TimeoutExpired):
            print("VIEWER_OPEN=FAILED")
    else:
        print("VIEWER_OPEN=NOT_AVAILABLE")


def main(argv=None):
    parser=argparse.ArgumentParser(
        description="Repl hair-only auto-skin, no hoof animation. Original preserved.")
    parser.add_argument("operation",nargs="?",default="run",
                        choices=["run","doctor","status","resume","rollback"])
    parser.add_argument("--source",help="Exact, hash-locked Repl.glb file.")
    parser.add_argument("--output",help="Versioned output directory; never overwritten.")
    args=parser.parse_args(argv)
    print("CAMPAIGN="+CAMPAIGN)
    print("CAMPAIGN_VERSION="+VERSION)
    print("CAMPAIGN_SCRIPT="+str(Path(__file__).resolve()))
    print("CAMPAIGN_SCRIPT_SHA256="+file_sha(Path(__file__).resolve()))
    print("EXPECTED_SOURCE_SHA256="+SOURCE_SHA256)
    root=output_root(args.output)
    print("OUTPUT_DIRECTORY="+str(root))
    if args.operation in ("status","rollback"):
        if args.operation=="rollback":
            print("ROLLBACK=NOT_REQUIRED_SOURCE_NEVER_MUTATED")
        if root.exists():
            receipt=verify_delivery(root)
            print("DELIVERY_STATUS="+receipt["status"])
            print("RECEIPT="+str(root/"RECEIPT_v0.1.0.json"))
        else:
            print("DELIVERY_STATUS=NOT_STARTED")
        return 0
    source=resolve_source(args.source)
    print("SOURCE_FILE="+str(source))
    print("ACTUAL_SOURCE_SHA256="+file_sha(source))
    _original, doc, _binary=glb_load(source)
    print("SOURCE_PREFLIGHT=PASS")
    print("SOURCE_SKIN_JOINTS="+str(len(doc["skins"][0]["joints"])))
    if args.operation=="doctor":
        print("DOCTOR=PASS_NO_MUTATION")
        return 0
    publish(root,source)
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except Blocked as error:
        print("CAMPAIGN_STATUS=BLOCKED")
        print("FAILURE="+str(error))
        print("SOURCE_MODIFIED=NO")
        print("HUMAN_VERDICT=PENDING")
        sys.exit(2)
    except Exception as error:
        print("CAMPAIGN_STATUS=FAILED_UNEXPECTEDLY")
        print("FAILURE="+type(error).__name__+": "+str(error))
        traceback.print_exc()
        print("SOURCE_MODIFIED=NO")
        sys.exit(3)
