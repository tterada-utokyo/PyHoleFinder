# PyHoleFinder
# Copyright (2020) Tohru Terada, The Universiy of Tokyo
# The source code is distributed under the MIT license. See LICENSE for details.

import os
import sys
import math
import mrcfile
import PySimpleGUI as sg
import params as prms
import funcs
import results
import navi
import image_template

# Grobal variables
params=prms.Params()

# Main function arguments
args=sys.argv
conf_ok=False
nav_ok=False
out_ok=False
for i in range(1,len(args)-1):
  if(args[i] == '-conf'):
    conf_ok=True
    fname_conf=args[i+1]
  elif(args[i] == '-nav'):
    nav_ok=True
    fname_nav=args[i+1]
  elif(args[i] == '-out'):
    out_ok=True
    fname_out=args[i+1]
    funcs.backfile(fname_out)
if(not nav_ok or not out_ok):
  print('Usage: %s [-conf config.txt] -nav input.nav -out output.nav'
        % args[0])
  sys.exit(1)

# Read configuration file
# First read default configuration file
fname=os.path.join(os.path.dirname(args[0]),'config_default.txt')
if(os.path.exists(fname)):
  params.read(fname)
  print('%s is used for default configuration file' % fname)
# Next read designated configuration file
if(conf_ok):
  if(os.path.exists(fname_conf)):
    params.read(fname_conf)
    print('Parameters of %s are used' % fname_conf)
  else:
    print('Cannot open %s' % fname_conf)
    print('Default parameters are used.')
else:
  fname_conf='config.txt'

# Load SerialEM Navigator file
nv=navi.Navi()
if(os.path.exists(fname_nav)):
  nv.read(fname_nav)
  fitem=[]
  for fname in nv.file_list:
    fitem.append(fname)
else:
  print('Cannot open %s' % fname_nav)
  sys.exit(1)

# Prepare widgets
item=['---']
item2=['3: 3x3','5: 5x5']
if(params.gsize == 3):
  dval2=item2[0]
else:
  dval2=item2[1]
item3=[]
sort_index={}
for i in range(16):
  item3.append('sort %d' % i)
  sort_index[item3[i]]=i
dval3=item3[params.sort]
item4=['auto','height','width']
if(params.fit_mode == 'height'):
  dval4='height'
elif(params.fit_mode == 'width'):
  dval4='width'
else:
  dval4='auto'
TM_thresholdText='%.1f' % float(params.TM_threshold)
frame1=[[sg.Button('Select',size=(10,1)),
         sg.Button('Adjust',size=(10,1)),
         sg.Text('threshold:',size=(9,1)),
         sg.Input(default_text=TM_thresholdText,size=(9,1),
                  key='-TMTHRESHOLD-'),
         sg.Button('Apply',size=(10,1)),
         sg.Button('Apply to all',size=(10,1))],
        [sg.Button('Add',size=(10,1)),
         sg.Button('Delete',size=(10,1)),
         sg.Button('Clear',size=(10,1)),
         sg.Button('Clear all',size=(10,1)),
         sg.Button('Cluster',size=(10,1)),
         sg.Button('Cluster all',size=(10,1))]]
layout=[[sg.Graph(canvas_size=(params.xsize,params.ysize),
                  graph_bottom_left=(0,0),
                  graph_top_right=(params.xsize,params.ysize),
                  key='-GRAPH-',
                  change_submits=True,drag_submits=True)],
        [sg.Text('Progress:',size=(15,1)),
         sg.ProgressBar(100,orientation='h',size=(20,15),key='-PROGRESS-'),
         sg.Text('  0% ',size=(5,1),key='-PROGRESS-TEXT-')],
        [sg.Text('Select file:',size=(15,1)),
         sg.OptionMenu(fitem,size=(75,1),key='-FILE-'),
         sg.Button('Open',size=(10,1))],
        [sg.Text('Select image:',size=(15,1)),
         sg.Spin(item,size=(10,1),key='-SLICE-'),
         sg.Checkbox('Exclude',size=(10,1),key='-EXCLUDE-'),
         sg.Button('Translate',size=(10,1)),
         sg.Button('Zoom',size=(10,1)),
         sg.Button('Fit',size=(10,1)),
         sg.OptionMenu(item4,default_value=dval4,size=(10,1),key='-FIT-')],
        [sg.Text('Template matching:',size=(15,1)),
         sg.Frame('',frame1,key='-FRAME1-')],
        [sg.Text('Group holes:',size=(15,1)),
         sg.OptionMenu(item2,default_value=dval2,
                       size=(10,1),key='-GROUP-SIZE-'),
         sg.OptionMenu(item3,default_value=dval3,
                       size=(10,1),key='-SORT-ORDER-'),
         sg.Button('Group',size=(10,1)),
         sg.Button('Group all',size=(10,1))],
        [sg.Text('Status:',size=(75,1),key='-STATUS-TEXT-'),
         sg.Button('Save',size=(10,1)),
         sg.Button('Quit',size=(10,1))]]
window=sg.Window('PyHoleFinder',layout,return_keyboard_events=True,
                 location=(0, 0),use_default_focus=False,finalize=True)
graph=window.Element('-GRAPH-')
stext=window.Element('-STATUS-TEXT-')
window['-SLICE-'].bind('<ButtonRelease-1>','+UP+')
window['-EXCLUDE-'].bind('<ButtonRelease-1>','+UP+')
window['-FRAME1-'].expand(expand_x=True)
window['-PROGRESS-'].expand(expand_x=True)

# Main loop
mode=None
index=0
opened=False
saved=False
img_temp=image_template.ImageTemplate()
while True:
  event,values=window.read()
# print(event,values)
  if event is None:
    break
  elif event == 'q' or event == 'Quit':
    if not saved:
      reply=sg.PopupOKCancel('Data are discarded. Really quit?')
      if reply == 'Cancel':
        continue
    reply=sg.PopupYesNo('Do you want to save settings?')
    if reply == 'Yes':
      params.write(fname_conf)
    break
  elif event == 'Open':
    if opened:
      reply=sg.PopupOKCancel('Data are discarded. Really open?')
      if(reply == 'Cancel'):
        continue
      else:
        graph.DrawRectangle((0,0),(params.xsize,params.ysize),
                            fill_color='black')
    mode='None'
    fname=values['-FILE-']
    findex=nv.file_index[fname]
    if(not os.path.exists(fname)):
      replay=sg.Popup('%s does not exist.' % fname)
      continue
    mrc=mrcfile.open(fname)
    nimage=mrc.data.shape[0]
    if(nimage > len(nv.title[findex])):
      nimage=len(nv.title[findex])
    item=[]
    r=[]
    title_index={}
# Load all images of selected file
    stext.Update(value='Status: Loading images from %s' % fname)
    for i in range(nimage):
      title='%d : %s' % (i,nv.title[findex][i])
      title_index[title]=i
      item.append(title)
      r.append(results.Results())
      r[i].title=nv.title[findex][i]
      r[i].MapID=nv.MapID[findex][i]
      r[i].StageXYZ=nv.StageXYZ[findex][i]
      r[i].load_MRC_data(mrc.data[nv.sliceID[findex][i]],params,window)
      r[i].xori=0
      r[i].yori=params.ysize
      r[i].scale=-1
      v=math.floor((i+1)/nimage*100)
      window['-PROGRESS-'].UpdateBar(v)
      vtext='%3d%%' % v
      window['-PROGRESS-TEXT-'].Update(value=vtext)
    window['-SLICE-'].Update(values=item,value=item[index])
    opened=True
# Display first image
    index=0
    stext.Update(value='Status: %s is displayed' % r[index].title)
    window['-EXCLUDE-'].Update(value=r[index].excluded)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    else:
      current_img=r[index].data
    params.xori=r[index].xori
    params.yori=r[index].yori
    params.scale=r[index].scale
    params.fit_mode=values['-FIT-']
    funcs.draw_image(graph,current_img,params)
  elif event == '-SLICE-+UP+' and opened:
# Display selected image
    mode='None'
    prev_index=index
    val=values['-SLICE-']
    index=title_index[val]
    msg='Status: %s is displayed' % val
    window['-EXCLUDE-'].Update(value=r[index].excluded)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      msg+=', %d holes' % len(r[index].holes)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
        msg+=', %d groups' % len(r[index].glist)
    else:
      current_img=r[index].data
    r[prev_index].xori=params.xori
    r[prev_index].yori=params.yori
    r[prev_index].scale=params.scale
    params.xori=r[index].xori
    params.yori=r[index].yori
    params.scale=r[index].scale
    params.fit_mode=values['-FIT-']
    funcs.draw_image(graph,current_img,params)
    stext.Update(value=msg)
  elif event == '-EXCLUDE-+UP+' and opened:
    r[index].excluded=values['-EXCLUDE-']
  elif (event == 't' or event == 'Translate') and opened:
    mode='t'
    stext.Update(value='Status: Translation Mode: drag to translate')
    mouse_x0=-1
    mouse_y0=-1
  elif (event == 'z' or event == 'Zoom') and opened:
    mode='z'
    stext.Update(value='Status: Zoom Mode: drag to zoom')
    mouse_x0=-1
    mouse_y0=-1
  elif (event == 'f' or event == 'Fit') and opened and r[index].loaded:
    mode='None'
    stext.Update(value='Status: Scaled to fit to the canvas')
    mouse_x0=-1
    mouse_y0=-1
    params.xori=0
    params.yori=params.ysize
    params.scale=-1.0
    params.fit_mode=values['-FIT-']
    funcs.draw_image(graph,current_img,params)
  elif event == '0':
    mode='None'
    stext.Update(value='Status:')
  elif (event == 's' or event == 'Select') and opened and r[index].loaded:
    mode='s'
    mouse_x0=-1
    mouse_y0=-1
    msg='Status: Template Selection Mode: '
    msg+='click center of a hole and drag to enclose the hole'
    stext.Update(value=msg)
  elif event == 'Adjust' and opened and r[index].loaded and img_temp.has_template:
    if(img_temp.index == index):
      mode='j'
      backup_img=current_img
      current_img=img_temp.draw_circle(backup_img,params)
      funcs.draw_image(graph,current_img,params)
      current_img=backup_img
      msg='Status: Use arrow keys to move, +/- to change size, and ESC to set and exit'
      stext.Update(value=msg)
    else:
      msg='Status: Change image to %s' % r[img_temp.index].title
      stext.Update(value=msg)
  elif (event == 'Apply' or event == 'Apply to all') and opened:
    params.TM_threshold=float(values['-TMTHRESHOLD-'])
    if(event == 'Apply'):
      list=[index]
    else:
      list=range(nimage)
    for i in list:
      if(r[i].loaded and not r[i].excluded):
        r[i].template_matching(img_temp,params,window)
        msg='Status: %s: %d holes detected' % (r[i].title,len(r[i].holes))
        print(msg)
        stext.Update(value=msg)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    funcs.draw_image(graph,current_img,params)
  elif (event == 'Add' or event == 'a') and opened:
    mode = 'a'
    msg='Status: Addition Mode: click center of a hole to add'
    stext.Update(value=msg)
  elif (event == 'Delete' or event == 'd') and opened:
    mode = 'd'
    msg='Status: Deletion Mode: click center of a hole to delete'
    stext.Update(value=msg)
  elif (event == 'Clear' or event == 'Clear all') and opened:
    if(event == 'Clear'):
      list=[index]
      msg='Status: Deleted all holes in this image'
    else:
      list=range(nimage)
      msg='Status: Deleted all holes in all images'
    for i in list:
      if(r[i].loaded and not r[i].excluded):
        r[i].delete_all_holes()
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    else:
      current_img=r[index].data
    funcs.draw_image(graph,current_img,params)
    stext.Update(value=msg)
  elif (event == 'Cluster' or event == 'Cluster all') and opened:
    if(event == 'Cluster'):
      list=[index]
      msg='Status: Cluster holes in this image'
    else:
      list=range(nimage)
      msg='Status: Cluster holes in all images'
    for i in list:
      if(r[i].loaded and not r[i].excluded):
        r[i].cluster(params)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    else:
      current_img=r[index].data
    funcs.draw_image(graph,current_img,params)
    stext.Update(value=msg)
  elif (event == 'Group' or event == 'Group all') and opened:
    mode='None'
    gsize=values['-GROUP-SIZE-']
    if(gsize == item2[0]):
      params.gsize=3
    else:
      params.gsize=5
    params.sort=sort_index[values['-SORT-ORDER-']]
    if(event == 'Group'):
      list=[index]
    else:
      list=range(nimage)
    for i in list:
      if(r[i].loaded and not r[i].excluded):
        r[i].make_groups(params,window)
        msg='Status: %s: %d groups generated' % (r[i].title,len(r[i].glist))
        print(msg)
        stext.Update(value=msg)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    funcs.draw_image(graph,current_img,params)
  elif event == 'Save' and opened:
    funcs.save(r,nv,fname_out,params)
    stext.Update(value='Status: Wrote centers in %s' % fname_out)
    saved=True
  elif event == '-GRAPH-' and mode == 't' and opened and r[index].loaded:
    if mouse_x0 < 0 and mouse_y0 < 0:
      mouse_x0,mouse_y0=values['-GRAPH-']
    else:
      mouse_x1,mouse_y1=values['-GRAPH-']
      dx=mouse_x1-mouse_x0
      dy=mouse_y1-mouse_y0
      params.translate(dx,dy)
      funcs.draw_image(graph,current_img,params)
      mouse_x0=mouse_x1
      mouse_y0=mouse_y1
  elif event == '-GRAPH-' and mode == 'z' and opened and r[index].loaded:
    if mouse_x0 < 0 and mouse_y0 < 0:
      mouse_x0,mouse_y0=values['-GRAPH-']
      mouse_x1=mouse_x0
      mouse_y1=mouse_y0
    else:
      mouse_x2,mouse_y2=values['-GRAPH-']
      dx=mouse_x2-mouse_x1
      dy=mouse_y2-mouse_y1
      fac=(1.0-dy/params.ysize)
      params.zoom(fac,mouse_x0,mouse_y0)
      funcs.draw_image(graph,current_img,params)
      mouse_x1=mouse_x2
      mouse_y1=mouse_y2
  elif event == '-GRAPH-' and mode == 's' and opened and r[index].loaded:
    if mouse_x0 < 0 and mouse_y0 < 0:
      mouse_x0,mouse_y0=values['-GRAPH-']
      backup_img=current_img
      img_temp=image_template.ImageTemplate()
    else:
      mouse_x1,mouse_y1=values['-GRAPH-']
      pos0=params.get_pos((mouse_x0,mouse_y0))
      pos1=params.get_pos((mouse_x1,mouse_y1))
      img_temp.set(pos0,pos1,index)
      current_img=img_temp.draw_circle(backup_img,params)
      funcs.draw_image(graph,current_img,params)
  elif event == '-GRAPH-+UP' and mode == 's' and opened and r[index].loaded:
    mode='None'
    mouse_x1,mouse_y1=values['-GRAPH-']
    pos0=params.get_pos((mouse_x0,mouse_y0))
    pos1=params.get_pos((mouse_x1,mouse_y1))
    img_temp.set(pos0,pos1,index)
    current_img=img_temp.draw_box(backup_img,params)
    funcs.draw_image(graph,current_img,params)
    img_temp.extract(r[index].data,params)
    val=(img_temp.center[0],img_temp.center[1],img_temp.radius)
    msg='Status: Template at (%d,%d) with radius %d' % val
    stext.Update(value=msg)
    current_img=backup_img
    mouse_x0=-1
    mouse_y0=-1
  elif (event == 'Left:37' or event == 'Up:38' or event == 'Right:39' or
        event == 'Down:40' or event == 'Escape:27' or
        event == '+' or event == '-') and mode == 'j':
    cx,cy=img_temp.center
    if(event == 'Left:37'):
      cx-=1
    if(event == 'Up:38'):
      cy-=1
    if(event == 'Right:39'):
      cx+=1
    if(event == 'Down:40'):
      cy+=1
    if(event == '+'):
      img_temp.radius+=1
    if(event == '-'):
      img_temp.radius-=1
    img_temp.center=(cx,cy)
    backup_img=current_img
    if(event == 'Escape:27'):
      mode='None'
      current_img=img_temp.draw_box(backup_img,params)
      val=(img_temp.center[0],img_temp.center[1],img_temp.radius)
      msg='Status: Template at (%d,%d) with radius %d' % val
      img_temp.extract(r[index].data,params)
    else:
      current_img=img_temp.draw_circle(backup_img,params)
      msg='Status: Use arrow keys to move, +/- to change size, and ESC to set and exit'
    funcs.draw_image(graph,current_img,params)
    stext.Update(value=msg)
    current_img=backup_img
  elif event == '-GRAPH-' and mode == 'a' and opened and r[index].loaded:
    mode='None'
    pos=params.get_pos(values['-GRAPH-'])
    if(r[index].add_hole(pos,params)):
      msg='Status: Added a hole at (%.1f,%.1f)' % (pos[0],pos[1])
      print(msg)
      stext.Update(value=msg)
    else:
      msg='Status: Not added at (%.1f,%.1f)' % (pos[0],pos[1])
      print(msg)
      stext.Update(value=msg)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    funcs.draw_image(graph,current_img,params)
  elif event == '-GRAPH-' and mode == 'd' and opened and r[index].loaded:
    mode='None'
    pos=params.get_pos(values['-GRAPH-'])
    if(r[index].delete_hole(pos,params)):
      msg='Status: Deleted a hole at (%.1f,%.1f)' % (pos[0],pos[1])
      print(msg)
      stext.Update(value=msg)
    else:
      msg='Status: Not deleted at (%.1f,%.1f)' % (pos[0],pos[1])
      print(msg)
      stext.Update(value=msg)
    if(r[index].detected):
      current_img=funcs.draw_circles(r[index].data,r[index].holes,params)
      if(r[index].grouped):
        current_img=funcs.draw_groups(current_img,r[index].glist,
                                      r[index].gcrd,r[index].holes,params)
    funcs.draw_image(graph,current_img,params)
  elif event == '-GRAPH-+UP' and (mode == 't' or mode == 'z') and opened:
    mouse_x0=-1
    mouse_y0=-1
  elif event == 'MouseWheel:Down' and opened and r[index].loaded:
    params.zoom(1.1,params.xsize*0.5,params.ysize*0.5)
    funcs.draw_image(graph,current_img,params)
  elif event == 'MouseWheel:Up' and opened and r[index].loaded:
    params.zoom(1/1.1,params.xsize*0.5,params.ysize*0.5)
    funcs.draw_image(graph,current_img,params)

if opened:
  mrc.close()
window.close()
