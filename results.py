# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import numpy as np
import math
import cv2
import params
from scipy.cluster.hierarchy import linkage, fcluster

class Results:
  def __init__(self):
    self.data=[]
    self.mask=[]
    self.holes=[]
    self.gdx=[]
    self.gdy=[]
    self.glist=[]
    self.gcrd=[]
    self.loaded=False
    self.detected=False
    self.clustered=False
    self.grouped=False
    self.excluded=False
    self.title=None
    self.MapID=None
    self.StageXYZ=None
    self.sort_coeff=[( 0, 1, 1, 0),(-1, 1, 1, 1),(-1, 0, 1, 0),(-1,-1,-1, 1),
                     ( 0,-1,-1, 0),( 1,-1,-1,-1),( 1, 0, 0,-1),( 1, 1, 1,-1),
                     ( 0, 1,-1, 0),(-1, 1,-1,-1),(-1, 0,-1, 0),(-1,-1, 1,-1),
                     ( 0,-1, 1, 0),( 1,-1, 1, 1),( 1, 0, 0, 1),( 1, 1,-1, 1)]
    self.xori=0
    self.yori=0
    self.scale=-1

  def load_MRC_data(self,mrcdata,params,window):
    if(not self.loaded):
      ny=mrcdata.shape[0]
      nx=mrcdata.shape[1]
      histogram=np.histogram(mrcdata,params.MRC_histogram_bins)
      htot=np.sum(histogram[0])
      hsum=0
      for i in range(len(histogram[0])):
        hsum+=histogram[0][i]
        if(float(hsum)/float(htot) > params.MRC_dark_cut):
          minval=histogram[1][i]
          break
      hsum=0
      for i in range(len(histogram[0])-1,-1,-1):
        hsum+=histogram[0][i]
        if(float(hsum)/float(htot) > params.MRC_bright_cut):
          maxval=histogram[1][i]
          break
      temp=mrcdata-minval
      maxval-=minval
      temp=np.where(temp < 0,0,temp)
      temp=np.where(temp > maxval,maxval,temp)
      fac=255.0/float(maxval)
      self.data=np.flipud(temp*fac).astype(np.uint8)
# Generate mask
      mth=params.mask_threshold
      ksize=params.mask_kernel_size
      nit=params.mask_iterations
      img=np.where(self.data < mth,0,255).astype(np.uint8)
      kernel=np.ones((ksize,ksize),dtype=np.uint8)
      img=cv2.dilate(img,kernel,iterations=1)
      img=cv2.erode(img,kernel,iterations=nit)
      self.mask=np.where(img < 128,0,1).astype(np.uint8)
      self.loaded=True
    return self.loaded

  def __find_hole(self,c0):
    d2min=0
    for i in range(len(self.holes)):
      c1=self.holes[i]
      d2=(c1[0]-c0[0])**2+(c1[1]-c0[1])**2
      if(i == 0 or d2min > d2):
        d2min=d2
        icen=i
    return icen

  def __find_hole_zone(self,c0,cut):
    cut2=cut**2
    for i in range(len(self.holes)):
      c1=self.holes[i]
      d2=(c1[0]-c0[0])**2+(c1[1]-c0[1])**2
      if(d2 < cut2):
        return True
    return False

  def cluster(self,params):
    if(self.loaded and self.detected and not self.clustered):
      Z=linkage(self.holes,method='single')
      cluster_ids=fcluster(Z,t=params.cluster_threshold,criterion='distance')
      ncluster=np.max(cluster_ids)
      count=np.zeros(ncluster+1,dtype=np.int32)
      for i in range(len(self.holes)):
        count[cluster_ids[i]]+=1
      cen_cid=np.argmax(count)
      cluster_holes=[]
      for i in range(len(self.holes)):
        if(cluster_ids[i] == cen_cid):
          cluster_holes.append(self.holes[i])
      self.holes=cluster_holes
      self.clustered=True
    return self.clustered

  def __find_closest4(self,icen,cut2):
    if(not self.loaded):
      return None
    if(not self.detected):
      return None
    list=[]
    cen=self.holes[icen]
#   print('ICEN=%d (%f,%f)' % (icen,cen[0],cen[1]))
    for i in range(len(self.holes)):
      if(i == icen):
        continue
      c1=self.holes[i]
      d2=(c1[0]-cen[0])**2+(c1[1]-cen[1])**2
      if(d2 < cut2):
        list.append((i,math.sqrt(d2)))
    slist=sorted(list,key=lambda x: x[1])
    if(len(slist)>=4 and slist[3][1]/slist[0][1] < 1.1):
      return slist[0:4]
    else:
      return None

  def __find_spacing(self,params):
    if(not self.loaded):
      return False
    if(not self.detected):
      return False
    xmin,ymin=np.min(self.holes,axis=0)
    xmax,ymax=np.max(self.holes,axis=0)
    factors=[(0.5,0.5),(0.3,0.5),(0.7,0.5),
             (0.5,0.3),(0.3,0.3),(0.7,0.3),
             (0.5,0.7),(0.3,0.7),(0.7,0.7)]
    xwidth=xmax-xmin
    ywidth=ymax-ymin
    cut=min(xwidth,ywidth)*0.1
    cut2=cut**2
    found=False
    for fac in factors:
      c0=(xmin+xwidth*fac[0],ymin+ywidth*fac[1])
      icen=self.__find_hole(c0)
      cen=self.holes[icen]
      slist=self.__find_closest4(icen,cut2)
      if(slist is not None):
        found=True
        break
    if(not found):
      for icen in range(len(self.holes)):
        cen=self.holes[icen]
        slist=self.__find_closest4(icen,cut2)
        if(slist is not None):
          found=True
          break
    if(found):
      ix=-1
      for i in range(4):
        c1=self.holes[slist[i][0]]
        if(c1[0]-cen[0] < 0):
          ix=slist[i][0]
          self.gdx=[self.holes[ix][0]-cen[0],
                    self.holes[ix][1]-cen[1]]
          break
      if(ix < 0):
        return False
      dx=[self.gdx[0],self.gdx[1]]
      norm=math.sqrt(dx[0]**2+dx[1]**2)
      dx[0]/=norm
      dx[1]/=norm
      iy=-1
      for i in range(4):
        c1=self.holes[slist[i][0]]
        dy=[c1[0]-cen[0],c1[1]-cen[1]]
        norm=math.sqrt(dy[0]**2+dy[1]**2)
        dy[0]/=norm
        dy[1]/=norm
        dp=dx[0]*dy[0]+dx[1]*dy[1]
        cp=dx[0]*dy[1]+dx[1]*dy[0]
        if(abs(dp) < 0.1 and cp < 0.0):
          iy=slist[i][0]
          self.gdy=[self.holes[iy][0]-cen[0],
                    self.holes[iy][1]-cen[1]]
          break
      if(ix >= 0 and iy >=0):
        return True
    return False
#       print(icen,ix,iy)
#       print(self.gdx)
#       print(self.gdy)

  def make_groups(self,params,window):
    if(self.loaded and self.detected):
      self.glist=[]
      self.gcrd=[]
      if(not self.cluster(params)):
        return False
      if(not self.__find_spacing(params)):
        return False
      v=self.sort_coeff[params.sort]
      self.holes=sorted(self.holes,key=lambda x:
                        (v[0]*x[0]+v[1]*x[1],v[2]*x[0]+v[3]*x[1]))
      dx=self.gdx
      dy=self.gdy
      normx2=dx[0]**2+dx[1]**2
      normy2=dy[0]**2+dy[1]**2
      nholes=len(self.holes)
      crd=np.zeros((nholes,2))
      c0=self.holes[0]
      for i in range(1,nholes):
        ci=self.holes[i]
        crd[i,0]=((ci[0]-c0[0])*dx[0]+(ci[1]-c0[1])*dx[1])/normx2
        crd[i,1]=((ci[0]-c0[0])*dy[0]+(ci[1]-c0[1])*dy[1])/normy2        
      cluster=[-1]*nholes
      cut=(params.gsize-1)/2+0.5
      ncluster=0
      for i in range(nholes):
        list=[]
        gcrd=[]
        found=False
        for j in range(nholes):
          if(cluster[j] >= 0):
            continue
          d0=crd[i,0]-crd[j,0]
          d1=crd[i,1]-crd[j,1]
          if(-cut < d0 < cut and -cut < d1 < cut):
            list.append(j)
            gcrd.append((int(round(d0)),int(round(d1))))
          if(len(set(gcrd)) == params.gsize**2):
            found=True
            break
        if(found):
          for j in list:
            cluster[j]=ncluster
          self.glist.append(list)
          self.gcrd.append(gcrd)
          ncluster+=1
        v=math.floor((i+1)/nholes*100)
        window['-PROGRESS-'].UpdateBar(v)
        vtext='%3d%%' % v
        window['-PROGRESS-TEXT-'].Update(value=vtext)
      self.grouped=True
    return self.grouped

  def add_hole(self,pos,params):
    if(self.loaded and self.detected):
      if(not self.grouped):
        self.__find_spacing(params)
      near=self.__find_hole(pos)
      c0=self.holes[near]
      dx=self.gdx
      dy=self.gdy
      normx2=dx[0]**2+dx[1]**2
      normy2=dy[0]**2+dy[1]**2
      d0=abs(((pos[0]-c0[0])*dx[0]+(pos[1]-c0[1])*dx[1])/normx2)
      d1=abs(((pos[0]-c0[0])*dy[0]+(pos[1]-c0[1])*dy[1])/normy2)
      if(d0 > 0.5 or d1 > 0.5):
        self.holes=np.append(self.holes,[[pos[0],pos[1]]],axis=0)
        return True
    return False

  def delete_hole(self,pos,params):
    if(self.loaded and self.detected):
      if(not self.grouped):
        self.__find_spacing(params)
      del_hole=self.__find_hole(pos)
      c0=self.holes[del_hole]
      dx=self.gdx
      dy=self.gdy
      normx2=dx[0]**2+dx[1]**2
      normy2=dy[0]**2+dy[1]**2
      d0=abs(((pos[0]-c0[0])*dx[0]+(pos[1]-c0[1])*dx[1])/normx2)
      d1=abs(((pos[0]-c0[0])*dy[0]+(pos[1]-c0[1])*dy[1])/normy2)
      if(d0 < 0.5 and d1 < 0.5):
        self.holes=np.delete(self.holes,del_hole,axis=0)
        glist_new=[]
        gcrd_new=[]
        for i in range(len(self.glist)):
          gl=self.glist[i]
          gc=self.gcrd[i]
          if(not del_hole in gl):
            for j in range(len(gl)):
              if(gl[j]>=del_hole):
                gl[j]-=1
            glist_new.append(gl)
            gcrd_new.append(gc)
        self.glist=glist_new
        self.gcrd=gcrd_new
        return True
    return False

  def delete_all_holes(self):
    if(self.loaded and self.detected):
      self.holes=[]
      self.glist=[]
      self.gcrd=[]
      self.detected=False
      self.clustered=False
      self.grouped=False
      return True
    return False

  def template_matching(self,template,params,window):
    if(not self.loaded):
      return False
    img=self.data*self.mask
    match=cv2.matchTemplate(img,template.image,cv2.TM_CCOEFF_NORMED)
    hit=np.where(match > params.TM_threshold)
    sorted_hit=sorted(list(zip(*hit)),key=lambda x: -match[x[0],x[1]])
    params.hole_radius=template.radius
    nholes=len(sorted_hit)
    i=0
    for pos in sorted_hit:
      d=params.template_padding+template.radius
      cy=pos[0]+d
      cx=pos[1]+d
      if(not self.__find_hole_zone((cx,cy),template.radius)):
        if(len(self.holes) > 0):
          self.holes=np.append(self.holes,[[cx,cy]],axis=0)
        else:
          self.holes=np.array([[cx,cy]])
      v=math.floor((i+1)/nholes*100)
      window['-PROGRESS-'].UpdateBar(v)
      vtext='%3d%%' % v
      window['-PROGRESS-TEXT-'].Update(value=vtext)
      i+=1
    if(len(self.holes) > 0):
      self.detected=True
    return True
