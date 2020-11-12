# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import adoc

def get_val_int_tuple(doc,sec,key,x):
  val=doc.find_from_section(sec,key)
  if(val is not None):
    data=val.split()
    list=[]
    for i in data:
      list.append(int(i))
    return list
  else:
    return x

def get_val_int(doc,sec,key,x):
  val=doc.find_from_section(sec,key)
  if(val is not None):
    return int(float(val))
  else:
    return x

def get_val_float(doc,sec,key,x):
  val=doc.find_from_section(sec,key)
  if(val is not None):
    return float(val)
  else:
    return x

def get_val_text(doc,sec,key,x):
  val=doc.find_from_section(sec,key)
  if(val is not None):
    return val
  else:
    return x

class Params:
  def __init__(self):
# Parameters for display
    self.xsize=800
    self.ysize=600
    self.xori=0
    self.yori=self.ysize
    self.scale=-1.0
    self.fit_mode='auto'
# Parameters for MRC data import
    self.MRC_histogram_bins=2000
    self.MRC_dark_cut=0.005
    self.MRC_bright_cut=0.005
# Membrane region mask
    self.mask_threshold=10
    self.mask_kernel_size=10
    self.mask_iterations=5
# Parameters for template matching and circle drawing
    self.hole_radius=8
    self.hole_padding=6
    self.line_width=2
    self.template_padding=6
    self.TM_threshold=0.6
# Parameters for grouping
    self.cluster_threshold=100
    self.gsize=5
    self.sort=0
# Parameters for color
    self.circle_color=(255,0,0)
    self.group_color=(255,0,0)
    self.template_color=(0,0,255)
    self.navi_color=3

  def zoom(self,fac,x0,y0):
    self.scale=self.scale*fac
    dx=self.xori-x0
    dy=self.yori-y0
    dx*=fac
    dy*=fac
    self.xori=int(dx+x0)
    self.yori=int(dy+y0)

  def translate(self,dx,dy):
    self.xori+=dx
    self.yori+=dy

  def get_pos(self,p):
    x=(p[0]-self.xori)/self.scale
    y=-(p[1]-self.yori)/self.scale
    return (x,y)

  def read(self,fname):
    conf=adoc.Adoc()
    conf.read(fname)
    self.xsize=get_val_int(conf,0,'xsize',self.xsize)
    self.ysize=get_val_int(conf,0,'ysize',self.ysize)
    self.xori=0
    self.yori=self.ysize
    self.scale=-1.0
    self.fit_mode=get_val_text(conf,0,'fit_mode',self.fit_mode)
    self.MRC_histogram_bins=get_val_int(conf,0,'MRC_histogram_bins',
                                        self.MRC_histogram_bins)
    self.MRC_dark_cut=get_val_float(conf,0,'MRC_dark_cut',
                                    self.MRC_dark_cut)
    self.MRC_bright_cut=get_val_float(conf,0,'MRC_bright_cut',
                                      self.MRC_bright_cut)
    self.mask_threshold=get_val_int(conf,0,'mask_threshold',
                                    self.mask_threshold)
    self.mask_kernel_size=get_val_int(conf,0,'mask_kernel_size',
                                      self.mask_kernel_size)
    self.mask_iterations=get_val_int(conf,0,'mask_iterations',
                                     self.mask_iterations)
    self.hole_radius=get_val_int(conf,0,'hole_radius',self.hole_radius)
    self.hole_padding=get_val_int(conf,0,'hole_padding',self.hole_padding)
    self.line_width=get_val_int(conf,0,'line_width',self.line_width)
    self.template_padding=get_val_int(conf,0,'template_padding',
                                      self.template_padding)
    self.TM_threshold=get_val_float(conf,0,'TM_threshold',self.TM_threshold)
    self.cluster_threshold=get_val_int(conf,0,'threshold',
                                       self.cluster_threshold)
    self.gsize=get_val_int(conf,0,'gsize',self.gsize)
    self.sort=get_val_int(conf,0,'sort',self.sort)
    self.circle_color=get_val_int_tuple(conf,0,'circle_color',
                                        self.circle_color)
    self.group_color=get_val_int_tuple(conf,0,'group_color',self.group_color)
    self.template_color=get_val_int_tuple(conf,0,'template_color',
                                          self.template_color)
    self.navi_color=get_val_int(conf,0,'navi_color',self.navi_color)

  def write(self,fname):
    conf=adoc.Adoc()
    i=conf.new_section()
    conf.append(i,'xsize',self.xsize)
    conf.append(i,'ysize',self.ysize)
    conf.append(i,'fit_mode',self.fit_mode)
    conf.append(i,'MRC_histogram_bins',self.MRC_histogram_bins)
    conf.append(i,'MRC_dark_cut',self.MRC_dark_cut)
    conf.append(i,'MRC_bright_cut',self.MRC_bright_cut)
    conf.append(i,'mask_threshold',self.mask_threshold)
    conf.append(i,'mask_kernel_size',self.mask_kernel_size)
    conf.append(i,'mask_iterations',self.mask_iterations)
    conf.append(i,'hole_radius',self.hole_radius)
    conf.append(i,'hole_padding',self.hole_padding)
    conf.append(i,'line_width',self.line_width)
    conf.append(i,'template_padding',self.template_padding)
    conf.append(i,'TM_threshold',self.TM_threshold)
    conf.append(i,'cluster_threshold',self.cluster_threshold)
    conf.append(i,'gsize',self.gsize)
    conf.append(i,'sort',self.sort)
    str='%d %d %d' % tuple(self.circle_color)
    conf.append(i,'circle_color',str)
    str='%d %d %d' % tuple(self.group_color)
    conf.append(i,'group_color',str)
    str='%d %d %d' % tuple(self.template_color)
    conf.append(i,'template_color',str)
    conf.append(i,'navi_color',self.navi_color)
    conf.write(fname)
