#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paramiko
import os
import transmissionrpc
import getpass
import sys
import traceback
from termcolor import colored
from stat import *

user = "xbian"
host = "zurawina.local"

ssh_username = user
ssh_server = host
ssh_port = 22

transmission_user = user
transmission_host = host
transmission_port = 9091
transmission_timeout = 180

download_dir="downloads"

class SCP_Client:
  scp = ''
  ssh = ''

  def __init__(self):
    self.ssh = paramiko.SSHClient()
    self.ssh.load_system_host_keys()
    try:
      self.ssh.connect(ssh_server, username=ssh_username, look_for_keys=True, port=ssh_port);
      self.scp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
    except socket.error:
      print "Error al conectar con %@" % ssh_server

  def prepare_dir(self, path):
    os.mkdir(path)
    os.chdir(path)

  def get_recursive(self, path, extra_path=" "):
    self.scp.chdir(path)
    for file in self.scp.listdir("."):
      print extra_path+"/"+file
      file_stat = self.scp.lstat(file)
      if S_ISDIR(file_stat.st_mode):
        os.mkdir(file) 
        os.chdir(file)
        self.get_recursive(file, extra_path+"/"+file)
        self.scp.chdir("..")
        os.chdir("..")
      else:
        self.scp.get(file, file)

  def get_resource(self, resource):
    resource_stat = self.scp.lstat(download_dir+"/"+resource) 
    resource=resource.replace(" ", "\\ ").replace("[", "\\[").replace("]", "\\]")
    if S_ISDIR(resource_stat.st_mode):
      return self.get_directory(resource)
    else:
      return self.get_file(resource)

  def get_directory(self, path):
    self.prepare_dir(path)
    scp_copy="scp -r \"%s@%s:~/%s/%s/*\" ." % (ssh_username, ssh_server, download_dir, path)
    status = os.system(scp_copy)
    os.chdir("..")
    return status

  def get_file(self, file):
    scp_copy="scp \"%s@%s:~/%s/%s\" ." % (ssh_username, ssh_server, download_dir, file)
    return os.system(scp_copy)

  def close(self):
    self.scp.close()
    self.ssh.close()
  

class Transmission_Client():
  connected = colored("Connected", 'green', attrs=['dark'])
  error = colored("FAIL", 'red', attrs=['dark'])
  thinking = colored("...", 'white', attrs=['dark'])
  copy = colored("Downloaded and ready to copy", 'cyan', attrs=['dark'])
  delete = colored("Copied and deleted", 'green', attrs=['dark'])

  transmission_password = ""
  transmission = ""

  def __init__(self):
    self.transmission_password = getpass.getpass("Enter your password [%s@%s:%s]:" % (transmission_user, transmission_host, transmission_port))

  def print_info(self, msg, status):
      print "%-100s [%s]" % (msg, status)
  
  def connect(self):
    self.print_info("Connecting to %s:%s" % (transmission_host, transmission_port), self.thinking)
    try:
      self.transmission = transmissionrpc.Client(transmission_host, port=transmission_port,
        user=transmission_user, password=self.transmission_password,
        timeout=transmission_timeout)
      self.print_info("Connecting to %s:%s" % (transmission_host, transmission_port), self.connected)
    except:
      self.print_info("Connecting to %s:%s" % (transmission_host, transmission_port), self.error)
      sys.exit(0)

  def get_torrents(self, scp_client):
    for torrent in self.transmission.get_torrents(timeout=transmission_timeout):
      if torrent.doneDate != 0:
        self.print_info(torrent.name, self.copy)
        if (scp_client.get_resource(torrent.name) == 0):
#          self.transmission.remove_torrent(torrent.id, delete_data=True)
          self.print_info(torrent.name, self.delete)
        else:
          self.print_info(torrent.name, self.error)
      else:
        downloading_text = "Downloading "+ str(torrent.percentDone*100)+"%"
        self.print_info(torrent.name, colored(downloading_text, 'cyan', attrs=['dark']))

transmission = Transmission_Client()
transmission.connect()
scp = SCP_Client()
transmission.get_torrents(scp)
scp.close()
