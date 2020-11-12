# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import base64
import io
import math
import numpy as np
import cv2
from PIL import Image
import params
import adoc
import os

def draw_image(obj,data,params):
  ny=data.shape[0]
  nx=data.shape[1]
  if(params.scale <= 0):
    if(params.fit_mode == 'height'):
      params.scale=params.ysize/ny
    elif(params.fit_mode == 'width'):
      params.scale=params.xsize/nx
    else:
      params.scale=min(params.xsize/nx,params.ysize/ny)
    params.xori=round(0.5*(params.xsize-nx*params.scale))
    params.yori=round(0.5*(ny*params.scale-params.ysize)+params.ysize)
# print(params.scale)
  xstart=max(int(math.floor(-params.xori/params.scale)),0)
  ystart=max(int(math.floor((params.yori-params.ysize)/params.scale)),0)
  xend=min(xstart+int(math.ceil(params.xsize/params.scale)),nx)
  yend=min(ystart+int(math.ceil(params.ysize/params.scale)),ny)
  disp_region=data[ystart:yend,xstart:xend]
  ny1=disp_region.shape[0]
  nx1=disp_region.shape[1]
  nx2=math.floor(nx1*params.scale)
  ny2=math.floor(ny1*params.scale)
  if(params.scale < 1.0):
    data2=cv2.resize(disp_region,(nx2,ny2),interpolation=cv2.INTER_AREA)
  else:
    data2=cv2.resize(disp_region,(nx2,ny2),interpolation=cv2.INTER_LINEAR)
  if(data2.ndim == 2):
    data2=cv2.merge((data2,data2,data2))
  img_pil=Image.fromarray(data2)
# print(img_pil.mode)
  with io.BytesIO() as output:
    img_pil.save(output,format='PNG')
    data3=output.getvalue()
  obj.DrawRectangle((0,0),(params.xsize,params.ysize),fill_color='black')
  xori=max(0,params.xori)
  yori=min(params.ysize,params.yori)
  obj.DrawImage(data=base64.b64encode(data3),location=(xori,yori))

def draw_circles(data,circles,params):
  data2=np.empty_like(data)
  color=params.circle_color
  if(data2.ndim == 2):
    data2[:,:]=data[:,:]
    data2=cv2.merge((data2,data2,data2))
  else:
    data2[:,:,:]=data[:,:,:]
  rad=int(math.ceil(params.hole_radius+params.hole_padding))
  lw=int(params.line_width)
  for c in circles:
    cv2.circle(data2,(int(c[0]),int(c[1])),rad,color,lw)
  return data2

def draw_groups(data,glist,gcrd,holes,params):
  data2=np.empty_like(data)
  if(data2.ndim == 2):
    data2[:,:]=data[:,:]
    data2=cv2.merge((data2,data2,data2))
  else:
    data2[:,:,:]=data[:,:,:]
  color=params.group_color
  for i in range(len(glist)):
    gl=glist[i]
    gc=gcrd[i]
    gsize=round(math.sqrt(len(gl)))
    vcrd=int(round((gsize-1)/2))
    rad=int(math.ceil(params.hole_radius+params.hole_padding)*math.sqrt(2.0))
    lw=int(params.line_width)
    ok=0
    for j in range(len(gl)):
      if(gc[j] == (0,0)):
        xc=round(holes[gl[j]][0])
        yc=round(holes[gl[j]][1])
        ok+=1
    for j in range(len(gl)):
      if(gc[j] == (-vcrd,-vcrd)):
        x0=round(holes[gl[j]][0])
        y0=round(holes[gl[j]][1])
        dr=math.sqrt((x0-xc)**2+(y0-yc)**2)
        x0=int(xc+round((x0-xc)*(dr+rad)/dr))
        y0=int(yc+round((y0-yc)*(dr+rad)/dr))
        ok+=1
      if(gc[j] == (vcrd,-vcrd)):
        x1=round(holes[gl[j]][0])
        y1=round(holes[gl[j]][1])
        dr=math.sqrt((x1-xc)**2+(y1-yc)**2)
        x1=int(xc+round((x1-xc)*(dr+rad)/dr))
        y1=int(yc+round((y1-yc)*(dr+rad)/dr))
        ok+=1
      if(gc[j] == (vcrd,vcrd)):
        x2=round(holes[gl[j]][0])
        y2=round(holes[gl[j]][1])
        dr=math.sqrt((x2-xc)**2+(y2-yc)**2)
        x2=int(xc+round((x2-xc)*(dr+rad)/dr))
        y2=int(yc+round((y2-yc)*(dr+rad)/dr))
        ok+=1
      if(gc[j] == (-vcrd,vcrd)):
        x3=round(holes[gl[j]][0])
        y3=round(holes[gl[j]][1])
        dr=math.sqrt((x3-xc)**2+(y3-yc)**2)
        x3=int(xc+round((x3-xc)*(dr+rad)/dr))
        y3=int(yc+round((y3-yc)*(dr+rad)/dr))
        ok+=1
    if(ok == 5):
      cv2.line(data2,(x0,y0),(x1,y1),color,lw)
      cv2.line(data2,(x1,y1),(x2,y2),color,lw)
      cv2.line(data2,(x2,y2),(x3,y3),color,lw)
      cv2.line(data2,(x3,y3),(x0,y0),color,lw)
#     cv2.line(data2,(xc-10,yc),(xc+10,yc),color,2)
#     cv2.line(data2,(xc,yc-10),(xc,yc+10),color,2)
    else:
      print(gsize,vcrd)
      print(gl)
      print(gc)
  return data2

def draw_box(data,pos0,pos1,params):
  data2=np.empty_like(data)
  if(data2.ndim == 2):
    data2[:,:]=data[:,:]
    data2=cv2.merge((data2,data2,data2))
  else:
    data2[:,:,:]=data[:,:,:]
  color=params.group_color
  lw=params.line_width
  x0=int(pos0[0])
  y0=int(pos0[1])
  x1=int(pos1[0])
  y1=int(pos1[1])
  cv2.rectangle(data2,(x0,y0),(x1,y1),color,lw)
  return data2

def save(results,nv,fname,param):
  ad=adoc.Adoc()
  sec=ad.new_section()
  ad.append(sec,'AdocVersion','2.00')
  for r in results:
    if(not r.excluded):
      groupID=nv.new_groupID()
      ny=r.data.shape[0]
      if(r.grouped):
        list=[]
        for i in range(len(r.glist)):
          gl=r.glist[i]
          gc=r.gcrd[i]
          ok=False
          for j in range(len(gl)):
            if(gc[j] == (0,0)):
              list.append(gl[j])
              break
      else:
        list=range(len(r.holes))
      nitem=0
      for i in list:
        xc=int(r.holes[i][0])
        yc=ny-1-int(r.holes[i][1])
        sec=ad.new_section()
        title='%s-%03d' % (r.title,nitem+1)
        ad.append(sec,"Item",title)
        nitem+=1
        ad.append(sec,'Color',param.navi_color)
        ad.append(sec,'NumPts',1)
        ad.append(sec,'Regis',1)
        ad.append(sec,'Type',0)
        ad.append(sec,'PtsX',xc)
        ad.append(sec,'PtsY',yc)
        ad.append(sec,'DrawnID',r.MapID)
        ad.append(sec,'GroupID',groupID)
        ad.append(sec,'Acquire',1)
        crd='%d %d %s' % (xc,yc,r.StageXYZ[2])
        ad.append(sec,'CoordsInMap',crd)
  ad.write(fname)

def backfile(fname):
  if(os.path.exists(fname)):
    i=1
    while(True):
      new_fname=fname+('.%d' % i)
      if(os.path.exists(new_fname)):
        i+=1
      else:
        os.rename(fname,new_fname)
        print('%s was renamed %s.' % (fname,new_fname))
        return True
        break
  else:
    return False
