#!/usr/bin/env python3
"""Repl hair-only five-control campaign v0.2.0.

One commissioned objective: add 3 mane + 2 tail joints to the *derived*
Repl.glb, redistribute automatically generated axial hair skin weights onto
those child joints, and evaluate a gentle neck-only animation with stationary
hooves. All five added joints remain at REST during this experiment.

No new leg animation, body mesh edit, source overwrite, cloth, wind shader,
external dependencies, Git mutations, or opportunistic repair.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import traceback

CAMPAIGN = "REPL_HAIR_FIVE_CONTROLS"
VERSION = "0.2.0"
SOURCE_SHA256 = "d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f"
PREDECESSOR = "repl_hair_bind_v0_1_0.py"
PREDECESSOR_BLOB_SHA = "33ca93660f3d5858d4496027902b9b7a7e44d800"
# Target articulation follows *existing* axial bones. No body skin weights
# can refer to appended indices, so new controls cannot control the body.
CONTROLS = (
    ("REPL_MANE_REAR", "Bone_003", None, (-0.06, 1.20, -0.04)),
    ("REPL_MANE_MIDDLE", "Bone_010", None, (0.0, 1.40, 0.31)),
    ("REPL_MANE_FRONT", "Bone_008", None, (0.0, 1.59, 0.57)),
    ("REPL_TAIL_BASE", "Bone_004", None, (0.0, 1.05, -0.93)),
    ("REPL_TAIL_TIP", "REPL_TAIL_BASE", None, (0.0, 0.80, -1.27)),
)
EXPECTED_NEW_JOINT_COUNT = 48
EXPECTED_NEW_NODE_COUNT = 51
OUTPUT_NAME = "Repl_HairFiveControls_v0.2.0.glb"
REPORT_NAME = "Repl_HairFiveControls_v0.2.0_report.json"
PREVIEW_NAME = "Repl_HairFiveControls_v0.2.0_preview.html"
RECEIPT_NAME = "RECEIPT_v0.2.0.json"
OUTPUT_DIR = "Repl_HairFiveControls_v0.2.0"


class Blocked(RuntimeError):
    pass


def require(ok, reason):
    if not ok:
        raise Blocked(reason)


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(source: bytes):
    return hashlib.sha1(
        b"blob " + str(len(source)).encode() + b"\0" + source
    ).hexdigest()


def load_predecessor():
    src = Path(__file__).with_name(PREDECESSOR)
    require(src.is_file(), "REQUIRED_GIT_OWNED_V0_1_0_ENGINE_MISSING")
    require(git_blob_sha(src.read_bytes()) == PREDECESSOR_BLOB_SHA,
            "PREDECESSOR_GIT_BLOB_SHA_MISMATCH")
    spec = importlib.util.spec_from_file_location("repl_hair_v010", src)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.VERSION == "0.1.0" and module.SOURCE_SHA256 == SOURCE_SHA256,
            "PREDECESSOR_IDENTITY_MISMATCH")
    return module


def read_glb_bytes(data: bytes):
    require(data[:4] == b"glTF", "DERIVED_GLB_BAD_MAGIC")
    _magic, version, length = struct.unpack_from("<4sII", data)
    require(version == 2 and length == len(data), "DERIVED_GLB_BAD_HEADER")
    n1, kind1 = struct.unpack_from("<I4s", data, 12)
    off = 20 + n1
    n2, kind2 = struct.unpack_from("<I4s", data, off)
    require(kind1 == b"JSON" and kind2 == b"BIN\x00", "DERIVED_GLB_BAD_CHUNKS")
    require(off + 8 + n2 == len(data), "DERIVED_GLB_WRONG_LENGTH")
    return json.loads(data[20:20+n1]), data[off+8:]


def matrix_from_glb_mat4(packed):
    """Column-major glTF accessor -> row-major 4x4 used by the base engine."""
    return [float(packed[4*c+r]) for r in range(4) for c in range(4)]


def matrix_to_glb_mat4(row_major):
    return tuple(float(row_major[4*r+c]) for c in range(4) for r in range(4))


def translation_matrix(xyz):
    x,y,z = xyz
    return [1,0,0,x, 0,1,0,y, 0,0,1,z, 0,0,0,1]


def local_point_from_parent_inverse(parent_ibm, world_pivot, base):
    return base.apply_matrix(parent_ibm, world_pivot)


def new_joint_definitions(doc, bin_data, base):
    """New bones inherit body pose but can independently rotate in the future.

    IBM_new = inverse(T_local) * IBM_parent, so in the initial rest pose,
    new skin transforms exactly cancel and never move the original mesh.
    """
    old_joints = list(doc["skins"][0]["joints"])
    require(len(old_joints) == 43 and len(doc["nodes"]) == 46,
            "MUST_START_WITH_43_BONES_AND_46_NODES")
    old_ibms_raw = base.accessor(doc, bin_data,
                                doc["skins"][0]["inverseBindMatrices"])
    require(len(old_ibms_raw) == 43, "OLD_IBMS_WRONG_LENGTH")
    all_ibms = [matrix_from_glb_mat4(row) for row in old_ibms_raw]
    old_name_to_joint = {doc["nodes"][node]["name"]: i
                         for i,node in enumerate(old_joints)}
    old_name_to_node = {doc["nodes"][node]["name"]: node
                        for node in old_joints}
    new_indices = {}
    manifest = []
    for control_name, parent_name, _ignored, pivot in CONTROLS:
        if parent_name in old_name_to_joint:
            parent_joint = old_name_to_joint[parent_name]
            parent_node = old_name_to_node[parent_name]
        else:
            require(parent_name in new_indices, "MISSING_NEW_PARENT")
            parent_joint = new_indices[parent_name]
            parent_node = doc["skins"][0]["joints"][parent_joint]
        parent_ibm = all_ibms[parent_joint]
        local_offset = local_point_from_parent_inverse(parent_ibm,pivot,base)
        inverse_offset = translation_matrix(tuple(-v for v in local_offset))
        new_ibm = base.matrix_mult(inverse_offset,parent_ibm)
        new_node_id = len(doc["nodes"])
        doc["nodes"].append({
            "name":control_name,
            "translation":[float(x) for x in local_offset],
            "rotation":[0,0,0,1],
            "scale":[1,1,1],
            "extras":{"role":"hair_only_control","version":VERSION,
                      "motion":"REST_IN_THIS_CAMPAIGN",
                      "original_parent":parent_name}
        })
        doc["nodes"][parent_node].setdefault("children",[]).append(new_node_id)
        new_joint_index = len(doc["skins"][0]["joints"])
        doc["skins"][0]["joints"].append(new_node_id)
        all_ibms.append(new_ibm)
        new_indices[control_name] = new_joint_index
        manifest.append({
            "name":control_name,"parent_name":parent_name,
            "node_id":new_node_id,"skin_index":new_joint_index,
            "requested_world_pivot":list(pivot),
            "local_translation":list(local_offset)
        })
    require(len(doc["nodes"]) == EXPECTED_NEW_NODE_COUNT,
            "APPENDED_NODE_COUNT_WRONG")
    require(len(doc["skins"][0]["joints"]) == EXPECTED_NEW_JOINT_COUNT,
            "APPENDED_JOINT_COUNT_WRONG")
    return new_indices, all_ibms, manifest, old_name_to_joint


def normalize4(d):
    pairs = [(k,v) for k,v in sorted(d.items()) if v>1e-8]
    total = sum(v for k,v in pairs)
    require(total > 1e-9, "ZERO_REPLACEMENT_WEIGHTS")
    pairs = sorted(((k,v/total) for k,v in pairs),key=lambda x:-x[1])[:4]
    again = sum(v for k,v in pairs)
    jj=[int(k) for k,v in pairs]
    ww=[float(v/again) for k,v in pairs]
    while len(jj)<4:
        jj.append(0);ww.append(0.0)
    return tuple(jj),tuple(ww)


def remap_onto_new_bones(doc,bin_data,base,new_indices,old_names):
    """Reuse v0.1.0's root-propagated automatic weights.

    Its maneuvering-free parent influence estimates are mapped by region to
    exactly five hair-only control bones. No independent hair keys yet.
    """
    hair=doc["meshes"][1]["primitives"][0]
    ids=base.accessor(doc,bin_data,hair["attributes"]["JOINTS_0"])
    old_weights=base.accessor(doc,bin_data,hair["attributes"]["WEIGHTS_0"])
    positions=base.accessor(doc,bin_data,hair["attributes"]["POSITION"])
    require(len(ids)==len(old_weights)==len(positions)==1819,
            "HAIR_VERTEX_COUNT_CHANGED")
    mane_map={
       "Bone_001":"REPL_MANE_REAR",
       "Bone_002":"REPL_MANE_REAR",
       "Bone_003":"REPL_MANE_REAR",
       "Bone_010":"REPL_MANE_MIDDLE",
       "Bone_009":"REPL_MANE_MIDDLE",
       "Bone_008":"REPL_MANE_FRONT",
       "Bone_007":"REPL_MANE_FRONT"
    }
    old_joint_names={
       i:doc["nodes"][node]["name"]
       for i,node in enumerate(doc["skins"][0]["joints"][:43])
    }
    out_j,out_w=[],[]
    report={"mane_vertices":0,"tail_vertices":0,
            "new_control_contributions":{n:0.0 for n in new_indices}}
    for i,(p,js,ws) in enumerate(zip(positions,ids,old_weights)):
        if p[2] >= -0.65:
            report["mane_vertices"]+=1
            contributions={}
            for j,w in zip(js,ws):
                if w<=0:continue
                name=old_joint_names[j]
                require(name in mane_map,"NON_AXIAL_MANE_SOURCE_BONE")
                target=new_indices[mane_map[name]]
                contributions[target]=contributions.get(target,0)+w
        else:
            report["tail_vertices"]+=1
            # Section distance from rump. This controls OPTIONAL later sway
            # without altering the appearance or relaxing root attachment.
            u=min(1.,max(0.,(-0.86-p[2])/(1.594-0.86)))
            smooth=u*u*(3-2*u)
            tip=0.80*smooth
            contributions={
                new_indices["REPL_TAIL_BASE"]:1-tip,
                new_indices["REPL_TAIL_TIP"]:tip
            }
        joints,weights=normalize4(contributions)
        require(all(0<=j<48 for j in joints),"INVALID_NEW_JOINT")
        require(abs(sum(weights)-1)<1e-5,"INVALID_HAIR_WEIGHT_SUM")
        out_j.append(joints);out_w.append(weights)
        for control,idx in new_indices.items():
            report["new_control_contributions"][control]+=sum(
                value for j,value in zip(joints,weights) if j==idx)
    require(report["mane_vertices"]>600 and report["tail_vertices"]>900,
            "HAIR_REGIONS_INCONSISTENT_WITH_SOURCE")
    require(all(v>0 for v in report["new_control_contributions"].values()),
            "HAIR_CONTROL_BONE_HAS_ZERO_WEIGHT")
    # Same spatial position (duplicated UV seam vertices) must have
    # exactly the same weights, so there can be no seam separation.
    seen={}
    for i,p in enumerate(positions):
        key=tuple(round(float(x),5) for x in p)
        sig=(out_j[i],tuple(round(w,5) for w in out_w[i]))
        require(key not in seen or seen[key]==sig,"WEIGHT_SEAM_MISMATCH")
        seen[key]=sig
    return out_j,out_w,report,positions


def review_keyframes(doc,bin_data,base):
    """Read v0.1.0's neck-only review clip without adding mane keys."""
    require(len(doc.get("animations",[]))==1,"REVIEW_CLIP_COUNT_CHANGED")
    anim=doc["animations"][0]
    require(len(anim["channels"])==4,"UNEXPECTED_REVIEW_CHANNEL_COUNT")
    allowed={"Bone_010","Bone_009","Bone_008","Bone_007"}
    frames={}
    for channel in anim["channels"]:
        require(channel["target"]["path"]=="rotation",
                "NON_ROTATION_CHANNEL_FORBIDDEN")
        nodeid=channel["target"]["node"]
        name=doc["nodes"][nodeid].get("name")
        require(name in allowed,"LEG_OR_HAIR_ANIMATION_CHANNEL_FORBIDDEN")
        sampler=anim["samplers"][channel["sampler"]]
        require(sampler.get("interpolation")=="LINEAR",
                "NONLINEAR_REVIEW_INTERPOLATION_UNEXPECTED")
        frames[nodeid]=base.accessor(doc,bin_data,sampler["output"])
    require(set(doc["nodes"][k]["name"] for k in frames)==allowed,
            "NECK_REVIEW_BONE_SET_CHANGED")
    return frames


def verify_derived(doc, binary, base, joints, weights, hairpos, keyframes):
    """Numerical validation of exact derived skin, not just old hair weights."""
    original_expected=base.EXPECTED_JOINTS
    try:
        base.EXPECTED_JOINTS=EXPECTED_NEW_JOINT_COUNT
        body=doc["meshes"][0]["primitives"][0]
        body_positions=base.accessor(doc,binary,body["attributes"]["POSITION"])
        verdict,frames=base.validate_motion(
            doc,binary,joints,weights,hairpos,body_positions,keyframes)
    finally:
        base.EXPECTED_JOINTS=original_expected
    require(verdict["max_hair_vertex_displacement"]>0.004,
            "REVIEW_HAIR_NOT_MOVING_WITH_NECK")
    require(verdict["hoof_bone_drift_max"]<1e-6,
            "HOOF_BONE_ROTATION_OR_TRANSLATION")
    require(verdict["hoof_vertex_drift_max"]<3e-4,
            "HOOF_SKIN_MOVEMENT")
    require(verdict["rest_hair_error_max"]<3e-4,
            "REST_MANE_TAIL_SILHOUETTE_CHANGED")
    return verdict,frames


def create_artifacts(source_path, base):
    old_glb_bytes, old_report, unused_preview=base.make_candidate(source_path)
    doc, original_bin=read_glb_bytes(old_glb_bytes)
    require(len(doc["skins"][0]["joints"])==43,
            "PREDECESSOR_SKIN_COUNT_UNEXPECTED")
    original_body=json.dumps(doc["meshes"][0],sort_keys=True)
    original_mesh_0_node=json.dumps(doc["nodes"][43],sort_keys=True)
    original_body_buffer_prefix=sha(original_bin)
    new_indices, matrices, manifest, old_map = new_joint_definitions(
        doc,original_bin,base)
    j,w,coverage,positions=remap_onto_new_bones(
        doc,original_bin,base,new_indices,old_map)
    extra=bytearray(original_bin)
    # Append updated 48-joint inverse bind matrices. Existing data is immutable.
    matrices_access=base.emit_accessor(
        doc,extra,[matrix_to_glb_mat4(row) for row in matrices],5126,"MAT4")
    doc["skins"][0]["inverseBindMatrices"]=matrices_access
    hair=doc["meshes"][1]["primitives"][0]
    hair["attributes"]["JOINTS_0"]=base.emit_accessor(
        doc,extra,j,5123,"VEC4",34962)
    hair["attributes"]["WEIGHTS_0"]=base.emit_accessor(
        doc,extra,w,5126,"VEC4",34962)
    require(json.dumps(doc["meshes"][0],sort_keys=True)==original_body,
            "BODY_MESH_DEFINITION_MODIFIED")
    require(json.dumps(doc["nodes"][43],sort_keys=True)==original_mesh_0_node,
            "BODY_MESH_NODE_MODIFIED")
    require(sha(bytes(extra[:len(original_bin)]))==original_body_buffer_prefix,
            "EXISTING_GLB_BINARY_PREFIX_MODIFIED")
    require(doc["nodes"][45].get("skin")==0,
            "DERIVED_HAIR_SKIN_BINDING_MISSING")
    keys=review_keyframes(doc,bytes(extra),base)
    verdict,frames=verify_derived(
        doc,bytes(extra),base,j,w,positions,keys)
    doc["asset"]["extras"]["replHairCampaign"]={
        "version":VERSION,"sourceSha256":SOURCE_SHA256,
        "predecessor":"0.1.0",
        "five_added_hair_controls":list(new_indices),
        "control_motion":"NONE / REST",
        "body_modification":"NONE",
        "manualVerdict":"PENDING"}
    output=base.glb_encode(doc,bytes(extra))
    report={"campaign":CAMPAIGN,"version":VERSION,
            "source_sha256":SOURCE_SHA256,
            "predecessor_version":"0.1.0",
            "control_bones":manifest,
            "control_weights":coverage,
            "validated_motion":verdict,
            "predecessor_validation":old_report.get("validation"),
            "original_body_mesh_unchanged":True,
            "original_body_vertex_data_unchanged":True,
            "original_43_joint_indices_preserved":True,
            "hair_control_channels":0,
            "hoof_and_leg_channels":0,
            "human_visual_acceptance":"PENDING",
            "limitations":[
              "This is a derived GLB; the original Repl.blend is untouched.",
              "Five additional rest-only bones are available for later use.",
              "Preview is untextured diagnostic; actual GLB review is required.",
              "No independent mane sway, shader, cloth or wind simulation.",
              "Numerical checks cannot establish physical phone display."
             ]}
    preview=base.PREVIEW_HTML.replace("__DATA__",
        json.dumps({"frames":frames},separators=(",",":")))
    preview=preview.replace("Repl hair bind v0.1.0",
                            "Repl five hair controls v0.2.0")
    preview=preview.replace("Four hooves", "Four hooves")
    return output,json.dumps(report,indent=2,sort_keys=True),preview


def delivery_dir(explicit):
    if explicit:return Path(explicit).expanduser().resolve()
    h=Path.home()
    shared=h/"storage"/"downloads"
    if shared.is_dir():return shared/OUTPUT_DIR
    return (h/"Downloads"/OUTPUT_DIR)


def exact_existing_receipt(folder):
    path=folder/RECEIPT_NAME
    require(path.is_file(),"PARTIAL_OR_COLLIDING_OUTPUT_FOLDER")
    r=json.loads(path.read_text("utf8"))
    require(r["version"]==VERSION and
            r["source_sha256"]==SOURCE_SHA256,
            "EXISTING_RECEIPT_WRONG_IDENTITY")
    for name,expected in r["outputs"].items():
        path=folder/name
        require(path.is_file() and file_sha(path)==expected,
                "EXISTING_OUTPUT_HASH_MISMATCH")
    return r


def do_run(args,base):
    source=base.resolve_source(args.source)
    print("SOURCE="+str(source))
    print("SOURCE_SHA256="+file_sha(source))
    folder=delivery_dir(args.output)
    print("OUTPUT_DIR="+str(folder))
    if folder.exists():
        r=exact_existing_receipt(folder)
        print("IDEMPOTENT_EXISTING_RESULT=VERIFIED")
        print("GLB_SHA256="+r["outputs"][OUTPUT_NAME])
        print("HUMAN_VERDICT=PENDING")
        return
    require(folder.parent.is_dir(),"OUTPUT_PARENT_UNAVAILABLE")
    staging=Path(tempfile.mkdtemp(prefix=".repl_hair_020_",
                                  dir=str(folder.parent)))
    try:
        glb,report,preview=create_artifacts(source,base)
        data={OUTPUT_NAME:glb,REPORT_NAME:report.encode("utf8"),
              PREVIEW_NAME:preview.encode("utf8")}
        for name,content in data.items():
            (staging/name).write_bytes(content)
        r={"campaign":CAMPAIGN,"version":VERSION,
           "source_path":str(source),"source_sha256":SOURCE_SHA256,
           "utc":dt.datetime.now(dt.timezone.utc).isoformat(),
           "outputs":{n:file_sha(staging/n) for n in data},
           "github_head":args.revision or "VERIFY_GIT_CHECKOUT_IN_LAUNCHER",
           "status":"NUMERIC_VALIDATION_PASS__HUMAN_VISUAL_PENDING",
           "source_mutated":False,
           "phone_files_ui_visibility":"UNVERIFIED",
           "human_verdict":"PENDING"}
        (staging/RECEIPT_NAME).write_text(
            json.dumps(r,indent=2,sort_keys=True),"utf8")
        require(not folder.exists(),"OUTPUT_PUBLISH_COLLISION")
        staging.rename(folder)
    finally:
        if staging.exists():shutil.rmtree(staging)
    exact_existing_receipt(folder)
    print("DERIVED_GLB="+str(folder/OUTPUT_NAME))
    print("OFFLINE_PREVIEW="+str(folder/PREVIEW_NAME))
    print("GLB_SHA256="+r["outputs"][OUTPUT_NAME])
    print("HUMAN_VERDICT=PENDING")
    # Publishing is attempted for the exact actual file, never a directory.
    if shutil.which("mediarefresh"):
        try:
            p=subprocess.run(["mediarefresh",str(folder/PREVIEW_NAME)],
                            timeout=12,check=False,capture_output=True)
            print("MEDIA_SCAN="+("REQUESTED" if p.returncode==0 else "FAILED"))
        except (OSError,subprocess.TimeoutExpired):
            print("MEDIA_SCAN=FAILED")
    elif shutil.which("termux-media-scan"):
        try:
            p=subprocess.run(["termux-media-scan",str(folder/PREVIEW_NAME)],
                            timeout=12,check=False,capture_output=True)
            print("MEDIA_SCAN="+("REQUESTED" if p.returncode==0 else "FAILED"))
        except (OSError,subprocess.TimeoutExpired):
            print("MEDIA_SCAN=FAILED")
    else:
        print("MEDIA_SCAN=UNAVAILABLE")
    if shutil.which("termux-open"):
        try:
            p=subprocess.run(["termux-open",str(folder/PREVIEW_NAME)],
                            timeout=10,check=False,capture_output=True)
            print("VIEWER_OPEN="+("REQUESTED_UNCONFIRMED"
                                 if p.returncode==0 else "FAILED"))
        except (OSError,subprocess.TimeoutExpired):
            print("VIEWER_OPEN=FAILED")
    else:print("VIEWER_OPEN=UNAVAILABLE")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",nargs="?",default="run",
                    choices=("run","resume","doctor","status","rollback"))
    ap.add_argument("--source",help="Exact owner Repl.glb path")
    ap.add_argument("--output",help="Immutable versioned output folder")
    ap.add_argument("--revision",help="Pinned Git revision from launcher")
    args=ap.parse_args()
    print("CAMPAIGN="+CAMPAIGN)
    print("VERSION="+VERSION)
    print("SCRIPT="+str(Path(__file__).resolve()))
    print("SCRIPT_SHA256="+file_sha(Path(__file__).resolve()))
    print("SOURCE_EXPECTED_SHA256="+SOURCE_SHA256)
    base=load_predecessor()
    if args.mode in ("status","rollback"):
        folder=delivery_dir(args.output)
        if args.mode=="rollback":
            print("SOURCE_ROLLBACK=NOT_NEEDED_ORIGINAL_NEVER_MODIFIED")
        if folder.exists():
            r=exact_existing_receipt(folder)
            print("STATUS="+r["status"])
            print("RECEIPT="+str(folder/RECEIPT_NAME))
        else:print("STATUS=NOT_STARTED")
        return
    source=base.resolve_source(args.source)
    print("EXACT_SOURCE="+str(source))
    base.glb_load(source)
    print("PREFLIGHT=PASS")
    if args.mode=="doctor":
        print("DOCTOR=PASS_SOURCE_UNCHANGED")
    else:do_run(args,base)


if __name__=="__main__":
    try:main()
    except (Blocked,ValueError,KeyError,IndexError,TypeError) as exc:
        print("CAMPAIGN_STATUS=BLOCKED")
        print("CAUSE="+type(exc).__name__+": "+str(exc))
        print("SOURCE_MUTATED=NO")
        print("HUMAN_VERDICT=PENDING")
        sys.exit(2)
    except Exception as exc:
        traceback.print_exc()
        print("CAMPAIGN_STATUS=ERROR")
        print("CAUSE="+type(exc).__name__+": "+str(exc))
        print("SOURCE_MUTATED=NO")
        sys.exit(3)
