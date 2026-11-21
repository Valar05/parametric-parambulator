/* v0.2.6: compare homologous joints in the exact SAME MODEL SPACE.
 * Scene roots are separated for viewing only. Rendering offsets are not
 * anatomical motion and must never contribute to gait safety constraints. */
export function comparisonPoint(root,bone,vectorFactory){
 if(!root||typeof root.worldToLocal!=='function'||!bone||typeof bone.getWorldPosition!=='function'||typeof vectorFactory!=='function')throw Error('COMPARISON_RIG_CONTRACT');
 return root.worldToLocal(bone.getWorldPosition(vectorFactory()));
}
export function collectComparisonPositions(rig,root,names,vectorFactory){
 if(!Array.isArray(names)||!names.length)throw Error('COMPARISON_JOINT_LIST_EMPTY');
 const out={};for(const name of names){if(!rig[name])throw Error('COMPARISON_MISSING_BONE '+name);out[name]=comparisonPoint(root,rig[name],vectorFactory)}
 return out;
}
