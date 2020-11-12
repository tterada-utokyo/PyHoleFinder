# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import re

class Adoc:
  def __init__(self):
    self.data=[]

  def read(self,fname):
    fp=open(fname)
    self.data=[]
    section=[]
    for line in fp:
      m=re.match(r'\[([^=]+)=([^=]+)\]',line)
      if(m):
        if(section):
          self.data.append(section)
          section=[]
        (str0,str1)=m.groups()
        section.append((str0.strip(),str1.strip()))
        continue
      m=re.match(r'([^=]+)=([^=]+)',line)
      if(m):
        (str0,str1)=m.groups()
        section.append((str0.strip(),str1.strip()))
    if(section):
      self.data.append(section)
    fp.close()

  def write(self,fname):
    fp=open(fname,mode='w')
    for i in range(len(self.data)):
      section=self.data[i]
      for j in range(len(section)):
        if(i == 0 or i > 0 and j > 0):
          fp.write('%s = %s\n' % (section[j][0],section[j][1]))
        else:
          fp.write('\n[%s = %s]\n' % (section[j][0],section[j][1]))
    fp.write('\n')
    fp.close()

  def find_from_section(self,i,key):
    section=self.data[i]
    for j in range(len(section)):
      if(key == section[j][0]):
        return section[j][1]
    return None

  def find(self,key):
    list=[]
    for i in range(len(self.data)):
      val=None
      val=self.find_from_section(i,key)
      if(val is not None):
        list.append((i,val))
    return list

  def new_section(self):
    section=[]
    self.data.append(section)
    return len(self.data)-1

  def append(self,i,key,val):
    self.data[i].append((key,val))
