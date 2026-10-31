from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
import os
import re
import io
import zipfile

app = Flask(__name__, template_folder='.')
app.secret_key = "astral_secret"

@app.route('/styles.css')
def styles():
    return send_from_directory('.', 'styles.css')

OFFSET_PATTERNS = {
    'ESP': [
        'public static Camera get_main()',
        'public Vector3 WorldToScreenPoint(Vector3 position)',
        'public Transform get_transform()',
        'public Vector3 get_position()',
        'public GameObject get_gameObject()',
        'public Vector3 get_eulerAngles',
        'public static MatchGame get_MatchGame',
        'public static Pawn get_LocalPawn()',
        'public bool get_IsFiring()',
        'public bool IsAiming()',
        'public bool get_TriggerQuickKnife()',
        'public virtual void set_AimRotation(Quaternion value)',
        'public virtual Quaternion get_MapShowRotation()',
        'public BRDroppedPickUpMgr get_DroppedPickUpMgr()',
        'public Vector3 get_LastPawnPos()',
        'public virtual Vector3 get_HeadPosition()',
        'public virtual string get_PlayerName()',
        'public uint get_TeamSeatId()',
        'public static Touch GetTouch(int index)',
        'public static bool get_touchSupported()',
        'public static int get_touchCount()',
        'public static Vector3 get_mousePosition()',
        'public static int get_width()',
        'public static int get_height()',
        'public static float get_dpi()',
        'public virtual uint get_TeamId()',
        'public int m_DefaultOpMode',
        'private bool m_IsBot',
        'protected bool m_IsAlive',
        'protected bool IsFadeOut',
        'protected Transform m_Mesh',
        'protected Transform m_HeadBone',
        'private bool bDiedRespawn',
        'private bool m_IsPlayerDead',
        'protected string m_NickName',
        'private AttackableTargetInfo m_AttackableInfo',
        'protected float m_Health',
        'protected float m_MaxHealth',
        'private List<> m_AllVehicles',
        'private readonly PawnList EnemyPawns',
        'protected int m_LastFireWeaponName',
        'public int vehicleType',
        'protected LethalAndTacticalConfConfig mThrowConf',
        'protected Dictionary<> mNormalItemEntityDic',
        'public static void SetResolution(int width, int height, bool fullscreen, int preferredRefreshRate)'
    ],
    'Wallhack': [
        'public override void OnReSpawnPlayer(Vector3 serverSyncPos)'
    ],
    'Hitbox': [
        'protected virtual bool SingleLineCheckPhysics(int hitType, AttackableTarget hitTarget, Collider hitCollider, Vector3 startPos, Vector3 dir, ImpactInfo impactInfo)'
    ],
    'Aim Assist': [
        'protected virtual float GetAssitAimSpeed(Vector3 assistCentorPos, float assistDis, float dis, float angle, bool isPVE, bool gamepadInput)'
    ],
    'No Recoil': [
        'private float GetScaleRecoil'
    ],
    'No Reload': [
        'public float get_ChangeClipTime',
        'public float get_ChangeClipLoopTime'
    ],
    'No Spread': [
        'protected float GetRealSpreadModifier'
    ],
    'No Shake': [
        'private void UpdateCameraShake'
    ],
    'Fast Scope': [
        'public float get_AimingTime'
    ],
    'Fast Switch': [
        'public float get_EquipTime'
    ],
    'Anti Flashbang': [
        'public float get_FlashBangTimeScale'
    ],
    'Weapon Kinetic': [
        'public bool get_IsKineticArmor'
    ],
    'Jet Jump': [
        'public void set_RatioOfVelocityY(float value)'
    ],
    'Jet Slide': [
        'public bool CanBoostSlide()'
    ],
    'Spectate No Delay': [
        'public bool NeedDelayProcess()',
        'public bool ProcessForDelay(byte[] packData, int PackDataCount, int Sequence, float timeQueued, int aiIndex)'
    ],
    'Small Crosshair': [
        'public bool get_UseCrosshairFireSizeBindInaccuracy()',
        'public float get_CrosshairSizeScaleAiming()'
    ],
    'Unlimited Bullets': [
        'public int get_ShotCost()'
    ],
    'No Overheat': [
        'public float get_AddHotTime()'
    ],
    'One Shot Sniper': [
        'public bool get_IsSingleShot()'
    ],
    'FireRate': [
        'public float get_FireBoltTime()',
        'public virtual float get_FireInterval()'
    ],
    'Instant Fire': [
        'public float get_AutoAssistAimRatesAiming()',
        'public float get_AutoLockTime()',
        'public float get_AssistAimInterval()'
    ],
    'Advance UAV': [
        'public virtual bool get_AdvanceUAVEnabled()'
    ],
    'No Parachute': [
        'public void OpenParachute(bool isAuto)'
    ],
    'Fast Dive': [
        'public bool IsAutoOpenWingsuit()'
    ],
    'Smooth FOV': [
        'public float GetMaxFov_1p()',
        'public float GetMaxFov_3p()'
    ],
    'Fast Snowb': [
        'protected float get_m_PhysSkisMaxSpeed()',
        'protected virtual float CalcFinalMoveScale()'
    ],
    'Speed Hack': [
        'public float get_AccelerationForwardSpeedUp()',
        'public float get_MaxVelocityForwardSpeedUp()'
    ],
    'Skip Tutorial': [
        'public static bool IsTutorialEnabled()'
    ],
    'Vulkan': [
        'public bool get_EnableVulkan()',
        'public void set_EnableVulkan(bool value)'
    ],
    'Long Execute': [
        'public int CheckTargetIsValid(Pawn tempPawn, out float distance)',
        'private bool CheckExecution_ObstacleAround()',
        'public bool CheckTargetIsValid_ManualParameter(Pawn tempPawn, out float distance)',
        'public void RequestCancelExecution(bool bForceInterrupt)'
    ],
    'Red Wallhack': [
        'public bool get_IsInEM3Eye()',
        'private float GetAccDistance()'
    ],
    'Outline Wallhack': [
        'private bool IsEffectActive()',
        'private bool IsEffectActive()'
    ],
    'Fast Loot': [
        'public float GetPickUpTime()'
    ],   
    'Fast Revive': [
        'public void set_ReviveTime(float value)'
    ],
}

# Paths removed — dump files are now uploaded per-request (Vercel serverless)
OLD_FILE = None
NEW_FILE = None

FEATURES_PER_PAGE = 8

def extract_function_name_from_pattern(pattern):
    pattern = pattern.strip()
    
    if '(' in pattern:
        func_part = pattern.split('(')[0].strip()
        parts = func_part.split()
        if parts:
            return parts[-1]
    else:
        parts = pattern.split()
        if parts:
            return parts[-1].rstrip(';')
    
    return None

FUNCTION_NAME_TO_FEATURE = {}
for feature, patterns in OFFSET_PATTERNS.items():
    for pattern in patterns:
        func_name = extract_function_name_from_pattern(pattern)
        if func_name:
            if func_name not in FUNCTION_NAME_TO_FEATURE:
                FUNCTION_NAME_TO_FEATURE[func_name] = []
            FUNCTION_NAME_TO_FEATURE[func_name].append((feature, pattern))

def search_pattern_in_content(pattern, content, feature_name, pattern_index, is_field_pattern=False):
    if pattern == 'public Vector3 get_eulerAngles':
        class_match = re.search(r'(public class Transform : Component, IEnumerable.*?)(?=public (?:class|struct) [^{]+?// TypeDefIndex: \d+|$)', content, re.DOTALL)
        if class_match:
            class_content = class_match.group(1)
            rva_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?' + re.escape(pattern), class_content, re.DOTALL)
            if rva_match:
                return rva_match.group(1)
    
    elif pattern == 'public bool get_IsFiring()':
        class_match = re.search(r'(public class Pawn : AttackableTarget, IDataPropertyWrapper, MovePlatformAttachable.*?)(?=public (?:class|struct) [^{]+?// TypeDefIndex: \d+|$)', content, re.DOTALL)
        if class_match:
            class_content = class_match.group(1)
            rva_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?' + re.escape(pattern), class_content, re.DOTALL)
            if rva_match:
                return rva_match.group(1)

    elif pattern_index == 1 and feature_name == 'Wallhack':
        class_match = re.search(r'(public class PlayerPawn : Pawn, IDataPropertyWrapper, IRayCastInteract.*?)(?=public (?:class|struct) [^{]+?// TypeDefIndex: \d+|$)', content, re.DOTALL)
        if class_match:
            class_content = class_match.group(1)
            rva_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?' + re.escape(pattern), class_content, re.DOTALL)
            if rva_match:
                return rva_match.group(1)
  
    elif pattern_index == 1 and feature_name == 'Hitbox':
        pattern_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?SingleLineCheckPhysics', content, re.DOTALL)
        if pattern_match:
            return pattern_match.group(1)
  
    elif pattern_index == 1 and feature_name == 'Aim Assist':
        pattern_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetAssitAimSpeed', content, re.DOTALL)
        if pattern_match:
            return pattern_match.group(1)
  
    elif pattern_index == 1 and feature_name == 'No Recoil':
        pattern_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetScaleRecoil', content, re.DOTALL)
        if pattern_match:
            return pattern_match.group(1)
  
    elif pattern_index == 1 and feature_name == 'No Spread':
        pattern_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetRealSpreadModifier', content, re.DOTALL)
        if pattern_match:
            return pattern_match.group(1)

    elif pattern_index == 1 and feature_name == 'No Shake':
        pattern_match = re.search(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?UpdateCameraShake', content, re.DOTALL)
        if pattern_match:
            return pattern_match.group(1)

    search_approaches = []
    
    if is_field_pattern:
        search_approaches.append((re.escape(pattern) + r'.*?//\s*(0x[0-9A-Fa-f]+)', re.DOTALL))
        if pattern.endswith(';'):
            pattern_no_semicolon = pattern.rstrip(';')
            search_approaches.append((re.escape(pattern_no_semicolon) + r'[^/]*?//\s*(0x[0-9A-Fa-f]+)', re.DOTALL))
    else:
        search_approaches.append((r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?' + re.escape(pattern), re.DOTALL))
        
        if '(' in pattern and ')' in pattern:
            method_base = pattern.split('(')[0].strip()
            search_approaches.append((r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?' + re.escape(method_base) + r'\([^)]*\)', re.DOTALL))
        
        if ' ' in pattern and '(' not in pattern:
            method_name = pattern.split()[-1].strip()
            search_approaches.append((r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?\b' + re.escape(method_name) + r'\b', re.IGNORECASE))
    
    for regex_pattern, flags in search_approaches:
        matches = re.finditer(regex_pattern, content, flags)
        for match in matches:
            rva_value = match.group(1)
            if not is_field_pattern:
                return rva_value
            else:
                return rva_value
    
    if not is_field_pattern:
        fallback_patterns = []
        
        if 'SingleLineCheckPhysics' in pattern:
            fallback_patterns.append(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?SingleLineCheckPhysics\([^)]*\)')
        elif 'GetAssitAimSpeed' in pattern or 'GetAssistAimSpeed' in pattern:
            fallback_patterns.extend([
                r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetAssitAimSpeed\([^)]*\)',
                r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetAssistAimSpeed\([^)]*\)'
            ])
        elif 'GetScaleRecoil' in pattern:
            fallback_patterns.append(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetScaleRecoil')
        elif 'GetRealSpreadModifier' in pattern:
            fallback_patterns.append(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?GetRealSpreadModifier')
        elif 'UpdateCameraShake' in pattern:
            fallback_patterns.append(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?UpdateCameraShake')
        
        for fallback_pattern in fallback_patterns:
            matches = re.finditer(fallback_pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                rva_value = match.group(1)
                return rva_value
    
    if is_field_pattern:
        field_name = pattern.split()[-1].rstrip(';')
        fallback_match = re.search(rf'\b{re.escape(field_name)}\b[^/]*?//\s*(0x[0-9A-Fa-f]+)', content, re.IGNORECASE)
        if fallback_match:
            return fallback_match.group(1)
    
    return None

def extract_offsets_from_file(feature, content=None):
    if content is None:
        return ["Error: No dump file uploaded. Please upload dump_new.cs first."]

    try:
        patterns = OFFSET_PATTERNS.get(feature, [])
        found = []

        for i, pattern in enumerate(patterns, 1):
            is_field_pattern = any(field_keyword in pattern for field_keyword in ['private', 'protected', 'm_'])

            result = search_pattern_in_content(pattern, content, feature, i, is_field_pattern)

            if result:
                found.append(f"{feature.replace(' ', '')}{i} = {result}")
            else:
                found.append(f"{feature.replace(' ', '')}{i} = Not found for pattern: {pattern}")

        return found if found else [f"No {feature} offsets found"]

    except Exception as e:
        return [f"Error: {str(e)}"]

def extract_all_offsets(content=None):
    if content is None:
        return ["Error: No dump file uploaded. Please upload dump_new.cs first."]

    try:
        results = []

        for feature, patterns in OFFSET_PATTERNS.items():
            feature_results = []
            for i, pattern in enumerate(patterns, 1):
                is_field_pattern = any(field_keyword in pattern for field_keyword in ['private', 'protected', 'm_'])

                result = search_pattern_in_content(pattern, content, feature, i, is_field_pattern)

                if result:
                    feature_results.append(f"{feature.replace(' ', '')}{i} = {result}")

            if feature_results:
                results.append(f"=== {feature.upper()} RESULTS ===")
                results.extend(feature_results)
                results.append(f"=== END OF {feature.upper()} DATA ===")
                results.append("")

        return results if results else ["No offsets found"]

    except Exception as e:
        return [f"Error: {str(e)}"]

def format_results_for_feature(feature, raw_results):
    if any("Error" in result for result in raw_results):
        return "\n".join(raw_results)
    formatted = [f"=== {feature.upper()} EXTRACTION RESULTS ===", ""]
    formatted.extend(raw_results)
    formatted.append("")
    formatted.append(f"=== END OF {feature.upper()} DATA ===")
    return "\n".join(formatted)

def format_all_results(raw_results):
    return "\n".join(raw_results)

def build_offset_map_from_old_dump(dump_old_content):
    if not dump_old_content:
        return {}
    
    offset_map = {}
    
    method_pattern = r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?((?:public|private|protected)\s+(?:static\s+)?(?:virtual\s+)?[\w<>,\[\]\s]+\s+(\w+)\s*\([^)]*\))'
    
    for match in re.finditer(method_pattern, dump_old_content, re.IGNORECASE):
        old_offset = match.group(1).upper()
        full_signature = match.group(2)
        method_name = match.group(3)
        
        if old_offset not in offset_map:
            offset_map[old_offset] = {
                'method_name': method_name,
                'signature': full_signature
            }
    
    field_pattern = r'([\w<>,\[\]\s]+\s+(\w+))\s*;?\s*//\s*(0x[0-9A-Fa-f]+)'
    for match in re.finditer(field_pattern, dump_old_content, re.IGNORECASE):
        field_signature = match.group(1)
        field_name = match.group(2)
        old_offset = match.group(3).upper()
        
        if old_offset not in offset_map:
            offset_map[old_offset] = {
                'method_name': field_name,
                'signature': field_signature,
                'is_field': True
            }
    
    return offset_map

def find_offset_with_fallback(old_offset, offset_map, dump_new_content):
    if not offset_map or not old_offset:
        return None
    
    old_offset_clean = old_offset.upper()
    
    if old_offset_clean not in offset_map:
        return None
    
    mapping = offset_map[old_offset_clean]
    method_name = mapping['method_name']
    
    if mapping.get('is_field'):
        field_signature = mapping['signature']
        new_field_pattern = re.escape(field_signature) + r'\s*;?\s*//\s*(0x[0-9A-Fa-f]+)'
        new_field_match = re.search(new_field_pattern, dump_new_content, re.IGNORECASE)
        if new_field_match:
            return new_field_match.group(1)
    else:
        new_offset_pattern = r'//\s*RVA:\s*(0x[0-9A-Fa-f]+)[^\n]*\n[^\n]*?\b' + re.escape(method_name) + r'\s*\('
        new_offset_match = re.search(new_offset_pattern, dump_new_content, re.IGNORECASE)
        if new_offset_match:
            return new_offset_match.group(1)
    
    return None

def find_offset_for_function(function_name, dump_content):
    if function_name in FUNCTION_NAME_TO_FEATURE:
        matches = FUNCTION_NAME_TO_FEATURE[function_name]
        for feature, pattern in matches:
            patterns = OFFSET_PATTERNS[feature]
            pattern_index = patterns.index(pattern) + 1
            is_field_pattern = any(field_keyword in pattern for field_keyword in ['private', 'protected', 'm_'])
            result = search_pattern_in_content(pattern, dump_content, feature, pattern_index, is_field_pattern)
            if result:
                return result
    
    return None

def update_cpp_file(file_content, dump_new_content, offset_map=None):
    hook_pattern = r'HOOK_LIB\s*\(\s*"([^"]+)"\s*,\s*"(0x[0-9A-Fa-f]+)"\s*,\s*(\w+)\s*,\s*orig_\w+\s*\)'
    
    updated_content = file_content
    updates_made = []
    
    for match in re.finditer(hook_pattern, file_content):
        lib_name = match.group(1)
        old_offset = match.group(2)
        function_name = match.group(3)
        
        new_offset = find_offset_for_function(function_name, dump_new_content)
        
        if not new_offset and offset_map:
            new_offset = find_offset_with_fallback(old_offset, offset_map, dump_new_content)
            if new_offset:
                updates_made.append({
                    'type': 'HOOK_LIB',
                    'library': lib_name,
                    'function': function_name,
                    'old_offset': old_offset,
                    'new_offset': new_offset,
                    'status': 'SUCCESS',
                    'method': 'FALLBACK'
                })
                old_hook = match.group(0)
                new_hook = old_hook.replace(old_offset, new_offset)
                updated_content = updated_content.replace(old_hook, new_hook)
                continue
        
        if new_offset:
            old_hook = match.group(0)
            new_hook = old_hook.replace(old_offset, new_offset)
            updated_content = updated_content.replace(old_hook, new_hook)
            updates_made.append({
                'type': 'HOOK_LIB',
                'library': lib_name,
                'function': function_name,
                'old_offset': old_offset,
                'new_offset': new_offset,
                'status': 'SUCCESS',
                'method': 'DIRECT'
            })
        else:
            updates_made.append({
                'type': 'HOOK_LIB',
                'library': lib_name,
                'function': function_name,
                'old_offset': old_offset,
                'new_offset': 'NOT FOUND',
                'status': 'FAILED',
                'method': 'NONE'
            })
    
    return updated_content, updates_made

def update_defines_file(file_content, dump_new_content, offset_map=None):
    updated_content = file_content
    updates_made = []
    
    define_to_api = {}
    api_pattern = r'#define\s+(Class_\w+|[\w_]+)\s+\(m_unity\s+\+\s+(api\d+)\)'
    for match in re.finditer(api_pattern, file_content):
        define_name = match.group(1)
        api_var = match.group(2)
        define_to_api[define_name] = api_var
    
    uintptr_pattern = r'uintptr_t\s+(api\d+)\s*=\s*(0x[0-9A-Fa-f]+)\s*;'
    
    for match in re.finditer(uintptr_pattern, file_content):
        api_var = match.group(1)
        old_offset = match.group(2)
        
        matching_define = None
        for define_name, define_api in define_to_api.items():
            if define_api == api_var:
                matching_define = define_name
                break
        
        if matching_define:
            function_base_name = matching_define.split('_')[-1]
            
            new_offset = find_offset_for_function(function_base_name, dump_new_content)
            
            if not new_offset:
                parts = matching_define.replace('Class_', '').replace('Pawn_', '').replace('Input_', '').replace('Screen_', '').replace('Camera_', '').replace('Component_', '').replace('Transform_', '').replace('Gameplay_', '').replace('MatchGame_', '').split('_')
                for i in range(len(parts)):
                    test_name = '_'.join(parts[i:])
                    new_offset = find_offset_for_function(test_name, dump_new_content)
                    if new_offset:
                        break
            
            if not new_offset and offset_map:
                new_offset = find_offset_with_fallback(old_offset, offset_map, dump_new_content)
                if new_offset:
                    old_line = match.group(0)
                    new_line = old_line.replace(old_offset, new_offset)
                    updated_content = updated_content.replace(old_line, new_line)
                    updates_made.append({
                        'type': 'uintptr_t',
                        'variable': api_var,
                        'function': matching_define,
                        'old_offset': old_offset,
                        'new_offset': new_offset,
                        'status': 'SUCCESS',
                        'method': 'FALLBACK'
                    })
                    continue
            
            if new_offset:
                old_line = match.group(0)
                new_line = old_line.replace(old_offset, new_offset)
                updated_content = updated_content.replace(old_line, new_line)
                updates_made.append({
                    'type': 'uintptr_t',
                    'variable': api_var,
                    'function': matching_define,
                    'old_offset': old_offset,
                    'new_offset': new_offset,
                    'status': 'SUCCESS',
                    'method': 'DIRECT'
                })
            else:
                updates_made.append({
                    'type': 'uintptr_t',
                    'variable': api_var,
                    'function': matching_define,
                    'old_offset': old_offset,
                    'new_offset': 'NOT FOUND',
                    'status': 'FAILED',
                    'method': 'NONE'
                })
        else:
            updates_made.append({
                'type': 'uintptr_t',
                'variable': api_var,
                'function': 'NO MAPPING',
                'old_offset': old_offset,
                'new_offset': 'SKIPPED',
                'status': 'SKIPPED',
                'method': 'NONE'
            })
    
    standalone_define_pattern = r'#define\s+(Class_\w+|[\w_]+)\s+\((m_unity\s+\+\s+)?(0x[0-9A-Fa-f]+)\s*\)'
    for match in re.finditer(standalone_define_pattern, file_content):
        define_name = match.group(1)
        old_offset = match.group(3)
        
        if any(u['old_offset'] == old_offset and u['status'] == 'SUCCESS' for u in updates_made):
            continue
        
        function_base_name = define_name.split('_')[-1]
        
        new_offset = find_offset_for_function(function_base_name, dump_new_content)
        
        if not new_offset:
            parts = define_name.replace('Class_', '').replace('Pawn_', '').replace('Input_', '').replace('Screen_', '').replace('Camera_', '').replace('Component_', '').replace('Transform_', '').replace('Gameplay_', '').replace('MatchGame_', '').split('_')
            for i in range(len(parts)):
                test_name = '_'.join(parts[i:])
                new_offset = find_offset_for_function(test_name, dump_new_content)
                if new_offset:
                    break
        
        if not new_offset and offset_map:
            new_offset = find_offset_with_fallback(old_offset, offset_map, dump_new_content)
            if new_offset:
                old_line = match.group(0)
                new_line = old_line.replace(old_offset, new_offset)
                updated_content = updated_content.replace(old_line, new_line)
                updates_made.append({
                    'type': '#define',
                    'variable': define_name,
                    'function': function_base_name,
                    'old_offset': old_offset,
                    'new_offset': new_offset,
                    'status': 'SUCCESS',
                    'method': 'FALLBACK'
                })
                continue
        
        if new_offset:
            old_line = match.group(0)
            new_line = old_line.replace(old_offset, new_offset)
            updated_content = updated_content.replace(old_line, new_line)
            updates_made.append({
                'type': '#define',
                'variable': define_name,
                'function': function_base_name,
                'old_offset': old_offset,
                'new_offset': new_offset,
                'status': 'SUCCESS',
                'method': 'DIRECT'
            })
        else:
            updates_made.append({
                'type': '#define',
                'variable': define_name,
                'function': function_base_name,
                'old_offset': old_offset,
                'new_offset': 'NOT FOUND',
                'status': 'FAILED',
                'method': 'NONE'
            })
    
    field_pattern = r'#define\s+(Class_\w+)\s+\((0x[0-9A-Fa-f]+)\s*\)'
    for match in re.finditer(field_pattern, file_content):
        define_name = match.group(1)
        old_offset = match.group(2)
        
        if any(u['old_offset'] == old_offset and u['status'] == 'SUCCESS' for u in updates_made):
            continue
        
        updates_made.append({
            'type': '#define (field)',
            'variable': define_name,
            'function': 'FIELD OFFSET',
            'old_offset': old_offset,
            'new_offset': 'KEPT',
            'status': 'KEPT',
            'method': 'NONE'
        })
    
    return updated_content, updates_made
    updated_content = file_content
    updates_made = []
    
    define_to_api = {}
    api_pattern = r'#define\s+(Class_\w+|[\w_]+)\s+\(m_unity\s+\+\s+(api\d+)\)'
    for match in re.finditer(api_pattern, file_content):
        define_name = match.group(1)
        api_var = match.group(2)
        define_to_api[define_name] = api_var
    
    uintptr_pattern = r'uintptr_t\s+(api\d+)\s*=\s*(0x[0-9A-Fa-f]+)\s*;'
    
    for match in re.finditer(uintptr_pattern, file_content):
        api_var = match.group(1)
        old_offset = match.group(2)
        
        matching_define = None
        for define_name, define_api in define_to_api.items():
            if define_api == api_var:
                matching_define = define_name
                break
        
        if matching_define:
            function_base_name = matching_define.split('_')[-1]
            
            new_offset = find_offset_for_function(function_base_name, dump_new_content)
            
            if not new_offset:
                parts = matching_define.replace('Class_', '').replace('Pawn_', '').replace('Input_', '').replace('Screen_', '').replace('Camera_', '').replace('Component_', '').replace('Transform_', '').replace('Gameplay_', '').replace('MatchGame_', '').split('_')
                for i in range(len(parts)):
                    test_name = '_'.join(parts[i:])
                    new_offset = find_offset_for_function(test_name, dump_new_content)
                    if new_offset:
                        break
            
            if not new_offset and dump_old_content:
                new_offset = find_offset_with_fallback(function_base_name, old_offset, dump_new_content, dump_old_content)
                if new_offset:
                    old_line = match.group(0)
                    new_line = old_line.replace(old_offset, new_offset)
                    updated_content = updated_content.replace(old_line, new_line)
                    updates_made.append({
                        'type': 'uintptr_t',
                        'variable': api_var,
                        'function': matching_define,
                        'old_offset': old_offset,
                        'new_offset': new_offset,
                        'status': 'SUCCESS',
                        'method': 'FALLBACK'
                    })
                    continue
            
            if new_offset:
                old_line = match.group(0)
                new_line = old_line.replace(old_offset, new_offset)
                updated_content = updated_content.replace(old_line, new_line)
                updates_made.append({
                    'type': 'uintptr_t',
                    'variable': api_var,
                    'function': matching_define,
                    'old_offset': old_offset,
                    'new_offset': new_offset,
                    'status': 'SUCCESS',
                    'method': 'DIRECT'
                })
            else:
                updates_made.append({
                    'type': 'uintptr_t',
                    'variable': api_var,
                    'function': matching_define,
                    'old_offset': old_offset,
                    'new_offset': 'NOT FOUND',
                    'status': 'FAILED',
                    'method': 'NONE'
                })
        else:
            updates_made.append({
                'type': 'uintptr_t',
                'variable': api_var,
                'function': 'NO MAPPING',
                'old_offset': old_offset,
                'new_offset': 'SKIPPED',
                'status': 'SKIPPED',
                'method': 'NONE'
            })
    
    standalone_define_pattern = r'#define\s+(Class_\w+|[\w_]+)\s+\((m_unity\s+\+\s+)?(0x[0-9A-Fa-f]+)\s*\)'
    for match in re.finditer(standalone_define_pattern, file_content):
        define_name = match.group(1)
        old_offset = match.group(3)
        
        if any(u['old_offset'] == old_offset and u['status'] == 'SUCCESS' for u in updates_made):
            continue
        
        function_base_name = define_name.split('_')[-1]
        
        new_offset = find_offset_for_function(function_base_name, dump_new_content)
        
        if not new_offset:
            parts = define_name.replace('Class_', '').replace('Pawn_', '').replace('Input_', '').replace('Screen_', '').replace('Camera_', '').replace('Component_', '').replace('Transform_', '').replace('Gameplay_', '').replace('MatchGame_', '').split('_')
            for i in range(len(parts)):
                test_name = '_'.join(parts[i:])
                new_offset = find_offset_for_function(test_name, dump_new_content)
                if new_offset:
                    break
        
        if not new_offset and dump_old_content:
            new_offset = find_offset_with_fallback(function_base_name, old_offset, dump_new_content, dump_old_content)
            if new_offset:
                old_line = match.group(0)
                new_line = old_line.replace(old_offset, new_offset)
                updated_content = updated_content.replace(old_line, new_line)
                updates_made.append({
                    'type': '#define',
                    'variable': define_name,
                    'function': function_base_name,
                    'old_offset': old_offset,
                    'new_offset': new_offset,
                    'status': 'SUCCESS',
                    'method': 'FALLBACK'
                })
                continue
        
        if new_offset:
            old_line = match.group(0)
            new_line = old_line.replace(old_offset, new_offset)
            updated_content = updated_content.replace(old_line, new_line)
            updates_made.append({
                'type': '#define',
                'variable': define_name,
                'function': function_base_name,
                'old_offset': old_offset,
                'new_offset': new_offset,
                'status': 'SUCCESS',
                'method': 'DIRECT'
            })
        else:
            updates_made.append({
                'type': '#define',
                'variable': define_name,
                'function': function_base_name,
                'old_offset': old_offset,
                'new_offset': 'NOT FOUND',
                'status': 'FAILED',
                'method': 'NONE'
            })
    
    field_pattern = r'#define\s+(Class_\w+)\s+\((0x[0-9A-Fa-f]+)\s*\)'
    for match in re.finditer(field_pattern, file_content):
        define_name = match.group(1)
        old_offset = match.group(2)
        
        if any(u['old_offset'] == old_offset and u['status'] == 'SUCCESS' for u in updates_made):
            continue
        
        updates_made.append({
            'type': '#define (field)',
            'variable': define_name,
            'function': 'FIELD OFFSET',
            'old_offset': old_offset,
            'new_offset': 'KEPT',
            'status': 'KEPT',
            'method': 'NONE'
        })
    
    return updated_content, updates_made

def generate_update_log(updates_made, file_type='unknown'):
    log_lines = []
    log_lines.append("=" * 80)
    log_lines.append("OFFSET UPDATE LOG")
    log_lines.append("=" * 80)
    log_lines.append(f"File Type: {file_type}")
    log_lines.append("")
    
    success_count = sum(1 for u in updates_made if u.get('status') == 'SUCCESS')
    direct_count = sum(1 for u in updates_made if u.get('method') == 'DIRECT')
    fallback_count = sum(1 for u in updates_made if u.get('method') == 'FALLBACK')
    failed_count = sum(1 for u in updates_made if u.get('status') == 'FAILED')
    skipped_count = sum(1 for u in updates_made if u.get('status') == 'SKIPPED')
    kept_count = sum(1 for u in updates_made if u.get('status') == 'KEPT')
    
    log_lines.append(f"SUMMARY:")
    log_lines.append(f"  ✓ Successfully Updated: {success_count}")
    log_lines.append(f"    → Direct Match: {direct_count}")
    log_lines.append(f"    → Fallback (Old Dump): {fallback_count}")
    log_lines.append(f"  ✗ Failed to Find: {failed_count}")
    if skipped_count > 0:
        log_lines.append(f"  ⊘ Skipped (No Mapping): {skipped_count}")
    if kept_count > 0:
        log_lines.append(f"  ⊙ Kept (Field Offsets): {kept_count}")
    log_lines.append("")
    log_lines.append("=" * 80)
    log_lines.append("")
    
    if direct_count > 0:
        log_lines.append("DIRECT MATCH UPDATES:")
        log_lines.append("-" * 80)
        for update in updates_made:
            if update.get('status') == 'SUCCESS' and update.get('method') == 'DIRECT':
                if update.get('type') == 'HOOK_LIB':
                    log_lines.append(f"✓ HOOK_LIB: {update['function']}")
                    log_lines.append(f"  Library: {update.get('library', 'N/A')}")
                    log_lines.append(f"  Old: {update['old_offset']} → New: {update['new_offset']}")
                else:
                    log_lines.append(f"✓ {update.get('type', 'Unknown')}: {update.get('variable', update.get('function'))}")
                    if 'function' in update and update.get('variable') != update.get('function'):
                        log_lines.append(f"  Function: {update['function']}")
                    log_lines.append(f"  Old: {update['old_offset']} → New: {update['new_offset']}")
                log_lines.append("")
    
    if fallback_count > 0:
        log_lines.append("FALLBACK UPDATES (Found via Old Dump Context):")
        log_lines.append("-" * 80)
        for update in updates_made:
            if update.get('status') == 'SUCCESS' and update.get('method') == 'FALLBACK':
                if update.get('type') == 'HOOK_LIB':
                    log_lines.append(f"⚡ HOOK_LIB: {update['function']}")
                    log_lines.append(f"  Library: {update.get('library', 'N/A')}")
                    log_lines.append(f"  Old: {update['old_offset']} → New: {update['new_offset']} [FALLBACK]")
                else:
                    log_lines.append(f"⚡ {update.get('type', 'Unknown')}: {update.get('variable', update.get('function'))}")
                    if 'function' in update and update.get('variable') != update.get('function'):
                        log_lines.append(f"  Function: {update['function']}")
                    log_lines.append(f"  Old: {update['old_offset']} → New: {update['new_offset']} [FALLBACK]")
                log_lines.append("")
    
    if failed_count > 0:
        log_lines.append("FAILED UPDATES (Not Found in Either Dump):")
        log_lines.append("-" * 80)
        for update in updates_made:
            if update.get('status') == 'FAILED':
                if update.get('type') == 'HOOK_LIB':
                    log_lines.append(f"✗ HOOK_LIB: {update['function']}")
                    log_lines.append(f"  Library: {update.get('library', 'N/A')}")
                else:
                    log_lines.append(f"✗ {update.get('type', 'Unknown')}: {update.get('variable', update.get('function'))}")
                    if 'function' in update and update.get('variable') != update.get('function'):
                        log_lines.append(f"  Function: {update['function']}")
                log_lines.append(f"  Old: {update['old_offset']} → Status: NOT FOUND")
                log_lines.append("")
    
    if skipped_count > 0:
        log_lines.append("SKIPPED (No Define Mapping):")
        log_lines.append("-" * 80)
        for update in updates_made:
            if update.get('status') == 'SKIPPED':
                log_lines.append(f"⊘ {update.get('type', 'Unknown')}: {update.get('variable')}")
                log_lines.append(f"  Old: {update['old_offset']}")
                log_lines.append("")
    
    log_lines.append("=" * 80)
    log_lines.append("END OF LOG")
    log_lines.append("=" * 80)
    
    return "\n".join(log_lines)

def process_uploaded_file(file_content, dump_new_content, offset_map, filename):
    if 'HOOK_LIB' in file_content:
        return update_cpp_file(file_content, dump_new_content, offset_map)
    elif 'uintptr_t' in file_content and '#define' in file_content:
        return update_defines_file(file_content, dump_new_content, offset_map)
    else:
        return update_cpp_file(file_content, dump_new_content, offset_map)

@app.route('/', defaults={'page': 1})
@app.route('/<int:page>')
def index(page=1):
    all_features = list(OFFSET_PATTERNS.keys())
    
    start_idx = (page - 1) * FEATURES_PER_PAGE
    end_idx = start_idx + FEATURES_PER_PAGE
    features = all_features[start_idx:end_idx]
    
    return render_template('index.html',
                           features=features,
                           results=False,
                           formatted_results=None,
                           selected_feature=None,
                           current_page=page,
                           has_next=end_idx < len(all_features))

@app.route('/', methods=['POST'])
@app.route('/<int:page>', methods=['POST'])
def index_post(page=1):
    action = request.form.get('action')
    
    all_features = list(OFFSET_PATTERNS.keys())
    start_idx = (page - 1) * FEATURES_PER_PAGE
    end_idx = start_idx + FEATURES_PER_PAGE
    features = all_features[start_idx:end_idx]
    
    # Read dump_new.cs from the uploaded file in this request
    dump_new_content = None
    dump_new_file = request.files.get('dump_new')
    if dump_new_file and dump_new_file.filename:
        dump_new_content = dump_new_file.read().decode('utf-8', errors='ignore')

    if action == 'extract':
        feature = request.form.get('feature')
        raw_results = extract_offsets_from_file(feature, dump_new_content)
        formatted_results = format_results_for_feature(feature, raw_results)

        return render_template('index.html',
                               features=features,
                               results=True,
                               formatted_results=formatted_results,
                               selected_feature=feature,
                               current_page=page,
                               has_next=end_idx < len(all_features))

    elif action == 'update_all':
        raw_results = extract_all_offsets(dump_new_content)
        formatted_results = format_all_results(raw_results)

        return render_template('index.html',
                               features=features,
                               results=True,
                               formatted_results=formatted_results,
                               selected_feature=None,
                               current_page=page,
                               has_next=end_idx < len(all_features))

    return redirect(f'/{page}' if page > 1 else '/')

@app.route("/preview_all", methods=['POST'])
def preview_all():
    dump_new_content = None
    dump_new_file = request.files.get('dump_new')
    if dump_new_file and dump_new_file.filename:
        dump_new_content = dump_new_file.read().decode('utf-8', errors='ignore')
    results = extract_all_offsets(dump_new_content)
    formatted_results = format_all_results(results)
    return jsonify({"results": formatted_results})

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('upload_page'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('upload_page'))
    
    if not (file.filename.endswith('.cpp') or file.filename.endswith('.h')):
        flash('Only .cpp and .h files are allowed')
        return redirect(url_for('upload_page'))

    dump_new_file = request.files.get('dump_new')
    if not dump_new_file or not dump_new_file.filename:
        flash('Error: dump_new.cs is required. Please upload it along with your file.')
        return redirect(url_for('upload_page'))

    try:
        file_content = file.read().decode('utf-8')
        dump_new_content = dump_new_file.read().decode('utf-8', errors='ignore')

        offset_map = None
        dump_old_file = request.files.get('dump_old')
        if dump_old_file and dump_old_file.filename:
            dump_old_content = dump_old_file.read().decode('utf-8', errors='ignore')
            offset_map = build_offset_map_from_old_dump(dump_old_content)
        
        updated_content, updates_made = process_uploaded_file(file_content, dump_new_content, offset_map, file.filename)
        
        file_type = 'HOOK_LIB Format'
        if 'uintptr_t' in file_content and '#define' in file_content:
            file_type = 'Defines.h Format'
        
        log_content = generate_update_log(updates_made, file_type)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('updated_' + file.filename, updated_content)
            zip_file.writestr('UPDATE_LOG.txt', log_content)
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'updated_{file.filename.rsplit(".", 1)[0]}_package.zip',
            mimetype='application/zip'
        )
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('upload_page'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
