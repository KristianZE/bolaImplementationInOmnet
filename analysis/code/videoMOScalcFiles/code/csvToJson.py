
import numpy as np
import pandas as pd
import matplotlib

from matplotlib import pyplot as plt

import json
import os
import math
import os.path

import sys


# ### Each of them contains the following five vector
# - DASHBufferLength - this is the "current" (according to the timestamp) length of the video present in the Video Client buffer in seconds
# - DASHVideoPlaybackPointer - this represents how many seconds of the video has been played back until "now" (the time-stamp time in the simulation)
# - DASHQualityLevel - this is video quality /Bitrate in kbits/s in which the last video segment has been downloaded
# - DASHVideoPlaybackStatus - this is the playback status of the video. It is logged only on changes (when the video is paused or the playback is resumed)! 1=started playing, 0=stopped playing
# - DASHReceivedBytes - this value represents how many Bytes were downloaded for the last video segment
# 
# ### Each vector consists of two "columns"
# - The first column is the time-stamp (when the value has been taken according to the simulation time)
# - The second column has the value
# 
# --------------------
# Note
# - tsPlaybackPointer is the experiment time
# - PlaybackPointer is the video time
# - tsReceivedBytes is the experiment time
# 
# ### setting.csv
# - VL: video duration
# - SL: segment length
# - MBL: max length of video buffer

''' rename the columns in the dataset & construct the video segments in I13
input: each dataset, DataFrame 
output:
'''
def get_segmentsInfo(ds,seglen,file):    
    #the actual video length in video time
    VL=ds.dropna(subset=['PlaybackPointer'])['PlaybackPointer'].values[-1]
#     VL=ds['PlaybackPointer'].dropna().iloc[-1]

    tmp=ds.dropna(subset=['QualityLevel']) #remove the rows which has NaN in the column 'QualityLevel'
    # the video is not finished : the last ones (the last start of segment) in column 'QualityLevel' might be stored in the buffer instead of played, so just skip it
    # the video is finished : skip the first line of bitrate
    segs_num=int(np.ceil(VL/seglen)) #the number of actual played segments
    tmp=tmp.iloc[1:segs_num+1] #mainly for the bitrate selection 
    
    tmp['start']=np.arange(0,VL,seglen)
    tmp = tmp.rename(columns={'QualityLevel':'bitrate'})
    #'start' # when did the video segment start,media start timestamp in s
    #'bitrate' #the video bitrate of the specific segment (i.e. the quality level),bitrate in kBit/s
    tmp['resolution']='1280x720' # resolution as "widthxheight", can keep it fix to 1280x720
    tmp['codec']='h264' # only "h264" supported in standard
    tmp['fps']=24.0 ## framerate,keep it fix to 24
    tmp['duration']=seglen #segment length,is the same for each segment,duration in s
    #the duration of the last segment
    if VL%seglen==0:
        tmp['duration'].values[-1]=seglen
    else:
        tmp['duration'].values[-1]=VL%seglen

        '''
        "representation": 1,   # representation ID / media quality level ID (optional)

        "frames": [
        # optional list of frames
        # when present, will enable modes 1, 2 or 3
        ]
        '''
        #construct the video segments in I13
    col_n = ['resolution','start','bitrate','codec','fps','duration']
    df = pd.DataFrame(tmp,columns = col_n)

    #loads here is used to convert str to list
    seg=json.loads(df.to_json(orient='records')) 

    return seg


# In[3]:


'''get the stalling information for I23
    
input: each dataset, DataFrame 
return : stalling is pair of `[start timestamp, duration]` for each stalling event
        where the start timestamp is measured in media time
'''
def get_stalling(ds):
    #set the frist stalling event which start at 0
    ds['tsPlaybackStatus'].values[0]=0

    idx=ds['tsPlaybackPointer'].isin(ds['tsPlaybackStatus'][ds['PlaybackStatus']==0])

    st=ds['PlaybackPointer'][idx] # start timestamp in video time

    tmp=ds.dropna(subset=['tsPlaybackStatus'])
    
    a=tmp['tsPlaybackStatus'].iloc[1::2]
    b=tmp['tsPlaybackStatus'].iloc[::2]

    if (len(a)+1)==len(b):
        #delete the last line of tsPlaybackStatus since the status of this row is 0 and it represents the end of the video
        #It's useless for the information about stalling
        b=b.drop(b.index[len(b)-1]) 
        st=st.drop(st.index[len(st)-1]) #except for the last one which is the end of the video

    # if the last line of tsPlaybackStatus is 1, it means the video is interrupted
    durations=a.values-b.values #duration, numpy
    st=st.values

    # print('number of stallings:',len(durations),', total stalling duration: ',durations.sum())

    stalling=np.vstack((st,durations)).T.tolist()
    
    return stalling


# In[4]:


'''Construct dict and dump it into JSON file
Input seg: list of video segments
      stall: list set
       
'''
def saveJson(seg,stall,streamID,filename):
    # Audio input information
    i11={"segments": {}}
    
    # video input information
    i13={
        "segments":seg, # list of video segments
        "streamId":streamID # unique identifier for the stream
    }
    
    #Generic input information
    iGen={
        "displaySize": "1280x720", # display resolution in pixels, given as `<width>x<height>`
        "device": "pc", # pc or mobile, default: "pc"
        "viewingDistance": "150cm" # not used
    }
    
    #Stalling input information
    i23={
        "streamId":streamID, #unique identifier for the stream
         #stalling is pair of `[start timestamp, duration]` for each stalling event
         # where the start timestamp is measured in media time
         "stalling":stall
    }

    dic={'I11':i11, 'I13':i13, 'IGen':iGen,'I23':i23}
    with open(filename, 'w+') as outfile:
        json.dump(dic,outfile,sort_keys=False, indent=4, separators=(',', ':'))


# In[5]:


'''read files from the folder in turn and dump to the corresponding JSON input files
Input:foldername
Output: the corresponding JSON_Formatted files
'''
def toJson(input_file,output_file, name):
    streamID=0
    #threshold, the minimum played video duration
    #If the played video time is lower than this, just ignored
    threshold=15
    seglen=5 #segment length
    ds=pd.read_csv(input_file)
    #rename the columns in the dataset
    ds.columns=['tsBufferLength','BufferLength','tsReceivedBytes','ReceivedBytes','tsQualityLevel','QualityLevel','tsPlaybackPointer','PlaybackPointer','tsPlaybackStatus','PlaybackStatus']
    # print('\n' + ds.to_string())
    initialTime = ds['tsPlaybackPointer'].values[0]
    ds['tsBufferLength'] = ds['tsBufferLength'] - initialTime
    ds['tsReceivedBytes'] = ds['tsReceivedBytes'] - initialTime
    ds['tsQualityLevel'] = ds['tsQualityLevel'] - initialTime
    ds['tsPlaybackPointer'] = ds['tsPlaybackPointer'] - initialTime
    ds['tsPlaybackStatus'] = ds['tsPlaybackStatus'] - initialTime

    if ds['PlaybackPointer'].dropna().iloc[-1]>=threshold:
        #segment length or called duration in segment, is the same for each segment
#                 seglen=setting[setting['Client']==file[:-4]]['SL'].values[0]           
        seg=get_segmentsInfo(ds,seglen,name) #list of video segments
        stall=get_stalling(ds) #list of stalling information
        savefname=output_file
        saveJson(seg,stall,streamID,savefname)
        streamID+=1
    else:
        print(name,end=' ')
        # just store the file name which played video time is lower than the threshold


# In[6]:


if __name__ == "__main__":
    print('CSV to JSON translation for ', end='')
    input_file=sys.argv[1]
    output_file=sys.argv[2]
    name = sys.argv[3]
    print(name, end=' processing... ')
    toJson(input_file,output_file,name)
    print('Done!')

