import argparse
import os

import exb_json
import bundles
import mod_generator
import rime_downloader

if __name__ == "__main__":
	try:
		# set it up
		parser = argparse.ArgumentParser(
			description='[--rimepath] RimeREPL.exe path')
		parser.add_argument("name", type=str, help="Name of the generated level loader mod, eg. rm-levelloader")
		parser.add_argument("version", type=str, help="Version of the generated level loader mod, eg. 1.0.0")
		parser.add_argument("-i", "--input", type=str, help="Path that contains the input files")
		parser.add_argument("-o", "--output", type=str, help="Path where the generated mod should be placed")
		parser.add_argument("--rimepath", type=str,
							help="Path to RimeREPL. By default it will download RimeREPL for you")

		# get it
		args = parser.parse_args()
		rime_path = args.rimepath

		mod_name = args.name
		mod_version = args.version
		in_dir = args.input
		out_dir = args.output

		if in_dir is None:
			in_dir = os.path.join(os.getcwd(), 'in')

		if out_dir is None:
			out_dir = os.path.join(os.getcwd(), 'mods', args.name)
		else:
			out_dir = os.path.join(out_dir, args.name)

		if rime_path is None:
			rime_path = rime_downloader.get_path()
			if not rime_downloader.is_downloaded():
				rime_downloader.download()

		print("Generating mod {} of version {} in {}".format(mod_name, mod_version, out_dir))

		exb_json.generate_ebx_json(in_dir, out_dir)
		superbundle_names = bundles.generate_bundles(rime_path, out_dir)
		mod_generator.generate_mod(mod_name, mod_version, superbundle_names, out_dir)

		print("You can find your generated mod here {}".format(out_dir))
	except KeyboardInterrupt:
		print('User has exited the program')
