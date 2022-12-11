import json
import os
import subprocess

WIN32_PREFIX = 'Win32'
BUNDLE_PREFIX = 'CustomLevels'
FROSTBITE_VER = 'Frostbite2_0'
INTERMEDIATE_FOLDER_NAME = 'intermediate'
EBX_JSON_FOLDER_NAME = 'ebx_json'
SB_OUTPUT_FOLDER_NAME = 'sb'

def generate_bundles(rime_path: str, out_dir: str):
	inputPath = os.path.join(
		os.getcwd(), INTERMEDIATE_FOLDER_NAME, EBX_JSON_FOLDER_NAME)
	outputPath = os.path.join(out_dir, SB_OUTPUT_FOLDER_NAME)

	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	commands = []

	superBundleNames = []
	print('Superbundles:')

	commandsPath = os.path.join(os.getcwd(), 'commands.txt')

	for mapName in os.listdir(inputPath):
		# build superbundle
		sbName = WIN32_PREFIX + '/' + BUNDLE_PREFIX + '/' + mapName + '/' + mapName
		commands.append('build_sb ' + sbName + ' ' +
						FROSTBITE_VER + ' \"' + outputPath + '\"\n')

		for file in os.listdir(os.path.join(inputPath, mapName)):
			fileName = os.path.splitext(file)[0]  # Remove extension
			filePath = os.path.join(inputPath, mapName, file)

			if not os.path.isfile(filePath):
				continue

			# build bundle
			bundleNameW32 = WIN32_PREFIX + '/' + \
							BUNDLE_PREFIX + '/' + mapName + '/' + fileName
			commands.append('build_bundle ' + bundleNameW32 + '\n')

			partitionName = BUNDLE_PREFIX + '/' + mapName + '/' + fileName

			# add partition to bundle and build bundle
			commands.append('add_json_partition ' +
							partitionName.lower() + ' \"' + filePath + '\"\n')
			commands.append('build\n')

		# build superbundle
		commands.append('build\n\n')
		superBundleNames.append(sbName)
		print(sbName)

	# save commands in commands.txt
	with open(commandsPath, "w") as f:
		f.writelines(commands)

	print('Attempting to compile with Rime...')

	commands_path = os.path.join(os.getcwd(), 'commands.txt')

	# execute commands with rime
	subprocess.run([os.path.join(rime_path, 'RimeREPL.exe'), commands_path], cwd=rime_path)

	return superBundleNames
