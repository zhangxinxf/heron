#!/usr/bin/python2.7

import argparse
import atexit
import base64
import contextlib
import glob
import logging
import logging.handlers
import os
import shutil
import sys
import subprocess
import tarfile
import tempfile

import heron.cli.src.python.args as args
import heron.cli.src.python.execute as execute
import heron.cli.src.python.jars as jars
import heron.cli.src.python.utils as utils

def create_parser(subparsers):
  parser = subparsers.add_parser(
      'activate',
      help='Activate a topology',
      usage = "%(prog)s [options] cluster/[role]/[environ] topology-name",
      add_help = False)

  args.add_titles(parser)
  args.add_cluster_role_env(parser)
  args.add_topology(parser)

  args.add_config(parser)
  args.add_verbose(parser)

  parser.set_defaults(subcommand='activate')
  return parser

def run(command, parser, cl_args, unknown_args):

  try:
    # check if the required arguments are provided
    cluster_role_env = cl_args['cluster/[role]/[env]']
    topology_name = cl_args['topology-name']

    # extract the config path
    config_path = cl_args['config_path']

  except KeyError:
    subparser = utils.get_subparser(parser, command)
    print(subparser.format_help())
    parser.exit()

  # check if the config path exists
  config_path = utils.get_heron_cluster_conf_dir(cluster_role_env, config_path);
  if not os.path.isdir(config_path):
    print("Config directory does not exist: %s" % config_path);
    parser.exit();

  try:
    cluster_role_env = utils.parse_cluster_role_env(cluster_role_env)
    config_overrides = utils.parse_cmdline_override(cl_args)

    new_args = [
        "--cluster", cluster_role_env[0],
        "--role", cluster_role_env[1],
        "--environment", cluster_role_env[2],
        "--heron_home", utils.get_heron_dir(),
        "--config_path", config_path,
        "--config_overrides", base64.b64encode(config_overrides),
        "--topology_name", topology_name,
        "--command", command,
    ]

    lib_jars = utils.get_heron_libs(jars.scheduler_jars() + jars.statemgr_jars())

    # invoke the runtime manager to kill the topology
    execute.heron_class(
        'com.twitter.heron.scheduler.RuntimeManagerMain',
        lib_jars,
        extra_jars=[],
        args= new_args
    )

  except Exception as ex:
    print 'Error: %s' % str(ex)
    print 'Failed to activate topology \'%s\'' % topology_name
    sys.exit(1)

  print 'Successfully activated topology \'%s\'' % topology_name
  sys.exit(0)