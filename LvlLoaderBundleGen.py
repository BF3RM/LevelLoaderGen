import uuid
import json
import os
import copy
import shutil

from templates import subWorldDataTemp, objectBlueprintTemp, referenceObjectDataTemp, effectReferenceObjectDataTemp

BUNDLE_PREFIX = 'CustomLevels'
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

##############################################

with open(os.path.join(os.getcwd(), 'VariationMap.json'), 'r') as f:
	variationMap = json.loads(f.read())
f.close()

inPath = os.path.join(os.getcwd(), 'in')

# Remove out/ folder
if os.path.exists(os.path.join(os.getcwd(), EXPORT_FOLDER_NAME)):
	shutil.rmtree(os.path.join(os.getcwd(), EXPORT_FOLDER_NAME))

for filename in os.listdir(inPath):
	filePath = os.path.join(inPath, filename)
	
	if not os.path.isfile(filePath):
		continue

	extension = os.path.splitext(filename)[1]

	if extension != '.json':
		continue

	with open(filePath, 'r') as f:
		jsonSave = json.loads(f.read())
	f.close()

	print('Processing file ' + filename)

	bundleName = BUNDLE_PREFIX + "/" + jsonSave['header']['mapName'] + '/' + jsonSave['header']['gameModeName']
	partitionName = bundleName.lower()
	worldPartDataName = BUNDLE_PREFIX + "/" + jsonSave['header']['mapName'] + '/' + 'Main'
	
	ebx, vanillaRODs = ProcessSaveFile(jsonSave, worldPartDataName)

	ebx['Name'] = partitionName
	swd = ebx['Instances'][ebx['PrimaryInstanceGuid']]
	swd['Name'] = bundleName

	ebxJSON = json.dumps(ebx, indent = 2)


	# Save EBX in JSON files
	ebxOutPath = os.path.join(os.getcwd(), EXPORT_FOLDER_NAME, EBX_FOLDER_NAME, jsonSave['header']['mapName'])
	if not os.path.exists(ebxOutPath):
		os.makedirs(ebxOutPath)

	outFileName = jsonSave['header']['mapName'] + '_' + jsonSave['header']['gameModeName']
	with open(os.path.join(ebxOutPath, jsonSave['header']['gameModeName'] + '.json'), "w") as f:
		f.write(ebxJSON)
	f.close()

	# Save list of modified vanilla RODs in Lua tables
	vanillaRODsJSON = json.dumps(vanillaRODs, indent = 1)
	vanillaRODsJSON = 'return [[\n' + vanillaRODsJSON + '\n]]'

	luaOutPath = os.path.join(os.getcwd(), EXPORT_FOLDER_NAME, LUA_FOLDER_NAME, jsonSave['header']['mapName'])
	if not os.path.exists(luaOutPath):
		os.makedirs(luaOutPath)

	with open(os.path.join(luaOutPath, outFileName + '.lua'), "w") as f:
		f.write(vanillaRODsJSON)
	f.close()