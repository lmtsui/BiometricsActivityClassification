import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class SpecChunk:

    # Will load all protocol data and no optional data by default
    # Set process=True will further complete the data processing
    def __init__(self, protocolList=None, optionalList=None, process=False):
        self.pList = protocolList
        self.oList = optionalList
        self.colName = ['timestamp', 'activityID', 'heart_rate', 'hand_temp', 'hand_acc16g_x', 'hand_acc16g_y', 'hand_acc16g_z', 'hand_acc6g_x', 'hand_acc6g_y', 'hand_acc6g_z', 'hand_gyro_x', 'hand_gyro_y', 'hand_gyro_z', 'hand_mag_x', 'hand_mag_y', 'hand_mag_z', 'hand_ori_0', 'hand_ori_1', 'hand_ori_2', 'hand_ori_3', 'chest_temp', 'chest_acc16g_x', 'chest_acc16g_y', 'chest_acc16g_z', 'chest_acc6g_x', 'chest_acc6g_y', 'chest_acc6g_z', 'chest_gyro_x', 'chest_gyro_y', 'chest_gyro_z', 'chest_mag_x', 'chest_mag_y', 'chest_mag_z', 'chest_ori_0', 'chest_ori_1', 'chest_ori_2', 'chest_ori_3', 'ankle_temp', 'ankle_acc16g_x', 'ankle_acc16g_y', 'ankle_acc16g_z', 'ankle_acc6g_x', 'ankle_acc6g_y', 'ankle_acc6g_z', 'ankle_gyro_x', 'ankle_gyro_y', 'ankle_gyro_z', 'ankle_mag_x', 'ankle_mag_y', 'ankle_mag_z', 'ankle_ori_0', 'ankle_ori_1', 'ankle_ori_2', 'ankle_ori_3']
        self.actDict = {}
        
        if protocolList:
            self.pList = protocolList
        else:
            self.pList = [1,2,3,4,5,6,7,8,9]
            
        proFilePath="PAMAP2_Dataset/Protocol/subject10"+str(self.pList[0])+".dat"
        self.df = pd.read_csv(proFilePath, sep=' ', header=None, names=self.colName)
        for f in self.pList[1:]:
            proFilePath="PAMAP2_Dataset/Protocol/subject10"+str(f)+".dat"
            self.df = self.df.append(pd.read_csv(proFilePath, sep=' ', header=None, names=self.colName))
        
        if optionalList:
            for f in self.oList:
                opFilePath="PAMAP2_Dataset/Optional/subject10"+str(f)+".dat"
                self.df = self.df.append(pd.read_csv(opFilePath, sep=' ', header=None, names=self.colName))
        
        if process:
            print('Removing useless data...')
            self.removeUseless()
            print('Linear Interpolating NaN...')
            self.interpolateNaN()
            print('Removing heads and tails...')
            self.throwAllHeadAndTail()
            
    
    
    def head(self, rowNum=5):
        self.df.head(rowNum)
        
        
    def tail(self, rowNum=5):
        self.df.head(rowNum)
        
        
    def removeUseless(self):
        self.df = self.df.loc[lambda df: df.activityID>0, :].reset_index(drop=True)
        colToDrop=['hand_acc6g_x', 'hand_acc6g_y', 'hand_acc6g_z', 'hand_ori_0', 'hand_ori_1', 'hand_ori_2', 'hand_ori_3',
               'chest_acc6g_x', 'chest_acc6g_y', 'chest_acc6g_z', 'chest_ori_0', 'chest_ori_1', 'chest_ori_2', 'chest_ori_3', 
               'ankle_acc6g_x', 'ankle_acc6g_y', 'ankle_acc6g_z', 'ankle_ori_0', 'ankle_ori_1', 'ankle_ori_2', 'ankle_ori_3']
        self.df = self.df.drop(colToDrop, axis=1)
        self.colName = list(self.df.columns.values)
        
        
    def interpolateNaN(self, method='linear'):
        self.df = self.df.interpolate(method=method, axis=0).ffill().bfill()
        
        
    def throwAllHeadAndTail(self, dt=10):
        self.actDict = {}
        self.actID = self.df.activityID.unique()
        for a in self.actID:
            self.actDict[a] = self.df.loc[lambda d: d.activityID==a, :].reset_index(drop=True)
            
            # find indices that show timestamp discondinuity:
            tgap = np.where(abs(np.array(self.actDict[a].timestamp[1:])-np.array(self.actDict[a].timestamp[:-1]))>0.015)[0]
            n = dt*100
    
            indToDrop = np.linspace(0, n-1, n)
            for t in range(len(tgap)):
                indToDrop = np.append(indToDrop, np.linspace(tgap[t]-(n-1), tgap[t]+n, 2*n))
            
            # Need to take care of the case like act24. Use np.unique().
            indToDrop = np.unique(np.append(indToDrop, np.linspace(len(self.actDict[a].timestamp)-n, len(self.actDict[a].timestamp)-1, n)).astype(int))

            self.actDict[a] = self.actDict[a].drop(self.actDict[a].index[indToDrop]).reset_index(drop=True)
        
        
    
    
class SegChunk:
    
    def __init__(self, specChunk, duration=5.12, tError=0.05):
        self.parent = specChunk
        self.colName = specChunk.colName
        self.featureName = []
        self.t = int(duration*100)
        self.actID = specChunk.actID
        self.segDict = {}
        self.count = 0
        
        t = int(duration*100)
        print('Segment Counts:')
        for a in specChunk.actID:
            N = len(specChunk.actDict[a])
            db = []
            for i in range(int(N/t)):
                delt = specChunk.actDict[a].timestamp[(i+1)*t-1]-specChunk.actDict[a].timestamp[i*t]
                if ((i+1)*t < N) and (delt<(duration+tError)) and (delt>(duration-tError)):
                    db.append(np.array(specChunk.actDict[a].loc[i*t:(i+1)*t-1, :]))
            
            self.segDict[a] = db
            self.count += len(self.segDict[a])
            print('actID={},\t count={}'.format(a, len(self.segDict[a])))
        print('Total counts=', self.count)
    
    
    def showContour(self, act, index):
        segment = self.segDict[act][index][:, 2:]
        nt, nf = segment.shape
        X, Y = np.meshgrid(np.linspace(0, nt-1, nt), np.linspace(0, nf-1, nf))
        Z = segment.transpose()

        fig = plt.figure(figsize=[8, 5])
        ax = plt.axes(projection='3d')
        ax.contour3D(X, Y, Z, 80, cmap='YlGnBu')
        ax.view_init(50, -35)
        ax.set_xlabel('time')
        ax.set_ylabel('feature')
        ax.set_zlabel('z');
    

    # colList = ['heart_rate', 'hand_temp', 'ankle_mag_x']
    # fName = 'mean'---> will create ['heart_rate_mean', 'hand_temp_mean', 'ankle_mag_x_mean']
    # method = np.mean
    def addSimpleFeature(self, colList, fName, method):
        colIndex = [self.colName[i] in colList for i in range(len(self.colName))]
        rawFeatures = np.where(np.array([self.colName[i] in colList for i in range(len(self.colName))])==True)[0]
        self.featureName += [self.colName[rawFeatures[i]]+'_'+fName for i in range(len(rawFeatures))]
        for a in self.actID:
            for i in range(len(self.segDict[a])):
                fList = []
                for c in range(len(self.colName)):
                    if colIndex[c]:
                        fList.append(method(self.segDict[a][i][:, c]))
                    else:
                        fList.append(None)
                self.segDict[a][i] = np.vstack((self.segDict[a][i], fList))
        
        
    ### Flatten all segment chunks in segDict
    # self.segDict is still a dictionary, but the value w.r.t each key is a list of 1D np.array instead of 2D array
    def flatten(self):
        for a in self.actID:
            n = len(self.segDict[a])
            self.segDict[a] = [np.array(list(filter(None, self.segDict[a][i].flatten('F')))) for i in range(n)]
        
   
    