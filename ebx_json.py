import uuid
import json
import os
import copy
import shutil

from templates import subWorldDataTemp, objectBlueprintTemp, referenceObjectDataTemp, effectReferenceObjectDataTemp

BUNDLE_PREFIX = 'CustomLevels'
INTERMEDIATE_FOLDER_NAME = 'intermediate'
MAP_SAVES_FOLDER_NAME = 'map_saves'
EBX_FOLDER_NAME = 'ebx_json'
LUA_LEVELS_PATH = os.path.join('ext', 'Shared', 'Levels')


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


def process_save_file(json_save: dict, world_part_data_name: str, variation_map: dict):
	vanilla_rods = {}
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

		if obj['origin'] == 1:  # vanilla
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

		ebx, vanilla_rods = process_save_file(json_save, world_part_data_name, variation_map)

		ebx['Name'] = partition_name
		swd = ebx['Instances'][ebx['PrimaryInstanceGuid']]
		swd['Name'] = bundle_name

		# Save EBX in JSON files
		save_ebx_json(ebx, json_save['header']['mapName'], json_save['header']['gameModeName'])

		save_lua_vanilla_modifications(
			vanilla_rods, json_save['header']['mapName'], json_save['header']['gameModeName'], out_dir)

	save_bundles_lua_map(bundles_lua_map, out_dir)
