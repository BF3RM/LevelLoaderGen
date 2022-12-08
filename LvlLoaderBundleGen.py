import uuid
import json
import os
import copy
import shutil

from templates import subWorldDataTemp, objectBlueprintTemp, referenceObjectDataTemp, effectReferenceObjectDataTemp

BUNDLE_PREFIX = 'CustomLevels'
INTERMEDIATE_FOLDER_NAME = 'intermediate'
INPORT_FOLDER_NAME = 'in'
MAP_SAVES_FOLDER_NAME = 'map_saves'
EXPORT_FOLDER_NAME = 'out'
EBX_FOLDER_NAME = 'ebx_json'
LUA_FOLDER_NAME = 'lua'

def CreateInitialPartitionStruct(name):
	ebx = copy.deepcopy(subWorldDataTemp)
	partitionGuid = str(uuid.uuid4())
	ebx['PartitionGuid'] = partitionGuid

	## TODO: guids should not be random maybe
	subWorldDataGuid = str(uuid.uuid4())
	descriptorGuid = str(uuid.uuid4())
	registryGuid = str(uuid.uuid4())
	worldPartDataGuid = str(uuid.uuid4())
	worldPartRODGuid = str(uuid.uuid4())
	ebx['PrimaryInstanceGuid'] = subWorldDataGuid

	# recreate the dict with the generated guids as keys
	newDict = {}
	newDict[subWorldDataGuid] = ebx['Instances']['SubWorldDataGuid']
	newDict[descriptorGuid] = ebx['Instances']['DescriptorGuid']
	newDict[registryGuid] = ebx['Instances']['RegistryGuid']
	newDict[worldPartDataGuid] = ebx['Instances']['WorldPartDataGuid']
	newDict[worldPartRODGuid] = ebx['Instances']['WorldPartRODGuid']

	newDict[subWorldDataGuid]['Descriptor']['InstanceGuid'] = descriptorGuid
	newDict[subWorldDataGuid]['Descriptor']['PartitionGuid'] = partitionGuid
	newDict[subWorldDataGuid]['RegistryContainer']['InstanceGuid'] = registryGuid
	newDict[subWorldDataGuid]['RegistryContainer']['PartitionGuid'] = partitionGuid

	newDict[registryGuid]['BlueprintRegistry'][0]['PartitionGuid'] = partitionGuid
	newDict[registryGuid]['BlueprintRegistry'][0]['InstanceGuid'] = subWorldDataGuid
	newDict[registryGuid]['BlueprintRegistry'][1]['PartitionGuid'] = partitionGuid
	newDict[registryGuid]['BlueprintRegistry'][1]['InstanceGuid'] = worldPartDataGuid

	newDict[worldPartRODGuid]['Blueprint']['PartitionGuid'] = partitionGuid
	newDict[worldPartRODGuid]['Blueprint']['InstanceGuid'] = worldPartDataGuid

	newDict[subWorldDataGuid]['Objects'][0]['PartitionGuid'] = partitionGuid
	newDict[subWorldDataGuid]['Objects'][0]['InstanceGuid'] = worldPartRODGuid
	newDict[registryGuid]['ReferenceObjectRegistry'][0]['PartitionGuid'] = partitionGuid
	newDict[registryGuid]['ReferenceObjectRegistry'][0]['InstanceGuid'] = worldPartRODGuid

	newDict[worldPartDataGuid]['Name'] = name

	ebx['Instances'] = newDict
	return ebx


def ProcessSaveFile(jsonSave, worldPartDataName):
	vanillaRODs = {}
	# Create structure
	ebx = CreateInitialPartitionStruct(worldPartDataName)

	# clean up
	swd = ebx['Instances'][ebx['PrimaryInstanceGuid']]
	rc = ebx['Instances'][swd['RegistryContainer']['InstanceGuid']]
	wprod = ebx['Instances'][swd['Objects'][0]['InstanceGuid']]
	wpd = ebx['Instances'][wprod['Blueprint']['InstanceGuid']]


	for i, obj in enumerate(jsonSave['data']):
		# if obj['origin'] != 2:
		# 	continue
		if obj['origin'] == 3: # custom children not supported
			continue

		if obj['origin'] == 1: # vanilla
			# add to table
			rod = obj['originalRef']

			if rod['partitionGuid'] in vanillaRODs:
				vanillaRODs[rod['partitionGuid']].append(rod['instanceGuid'])
			else:
				vanillaRODs[rod['partitionGuid']] = [rod['instanceGuid']]

			if 'isDeleted' in obj:
				continue

		referenceObjectDataGuid = obj['guid'].lower()
		
		referenceObjectData = None
		
		# Use effectROD if it's an effect
		if obj['blueprintCtrRef']['typeName'] == 'EffectBlueprint':
			referenceObjectData = copy.deepcopy(effectReferenceObjectDataTemp)
		else:
			referenceObjectData = copy.deepcopy(referenceObjectDataTemp)

		referenceObjectData['Blueprint']['InstanceGuid'] = obj['blueprintCtrRef']['instanceGuid']
		referenceObjectData['Blueprint']['PartitionGuid'] = obj['blueprintCtrRef']['partitionGuid']
		referenceObjectData['IndexInBlueprint'] = len(wpd['Objects']) + 30001
		referenceObjectData['IsEventConnectionTarget'] = 3 # Realm.Realm_None
		referenceObjectData['IsPropertyConnectionTarget'] = 3 # Realm.Realm_None
		referenceObjectData['CastSunShadowEnable'] = True
		referenceObjectData['Excluded'] = False
		
		# handle variation
		variation = None

		if 'variation' in obj:
			variation = variationMap.get(str(obj['variation']))
		
		if variation != None:
			referenceObjectData['ObjectVariation'] = {
				'PartitionGuid': variation[0],
				'InstanceGuid': variation[1]
				}

		# Handle transform
		if 'localTransform' in obj:
			referenceObjectData['BlueprintTransform'] = obj['localTransform']
		else:
			referenceObjectData['BlueprintTransform'] = obj['transform']

		# Fix left/right difference
		referenceObjectData['BlueprintTransform']['right'] = referenceObjectData['BlueprintTransform']['left']
		referenceObjectData['BlueprintTransform'].pop('left')

		ref = {
			'PartitionGuid': ebx['PartitionGuid'],
			'InstanceGuid': referenceObjectDataGuid
			}

		# Add to dictionary in root, add reference in worlpartdata.objects and registrycontainer.referenceobjectregistry
		ebx['Instances'][referenceObjectDataGuid] = referenceObjectData
		rc['ReferenceObjectRegistry'].append(ref)
		wpd['Objects'].append(ref)

	return ebx, vanillaRODs

# Outputs a lua file with the gamemode maps, allowing LevelLoader to work with custom bundles and use the same bundle for
# multiple gamemodes. Supports custom gamemodes too
def SaveBundlesLuaMap(bundlesLuaMap):
	if bundlesLuaMap:
		luaOutPath = os.path.join(os.getcwd(), EXPORT_FOLDER_NAME, LUA_FOLDER_NAME)
		if not os.path.exists(luaOutPath):
			os.makedirs(luaOutPath)

		bundlesLuaMapJSON = json.dumps(bundlesLuaMap, indent = 1)
		bundlesLuaMapJSON = 'return [[\n' + bundlesLuaMapJSON + '\n]]'

		with open(os.path.join(luaOutPath, 'BundlesMap.lua'), "w") as f:
			f.write(bundlesLuaMapJSON)
		f.close()

# Save EBX in JSON files to be later compiled by Rime
def SaveEBXAsJSON(ebx, mapName, gamemodeName):
	ebxJSON = json.dumps(ebx, indent = 2)

	ebxOutPath = os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME, EBX_FOLDER_NAME, mapName)
	if not os.path.exists(ebxOutPath):
		os.makedirs(ebxOutPath)

	with open(os.path.join(ebxOutPath, gamemodeName + '.json'), "w") as f:
		f.write(ebxJSON)
	f.close()

def SaveLuaVanillaModifications(vanillaRODs, mapName, gamemodeName):
	# Save list of modified vanilla RODs in Lua tables
	vanillaRODsJSON = json.dumps(vanillaRODs, indent = 1)
	vanillaRODsJSON = 'return [[\n' + vanillaRODsJSON + '\n]]'

	outFileName = mapName + '_' + gamemodeName
	luaOutPath = os.path.join(os.getcwd(), EXPORT_FOLDER_NAME, LUA_FOLDER_NAME, mapName)
	if not os.path.exists(luaOutPath):
		os.makedirs(luaOutPath)

	with open(os.path.join(luaOutPath, outFileName + '.lua'), "w") as f:
		f.write(vanillaRODsJSON)
	f.close()

##############################################

with open(os.path.join(os.getcwd(), 'VariationMap.json'), 'r') as f:
	variationMap = json.loads(f.read())
f.close()

inPath = os.path.join(os.getcwd(), INPORT_FOLDER_NAME)
mapSavesPath = os.path.join(inPath, MAP_SAVES_FOLDER_NAME)

# Load gamemode maps (for supporting custom gamemode names)
gamemodeMapPath = os.path.join(inPath, 'gamemode_map.json')
gamemodeMap = None
if (os.path.exists(gamemodeMapPath)):
	with open(gamemodeMapPath, 'r') as f:
		gamemodeMap = json.loads(f.read())
	f.close()
bundlesLuaMap = {}

# Remove out and intermediate folder
if os.path.exists(os.path.join(os.getcwd(), EXPORT_FOLDER_NAME)):
	shutil.rmtree(os.path.join(os.getcwd(), EXPORT_FOLDER_NAME))
if os.path.exists(os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME)):
	shutil.rmtree(os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME))

for filename in os.listdir(mapSavesPath):
	filePath = os.path.join(mapSavesPath, filename)
	
	if not os.path.isfile(filePath):
		continue

	extension = os.path.splitext(filename)[1]

	if extension != '.json':
		continue

	with open(filePath, 'r') as f:
		jsonSave = json.loads(f.read())
	f.close()

	print('Processing file ' + filename)

	# Save the gamemodes that this bundle will be loaded in a new
	# lua map: key -> map+gamemode loaded, value -> bundle to load
	# Basically it inverts the provided gamemode map
	if gamemodeMap:
		bundlePath = jsonSave['header']['mapName'] + '/' + jsonSave['header']['gameModeName']
		if bundlePath in gamemodeMap:
			for x in gamemodeMap[bundlePath]:
				bundlesLuaMap[x] = bundlePath
	
	bundleName = BUNDLE_PREFIX + "/" + jsonSave['header']['mapName'] + '/' + jsonSave['header']['gameModeName']
	partitionName = bundleName.lower()
	worldPartDataName = BUNDLE_PREFIX + "/" + jsonSave['header']['mapName'] + '/' + 'Main'
	
	ebx, vanillaRODs = ProcessSaveFile(jsonSave, worldPartDataName)

	ebx['Name'] = partitionName
	swd = ebx['Instances'][ebx['PrimaryInstanceGuid']]
	swd['Name'] = bundleName

	# Save EBX in JSON files
	SaveEBXAsJSON(ebx, jsonSave['header']['mapName'], jsonSave['header']['gameModeName'])

	SaveLuaVanillaModifications(vanillaRODs, jsonSave['header']['mapName'], jsonSave['header']['gameModeName'])

SaveBundlesLuaMap(bundlesLuaMap)