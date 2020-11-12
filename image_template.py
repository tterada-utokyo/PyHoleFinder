# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import math
import numpy as np
import cv2

class ImageTemplate:
  def __init__(self):
    self.has_template=False
    self.center=None
    self.radius=0
    self.image=None
    self.index=None

  def set(self,pos0,pos1,index):
    self.center=(round(pos0[0]),round(pos0[1]))
    self.radius=round(min(abs(pos1[0]-pos0[0]),abs(pos1[1]-pos0[1])))
    self.has_template=True
    self.index=index

  def draw_box(self,data,params):
    if(self.has_template):
      data2=np.empty_like(data)
      if(data2.ndim == 2):
        data2[:,:]=data[:,:]
        data2=cv2.merge((data2,data2,data2))
      else:
        data2[:,:,:]=data[:,:,:]
      color=params.template_color
      lw=params.line_width
      ny=data.shape[0]
      nx=data.shape[1]
      d=self.radius+params.template_padding
      xstart=max(int(math.floor(self.center[0]-d)),0)
      xend=min(int(math.ceil(self.center[0]+d)),nx)
      ystart=max(int(math.floor(self.center[1]-d)),0)
      yend=min(int(math.ceil(self.center[1]+d)),ny)
      cv2.rectangle(data2,(xstart,ystart),(xend,yend),color,lw)
      return data2
    else:
      return data

  def draw_circle(self,data,params):
    if(self.has_template):
      data2=np.empty_like(data)
      if(data2.ndim == 2):
        data2[:,:]=data[:,:]
        data2=cv2.merge((data2,data2,data2))
      else:
        data2[:,:,:]=data[:,:,:]
      color=params.template_color
      lw=params.line_width
      cv2.circle(data2,self.center,self.radius,color,params.line_width)
      return data2
    else:
      return data

  def extract(self,data,params):
    if(self.has_template):
      ny=data.shape[0]
      nx=data.shape[1]
      d=self.radius+params.template_padding
      xstart=max(int(math.floor(self.center[0]-d)),0)
      xend=min(int(math.ceil(self.center[0]+d)),nx)
      ystart=max(int(math.floor(self.center[1]-d)),0)
      yend=min(int(math.ceil(self.center[1]+d)),ny)
      self.image=data[ystart:yend,xstart:xend]

  def save(self,fname):
    if(self.has_template):
      cv2.imwrite(fname,self.image)
