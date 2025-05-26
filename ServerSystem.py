# -*- coding: utf-8 -*-
import server.extraServerApi as serverApi
import Config as DB
CF = serverApi.GetEngineCompFactory()
levelId = serverApi.GetLevelId()
eventList = []
def Listen(funcOrStr=None, EN=serverApi.GetEngineNamespace(), ESN=serverApi.GetEngineSystemName()):
    def binder(func):
        eventList.append((EN, ESN, funcOrStr if isinstance(funcOrStr, str)else func.__name__, func))
        return func
    return binder(funcOrStr)if callable(funcOrStr)else binder

class ServerSystem(serverApi.GetServerSystemCls()):
    def __init__(self, namespace, systemName):
        super(ServerSystem, self).__init__(namespace, systemName)
        for EN, ESN, eventName, callback in eventList:
            self.ListenForEvent(EN, ESN, eventName, self, callback)
        self.GlobalSwitch = CF.CreateExtraData(levelId).GetWholeExtraData()['AetherHealthShowGlobalSwitch'] if CF.CreateExtraData(levelId).GetWholeExtraData().has_key('AetherHealthShowGlobalSwitch') else True
        self.FirstPlayer = None
    def GlobalControl(self,data):
        if data['type'] == 'global':
            CF.CreateExtraData(levelId).SetExtraData("AetherHealthShowGlobalSwitch",data['bool'])
            self.GlobalSwitch = data['bool']
            self.CallAllClient('GlobalControl',{'bool':data['bool']})
        elif data['type'] == 'local':
            ExtraData = CF.CreateExtraData(levelId).GetWholeExtraData()
            if ExtraData.has_key('AetherHealthShowGlobalSwitch'):
                if ExtraData['AetherHealthShowGlobalSwitch'] == False:
                    CF.CreateMsg(data['id']).NotifyOneMessage(data['id'], "[系统]房主已关闭全局血量显示", "§r")
                    return
            CF.CreateExtraData(data['id']).SetExtraData("AetherHealthShowLocalSwitch",data['bool'])
            self.CallClient(data['id'],'GlobalControl',{'bool':data['bool']})
    @Listen('ClientEvent', DB.ModName, 'ClientSystem')
    def OnGetClientEvent(self, data):
        data['funcdata']['__id__'] = data['__id__']
        getattr(self, data['funcName'])(data['funcdata'])
    def CallClient(self, playerId, funcName, funcdata):
        self.NotifyToClient(playerId, 'ServerEvent', {'funcName': funcName, 'funcdata': funcdata})
    def CallAllClient(self, funcName, funcdata):
        self.BroadcastToAllClient('ServerEvent', {'funcName': funcName, 'funcdata': funcdata})
    @Listen
    def AddServerPlayerEvent(self,data):
        if not self.FirstPlayer:
            self.FirstPlayer = data['id']
    @Listen
    def ClientLoadAddonsFinishServerEvent(self,data):
        ExtraData = CF.CreateExtraData(levelId).GetWholeExtraData()
        if ExtraData.has_key('AetherHealthShowGlobalSwitch'):
            if ExtraData['AetherHealthShowGlobalSwitch'] == False:
                self.CallClient(data['playerId'],'GlobalControl',{'bool':False})
                return
        ExtraData = CF.CreateExtraData(data['playerId']).GetWholeExtraData()
        if ExtraData.has_key('AetherHealthShowLocalSwitch'):
            self.GlobalControl({'bool':ExtraData['AetherHealthShowLocalSwitch'],'type':'local','id':data['playerId']})
    @Listen
    def CommandEvent(self,data):
        id = data['entityId']
        if data['command'] == '/on hs':
            data['cancel'] = True
            self.GlobalControl({'bool':True,'type':'local','id':id})
        elif data['command'] == '/off hs':
            data['cancel'] = True
            self.GlobalControl({'bool':False,'type':'local','id':id})
        elif data['command'] == '/on alhs':
            data['cancel'] = True
            if id == self.FirstPlayer:
                self.GlobalControl({'bool':True,'type':'global'})
                CF.CreateMsg(id).NotifyOneMessage(id, "[系统]已开启全局血量显示", "§r")
            else:
                CF.CreateMsg(id).NotifyOneMessage(id, "[系统]您没有权限使用此指令", "§r")
        elif data['command'] == '/off alhs':
            data['cancel'] = True
            if id == self.FirstPlayer:
                self.GlobalControl({'bool':False,'type':'global'})
                CF.CreateMsg(id).NotifyOneMessage(id, "[系统]已关闭全局血量显示", "§r")
            else:
                CF.CreateMsg(id).NotifyOneMessage(id, "[系统]您没有权限使用此指令", "§r")
    def GetCanSee(self,data):
        if not self.GlobalSwitch:
            return
        
        self.CallClient(data['__id__'],
                            'NeedCreateEntities',
                            {'entityList': data.get('entityList', [])}
        )