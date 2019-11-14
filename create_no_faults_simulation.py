#! /usr/bin/env python

import os
import sys
import json
import shutil
import fileinput
import random
import argparse

parser = argparse.ArgumentParser(description='Converts a ucerf3 model on faults to a no-faults model')
required = parser.add_argument_group('required')
optional = parser.add_argument_group('optional')
# required args
required.add_argument('--sim_dir', help='Directory for the previously configured u3etas simulation', required=True)
required.add_argument('--nofaults_dir', help='Absolute path for the new no-fault simulation', required=True)
# optional args
optional.add_argument('--nodes', type=int, default=None, help='Number of nodes to use for the simulation')
optional.add_argument('--run_time', default=None, help='Run-time for the simulation, defaults to original run-time')
optional.add_argument('--queue', default=None, help='set queue for new simulation, defaults to original queue')
args = parser.parse_args()

# some filenes
config_basename = 'config.json'
slurm_basename = 'etas_sim_mpj.slurm'
ucerf3jar_basename = 'opensha-ucerf3-all.jar'
config_plots_dirname = 'config_input_plots'
slurm_plot_basename = 'plot_results.slurm'
simdir_exp = os.path.expandvars(args.sim_dir)
nofaultsdir_exp = os.path.expandvars(args.nofaults_dir)

# create no-faults directory
try:
    os.mkdir(args.nofaults_dir)
except FileExistsError:
    print("Folder already exist. Exiting program to not overwrite existing directory.")
    sys.exit(1)

# copy necessary files
if os.path.exists(os.path.join(args.sim_dir, slurm_plot_basename)):
    handle_plot_slurm = True
else:
    handle_plot_slurm = False

try:
    shutil.copy(os.path.join(simdir_exp, ucerf3jar_basename), os.path.join(nofaultsdir_exp, ucerf3jar_basename))
except FileNotFoundError:
    print('Unable to find jar file defaulting to jar on path')

shutil.copy(os.path.join(simdir_exp, slurm_basename),  os.path.join(nofaultsdir_exp, slurm_basename))
shutil.copytree(os.path.join(simdir_exp, config_plots_dirname), os.path.join(nofaultsdir_exp, config_plots_dirname))
if handle_plot_slurm:
    shutil.copy(os.path.join(simdir_exp, slurm_plot_basename), os.path.join(nofaultsdir_exp, slurm_plot_basename))

# update and rewrite the config.json
with open(os.path.join(args.sim_dir, config_basename), 'r') as f:
    config = json.load(f)
# following converts u3etas to no faults
config['simulationName'] = config['simulationName'] + ', No Faults'
config['outputDir'] = args.nofaults_dir
config['probModel'] = 'POISSON'
config['totRateScaleFactor'] = 1.0
config['randomSeed'] = random.getrandbits(64)
config['griddedOnly'] = True
# write to new dir
with open(os.path.join(args.nofaults_dir, 'config.json'), 'w') as f:
    json.dump(config, f, indent=2)

# edits simulation slurm file inplace, so need to copy before
for line in fileinput.input(os.path.join(nofaultsdir_exp, slurm_basename), inplace=True):
    if line.startswith('ETAS_CONF_JSON'):
        print(f'ETAS_CONF_JSON={os.path.join(args.nofaults_dir,config_basename)}')
    elif line.startswith("#SBATCH -N") and args.nodes:
        print(f'#SBATCH -N {args.nodes}')
    elif line.startswith("#SBATCH -t") and args.run_time:
        print(f'#SBATCH -t {args.run_time}')
    elif line.startswith("#SBATCH -p") and args.queue:
        print(f'#SBATCH -p {args.queue}')
    else:
        print(line, end="")

# edits the plotting slurm file if it exists, need to copy before
if handle_plot_slurm:
    for line in fileinput.input(os.path.join(nofaultsdir_exp, slurm_plot_basename), inplace=True):
        if line.startswith('ETAS_CONF_JSON'):
            print(f'ETAS_CONF_JSON={os.path.join(args.nofaults_dir,config_basename)}')
        elif line.startswith("#SBATCH -p") and args.queue:
            print(f'#SBATCH -p {args.queue}')
        else:
            print(line, end="")

