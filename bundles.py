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
	input_path = os.path.join(
		os.getcwd(), INTERMEDIATE_FOLDER_NAME, EBX_JSON_FOLDER_NAME)
	output_path = os.path.join(out_dir, SB_OUTPUT_FOLDER_NAME)

	if not os.path.exists(output_path):
		os.makedirs(output_path)
	commands = []

	super_bundle_names = []
	print('Superbundles:')

	commands_path = os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME, 'commands.txt')

	for mapName in os.listdir(input_path):
		# build superbundle
		sb_name = WIN32_PREFIX + '/' + BUNDLE_PREFIX + '/' + mapName + '/' + mapName
		commands.append('build_sb ' + sb_name + ' ' +
						FROSTBITE_VER + ' \"' + output_path + '\"\n')

		for file in os.listdir(os.path.join(input_path, mapName)):
			file_name = os.path.splitext(file)[0]  # Remove extension
			file_path = os.path.join(input_path, mapName, file)

			if not os.path.isfile(file_path):
				continue

			# build bundle
			bundle_name_w32 = WIN32_PREFIX + '/' + BUNDLE_PREFIX + '/' + mapName + '/' + file_name
			commands.append('build_bundle ' + bundle_name_w32 + '\n')

			partition_name = BUNDLE_PREFIX + '/' + mapName + '/' + file_name

			# add partition to bundle and build bundle
			commands.append('add_json_partition ' + partition_name.lower() + ' \"' + file_path + '\"\n')
			commands.append('build\n')

		# build superbundle
		commands.append('build\n\n')
		super_bundle_names.append(sb_name)
		print(sb_name)

	# save commands in commands.txt
	with open(commands_path, "w") as f:
		f.writelines(commands)

	print('Attempting to compile with Rime...')

	commands_path = os.path.join(os.getcwd(), 'commands.txt')

	# execute commands with rime
	subprocess.run([os.path.join(rime_path, 'RimeREPL.exe'), commands_path], cwd=rime_path)

	return super_bundle_names
