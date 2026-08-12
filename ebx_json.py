import uuid
import json
import os
import copy
import shutil

import ebx_to_rime

from templates import subWorldDataTemp, objectBlueprintTemp, referenceObjectDataTemp, effectReferenceObjectDataTemp

BUNDLE_PREFIX = 'CustomLevels'
INTERMEDIATE_FOLDER_NAME = 'intermediate'
MAP_SAVES_FOLDER_NAME = 'map_saves'
EBX_FOLDER_NAME = 'ebx_json'
LUA_LEVELS_PATH = os.path.join('ext', 'Shared', 'Levels')

# Fixed namespace so re-baking a project yields the same partition guids for its overridden
# blueprints, which keeps rebuilt bundles diffable and reproducible.
OVERRIDE_PARTITION_NS = uuid.UUID('6f9619ff-8b86-d011-b42d-00c04fc964ff')


def build_override_partitions(json_save, map_name):
	"""Per-instance EBX overrides -> {objectGuid: (partitionGuid, partitionName, partition)}.

	MapEditor clones an instance's blueprint the first time one of its EBX fields is edited, so
	that the edit isolates to that instance. The clone only exists at runtime, so the save carries
	it serialized; without this it is dropped and the baked level silently uses the stock blueprint.

	Each overridden instance gets its OWN partition and only its own ReferenceObjectData is
	repointed, which is what keeps sibling instances of the same prefab on the stock blueprint.
	"""
	overrides = {}

	for entry in json_save.get('ebx') or []:
		object_guid = str(entry.get('objectGuid') or '').strip().lower()
		partition = entry.get('partition')

		if not object_guid or not partition:
			# An empty objectGuid marks an Apply-to-Blueprint partition: it has to REPLACE the
			# stock partition under its original name for every reference to pick it up, including
			# vanilla ones this generator never emits. Bundle naming can't express that yet, so
			# skip it loudly rather than emit a partition nothing points at.
			print('  ! skipping a blueprint-wide override (needs partition shadowing)')
			continue

		partition_guid = str(uuid.uuid5(OVERRIDE_PARTITION_NS, object_guid))
		partition_name = BUNDLE_PREFIX + '/' + map_name + '/' + object_guid
		converted = ebx_to_rime.convert_partition(partition, partition_guid, partition_name)

		dangling = ebx_to_rime.dangling_references(converted)
		if dangling:
			# Compiles fine, fails at load — worth saying before it ships.
			print('  ! %d dangling internal reference(s) in override for %s (first: %s)'
				  % (len(dangling), object_guid, dangling[0][1]))

		overrides[object_guid] = (partition_guid, partition_name, converted)

	return overrides


def create_initial_partition_struct(name):
	ebx = copy.deepcopy(subWorldDataTemp)
	partition_guid = str(uuid.uuid4())
	ebx['PartitionGuid'] = partition_guid

	# TODO: guids should not be random maybe
	sub_world_data_guid = str(uuid.uuid4())
	descriptor_guid = str(uuid.uuid4())
	registry_guid = str(uuid.uuid4())
	world_part_data_guid = str(uuid.uuid4())
	world_part_rod_guid = str(uuid.uuid4())
	ebx['PrimaryInstanceGuid'] = sub_world_data_guid

	# recreate the dict with the generated guids as keys
	new_dict = {
		sub_world_data_guid: ebx['Instances']['SubWorldDataGuid'],
		descriptor_guid: ebx['Instances']['DescriptorGuid'],
		registry_guid: ebx['Instances']['RegistryGuid'],
		world_part_data_guid: ebx['Instances']['WorldPartDataGuid'],
		world_part_rod_guid: ebx['Instances']['WorldPartRODGuid']
	}

	new_dict[sub_world_data_guid]['Descriptor']['InstanceGuid'] = descriptor_guid
	new_dict[sub_world_data_guid]['Descriptor']['PartitionGuid'] = partition_guid
	new_dict[sub_world_data_guid]['RegistryContainer']['InstanceGuid'] = registry_guid
	new_dict[sub_world_data_guid]['RegistryContainer']['PartitionGuid'] = partition_guid

	new_dict[registry_guid]['BlueprintRegistry'][0]['PartitionGuid'] = partition_guid
	new_dict[registry_guid]['BlueprintRegistry'][0]['InstanceGuid'] = sub_world_data_guid
	new_dict[registry_guid]['BlueprintRegistry'][1]['PartitionGuid'] = partition_guid
	new_dict[registry_guid]['BlueprintRegistry'][1]['InstanceGuid'] = world_part_data_guid

	new_dict[world_part_rod_guid]['Blueprint']['PartitionGuid'] = partition_guid
	new_dict[world_part_rod_guid]['Blueprint']['InstanceGuid'] = world_part_data_guid

	new_dict[sub_world_data_guid]['Objects'][0]['PartitionGuid'] = partition_guid
	new_dict[sub_world_data_guid]['Objects'][0]['InstanceGuid'] = world_part_rod_guid
	new_dict[registry_guid]['ReferenceObjectRegistry'][0]['PartitionGuid'] = partition_guid
	new_dict[registry_guid]['ReferenceObjectRegistry'][0]['InstanceGuid'] = world_part_rod_guid

	new_dict[world_part_data_guid]['Name'] = name

	ebx['Instances'] = new_dict
	return ebx


def process_save_file(json_save: dict, world_part_data_name: str, variation_map: dict, overrides: dict = None):
	vanilla_rods = {}
	overrides = overrides or {}
	# Create structure
	ebx = create_initial_partition_struct(world_part_data_name)

	# clean up
	swd = ebx['Instances'][ebx['PrimaryInstanceGuid']]
	rc = ebx['Instances'][swd['RegistryContainer']['InstanceGuid']]
	wprod = ebx['Instances'][swd['Objects'][0]['InstanceGuid']]
	wpd = ebx['Instances'][wprod['Blueprint']['InstanceGuid']]

	for i, obj in enumerate(json_save['data']):
		if obj['origin'] == 3:  # custom children not supported
			continue

		if obj['origin'] == 1 or obj['origin'] == 4:  # vanilla
			# ignore if its a child of a PrefabBlueprint or SpatialPrefabBlueprint (prefab system not yet implemented)
			if 'parentData' in obj and (obj['parentData']['typeName'] == 'PrefabBlueprint' or obj['parentData']['typeName'] == 'SpatialPrefabBlueprint'):
				continue

			# add to table
			rod = obj['originalRef']

			if rod['partitionGuid'] in vanilla_rods:
				vanilla_rods[rod['partitionGuid']].append(rod['instanceGuid'])
			else:
				vanilla_rods[rod['partitionGuid']] = [rod['instanceGuid']]

			if 'isDeleted' in obj:
				continue

		reference_object_data_guid = obj['guid'].lower()

		reference_object_data = None

		# Use effectROD if it's an effect
		if obj['blueprintCtrRef']['typeName'] == 'EffectBlueprint':
			reference_object_data = copy.deepcopy(effectReferenceObjectDataTemp)
		else:
			reference_object_data = copy.deepcopy(referenceObjectDataTemp)

		# An instance with EBX overrides points at its OWN cloned blueprint instead of the stock
		# one. Every other instance of the same prefab is untouched and still resolves the stock
		# blueprint, which is what makes the override per-instance rather than global.
		override = overrides.get(reference_object_data_guid)

		if override is not None:
			override_partition_guid, _, override_partition = override
			reference_object_data['Blueprint']['InstanceGuid'] = override_partition['PrimaryInstanceGuid']
			reference_object_data['Blueprint']['PartitionGuid'] = override_partition_guid

			# A blueprint the level points at must ALSO be registered, exactly as the generator
			# registers the SubWorldData and WorldPartData it creates. Without this the
			# ReferenceObjectData resolves to nothing and the object simply does not appear in the
			# world — no error, it is just missing. (Observed: every overridden light pole vanished
			# from the baked level while unoverridden ones were fine.)
			rc['BlueprintRegistry'].append({
				'PartitionGuid': override_partition_guid,
				'InstanceGuid': override_partition['PrimaryInstanceGuid'],
			})
		else:
			reference_object_data['Blueprint']['InstanceGuid'] = obj['blueprintCtrRef']['instanceGuid']
			reference_object_data['Blueprint']['PartitionGuid'] = obj['blueprintCtrRef']['partitionGuid']
		reference_object_data['IndexInBlueprint'] = len(wpd['Objects']) + 30001
		reference_object_data['IsEventConnectionTarget'] = 3  # Realm.Realm_None
		reference_object_data['IsPropertyConnectionTarget'] = 3
		reference_object_data['CastSunShadowEnable'] = True
		reference_object_data['Excluded'] = False

		# handle variation
		variation = None

		if 'variation' in obj:
			variation = variation_map.get(str(obj['variation']))

		if variation is not None:
			reference_object_data['ObjectVariation'] = {
				'PartitionGuid': variation[0],
				'InstanceGuid': variation[1]
			}

		# # Handle transform 
		# if 'localTransform' and obj['origin'] == 2 in obj:
		# 	reference_object_data['BlueprintTransform'] = obj['localTransform']
		# else:
		reference_object_data['BlueprintTransform'] = obj['transform']

		# Fix left/right difference
		reference_object_data['BlueprintTransform']['right'] = reference_object_data['BlueprintTransform']['left']
		reference_object_data['BlueprintTransform'].pop('left')

		ref = {
			'PartitionGuid': ebx['PartitionGuid'],
			'InstanceGuid': reference_object_data_guid
		}

		# Add to dictionary in root, add reference in worlpartdata.objects and registrycontainer.referenceobjectregistry
		ebx['Instances'][reference_object_data_guid] = reference_object_data
		rc['ReferenceObjectRegistry'].append(ref)
		wpd['Objects'].append(ref)

	return ebx, vanilla_rods


# Outputs a lua file with the gamemode maps, allowing LevelLoader to work with custom bundles and use the same bundle for
# multiple gamemodes. Supports custom gamemodes too
def save_bundles_lua_map(bundles_lua_map: dict, out_dir: str):
	if bundles_lua_map:
		lua_out_path = os.path.join(out_dir, LUA_LEVELS_PATH)
		if not os.path.exists(lua_out_path):
			os.makedirs(lua_out_path)

		bundles_lua_map_json = json.dumps(bundles_lua_map, indent=1)
		bundles_lua_map_json = 'return [[\n' + bundles_lua_map_json + '\n]]'

		with open(os.path.join(lua_out_path, 'BundlesMap.lua'), "w") as f:
			f.write(bundles_lua_map_json)


# Save EBX in JSON files to be later compiled by Rime
def save_ebx_json(ebx: dict, map_name: str, gamemode_name: str):
	ebx_out_path = os.path.join(
		os.getcwd(), INTERMEDIATE_FOLDER_NAME, EBX_FOLDER_NAME, map_name)
	if not os.path.exists(ebx_out_path):
		os.makedirs(ebx_out_path)

	with open(os.path.join(ebx_out_path, gamemode_name + '.json'), "w") as f:
		json.dump(ebx, f, indent=2)


def save_override_partitions(overrides: dict, map_name: str, gamemode_name: str):
	"""Write each overridden instance's blueprint next to the level partition.

	bundles.py adds EVERY file in the map's intermediate folder to the bundle, so writing them
	here is all that is needed to get them compiled in.
	"""
	if not overrides:
		return

	# Into a "<gamemode>.d" sidecar folder, NOT next to the gamemode partition. bundles.py builds
	# one bundle per FILE, and the level is patched with a SubWorldReferenceObjectData naming a
	# single bundle — so a partition in its own bundle is never loaded, and an object pointing at
	# it silently disappears (its vanilla original is excluded, and the replacement never resolves).
	# The sidecar tells bundles.py to put these in the SAME bundle as the level partition.
	ebx_out_path = os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME, EBX_FOLDER_NAME,
								map_name, gamemode_name + '.d')

	if not os.path.exists(ebx_out_path):
		os.makedirs(ebx_out_path)

	for object_guid, (_, _, partition) in overrides.items():
		with open(os.path.join(ebx_out_path, object_guid + '.json'), 'w') as f:
			json.dump(partition, f, indent=2)


def save_lua_vanilla_modifications(vanillaRODs: dict, map_name: str, gamemode_name: str, out_dir: str):
	# Save list of modified vanilla RODs in Lua tables
	vanillaRODsJSON = json.dumps(vanillaRODs, indent=1)
	vanillaRODsJSON = 'return [[\n' + vanillaRODsJSON + '\n]]'

	out_file_name = map_name + '_' + gamemode_name
	lua_out_path = os.path.join(out_dir, LUA_LEVELS_PATH, map_name)
	if not os.path.exists(lua_out_path):
		os.makedirs(lua_out_path)

	with open(os.path.join(lua_out_path, out_file_name + '.lua'), "w") as f:
		f.write(vanillaRODsJSON)
	f.close()


##############################################


def generate_ebx_json(in_dir: str, out_dir: str):
	with open(os.path.join(os.path.dirname(__file__), 'VariationMap.json'), 'r') as f:
		variation_map = json.load(f)

	map_saves_path = os.path.join(in_dir, MAP_SAVES_FOLDER_NAME)

	# Load gamemode maps (for supporting custom gamemode names)
	gamemode_map_path = os.path.join(in_dir, 'gamemode_map.json')
	gamemode_map = None
	if os.path.exists(gamemode_map_path):
		with open(gamemode_map_path, 'r') as f:
			gamemode_map = json.load(f)

	bundles_lua_map = {}

	# Remove intermediate folder
	if os.path.exists(os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME)):
		shutil.rmtree(os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME))

	for filename in os.listdir(map_saves_path):
		file_path = os.path.join(map_saves_path, filename)

		if not os.path.isfile(file_path):
			continue

		extension = os.path.splitext(filename)[1]

		if extension != '.json':
			continue

		with open(file_path, 'r') as f:
			json_save = json.load(f)

		print('Processing file ' + filename)

		# Save the gamemodes that this bundle will be loaded in a new
		# lua map: key -> map+gamemode loaded, value -> bundle to load
		# Basically it inverts the provided gamemode map
		if gamemode_map:
			bundle_path = json_save['header']['mapName'] + '/' + json_save['header']['gameModeName']
			if bundle_path in gamemode_map:
				for x in gamemode_map[bundle_path]:
					bundles_lua_map[x] = bundle_path

		bundle_name = BUNDLE_PREFIX + "/" + json_save['header']['mapName'] + '/' + json_save['header']['gameModeName']
		partition_name = bundle_name.lower()
		world_part_data_name = BUNDLE_PREFIX + "/" + json_save['header']['mapName'] + '/' + 'Main'

		overrides = build_override_partitions(json_save, json_save['header']['mapName'])

		if overrides:
			print('Baking %d per-instance EBX override(s)' % len(overrides))

		ebx, vanilla_rods = process_save_file(json_save, world_part_data_name, variation_map, overrides)

		ebx['Name'] = partition_name
		swd = ebx['Instances'][ebx['PrimaryInstanceGuid']]
		swd['Name'] = bundle_name

		# Save EBX in JSON files
		save_ebx_json(ebx, json_save['header']['mapName'], json_save['header']['gameModeName'])
		save_override_partitions(overrides, json_save['header']['mapName'], json_save['header']['gameModeName'])

		save_lua_vanilla_modifications(
			vanilla_rods, json_save['header']['mapName'], json_save['header']['gameModeName'], out_dir)

	save_bundles_lua_map(bundles_lua_map, out_dir)
