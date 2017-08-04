from __future__ import print_function
from invoke import task, run
import os
import sys
import site
print(sys.executable)
print(site.getsitepackages())
import yaml
import shutil
import pdb

env_name = 'jupyterlab-demo'
demofolder = 'demofiles'

@task
def environment(ctx, clean=False, env_name=env_name):
	'''
	Creates environment for demo
	Args:
	clean: deletes environment prior to reinstallation
	env_name: name of environment to install
	'''
	if clean:
		print('deleting environment')
		ctx.run('source deactivate; conda remove -n {0!s} --all'.format(env_name))
	# Create a new environment
	print('creating environment {0!s}'.format(env_name))
	ctx.run("""
	    conda env create -f environment.yml -n {0!s};
		source activate {0!s};
		ipython kernel install --name {0!s} --display-name {0!s} --sys-prefix;
		jupyter labextension install @jupyterlab/google-drive@0.4.0 --no-build;
		jupyter labextension install @jupyterlab/geojson-extension@0.8.0 --no-build;
		jupyter labextension install @jupyterlab/json-extension@0.8.0 --no-build;
		jupyter labextension install @jupyter-widgets/jupyterlab-manager@0.24.1 --no-build;
		jupyter labextension install bqplot-jupyterlab@0.4.0 --no-build;
		jupyter lab clean && jupyter lab build;
		""".format(env_name), pty=True)

@task
def demofiles(ctx, clean=False, demofolder=demofolder):
	'''
	Clones demofiles into demofolder
	Args:
	clean: deletes demofiles from demofolder prior to installation
	demofolder: name of demofolder
	'''
	print('cleaning demofiles')
	if clean:
		shutil.rmtree(demofolder)
	print('creating demofolder')
	os.makedirs(demofolder)
	old_pwd = os.getcwd()
	os.chdir(demofolder)
	#list of repos used in demo
	print('cloning repos into demo folder {}'.format(demofolder))
	reponames = [
		'jakevdp/PythonDataScienceHandbook',
		'swissnexSF/Urban-Data-Challenge',
		'altair-viz/altair',
		'QuantEcon/QuantEcon.notebooks',
		'theandygross/TCGA',
		'aymericdamien/TensorFlow-Examples'
	]
	for repo in reponames:
		ctx.run('git clone https://github.com/{}.git'.format(repo))
		assert os.path.isdir(repo.split('/')[1]), '{} failed download'.format(repo)
	#This empty file and empty folder are for showing drag and drop in jupyterlab
	ctx.run('touch move_this_file.txt; mkdir move_it_here')

@task
def clean(ctx, env_name=env_name, demofolder=demofolder):
	'''
	Deletes both environment and demofolder
	Args:
	env_name: name of conda environment
	demofolder: path to folder with demofiles
	'''
	ctx.run('source deactivate;\
		conda remove --name {0!s} --all').format(env_name)
	shutil.rmtree(demofolder)
	with open("talks.yml", 'r') as stream:
		talks = yaml.load(stream)
	for t in talks:
		if os.path.exists(t):
			shutil.rmtree(t)

@task
def talk(ctx, talk_name, clean=False):
	'''
	Reads yaml file talks.yml and
	moves files and folders specified
	in yaml file to the a folder
	matching the name of the talk

	Args:
	talk_name: name of talk in talks.yml

	Note: yaml file is assumed to be
	a dict of dicts of lists and
  dict with the following python format:

	{talk_name:
		{'folders':
			['folder0', folder1']
		'files':
			['file0', file1']
     'rename':
      {'oldname': 'newname'}
		}
	}

	or in yaml format:

	talk_name:
		folders:
			- folder0
			- folder1
		files:
			- file0
			- file1
    rename:
      oldname: newname
	'''
	with open("talks.yml", 'r') as stream:
		talks = yaml.load(stream)
	if clean:
		shutil.rmtree(talk_name)
	if not os.path.exists(talk_name):
		os.makedirs(talk_name)
	for copy_type in ['folders', 'files']:
		if copy_type in talks[talk_name]:
			for f in talks[talk_name][copy_type]:
				copied_path = os.path.join(talk_name, os.path.basename(f))
				if copy_type == 'folders':
					if not os.path.exists(copied_path):
						shutil.copytree(f, copied_path)
					assert os.path.exists(copied_path),\
					'{} failed to copy into {}'.format(f, talk_name)
				elif copy_type == 'files':
					shutil.copy(f, copied_path)
					assert os.path.isfile(copied_path),\
					'{} failed to copy into {}'.format(f, talk_name)
	if 'rename' in talks[talk_name]:
		for old_file, new_file in talks[talk_name]['rename'].items():
			moved_file = os.path.join(talk_name, os.path.basename(old_file))
			if os.path.isfile(moved_file):
				os.rename(moved_file, os.path.join(talk_name, new_file))
			elif os.path.isfile(old_file):
				shutil.copy(old_file, os.path.join(talk_name, new_file))
