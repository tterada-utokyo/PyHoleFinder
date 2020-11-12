# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import adoc
import numpy as np

class Navi:
  def __init__(self):
    self.ad=None
    self.file_index={}
    self.file_list=[]
    self.section=[]
    self.title=[]
    self.MapID=[]
    self.StageXYZ=[]
    self.groupID_list=[]
    self.sliceID=[]

  def read(self,fname):
    self.ad=adoc.Adoc()
    self.ad.read(fname)
    hit=self.ad.find('MapFile')
    temp_list=[]
    for v in hit:
      temp_list.append(v[1])
    self.file_list=list(set(temp_list))
    self.section=[]
    self.title=[]
    self.MapID=[]
    self.StageXYZ=[]
    self.sliceID=[]
    for i in range(len(self.file_list)):
      self.file_index[self.file_list[i]]=i
      self.section.append([])
      self.title.append([])
      self.MapID.append([])
      self.StageXYZ.append([])
      self.sliceID.append([])
    for v in hit:
      i=self.file_index[v[1]]
      self.section[i].append(v[0])
      self.title[i].append(self.ad.data[v[0]][0][1])
      u=self.ad.find_from_section(v[0],'MapID')
      self.MapID[i].append(u)
      u=self.ad.find_from_section(v[0],'StageXYZ')
      self.StageXYZ[i].append(u.split())
      u=self.ad.find_from_section(v[0],'Note')
      tokens=u.split()
      if(tokens[0] == 'Sec'):
        self.sliceID[i].append(int(tokens[1]))
      else:
        self.sliceID[i].append(len(self.sliceID[i]))

#   print(self.file_index)
#   print(self.file_list)
#   print(self.section)
#   print(self.title)
#   print(self.MapID)
#   print(self.StageXYZ)

  def new_groupID(self):
    if(len(self.groupID_list) == 0):
      hit=self.ad.find('GroupID')
      temp_list=[]
      for v in hit:
        temp_list.append(v[1])
      self.groupID_list=set(temp_list)
    while(True):
      r=np.random.randint(0,2**31)
      if(not r in self.groupID_list):
        self.groupID_list.add(r)
        return r

if __name__ == '__main__':
  navi=Navi()
  navi.read('navi2.nav')
      
    
