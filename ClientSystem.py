# -*- coding: utf-8 -*-
import client.extraClientApi as clientApi
import Config as DB
CF = clientApi.GetEngineCompFactory()
PID = clientApi.GetLocalPlayerId()
levelId = clientApi.GetLevelId()
CreateGame = CF.CreateGame(levelId)
eventList = []
comp = CF.CreateTextBoard(levelId)
EntityTypeEnum = clientApi.GetMinecraftEnum().EntityType
GetPos = CF.CreatePos(PID).GetPos
EntityBlackList = ("xj_3d_item:item_3d","xj_3d_item:item_3d_armor","xj_3d_item:item_3d_block","xj_3d_item:item_3d_tool",'minecraft:fishing_hook','minecraft:area_effect_cloud','minecraft:ender_crystal','minecraft:painting','minecraft:lightning_bolt','minecraft:eye_of_ender_signal','minecraft:xp_orb','minecraft:tnt','minecraft:boat','minecraft:leash_knot','minecraft:falling_block','minecraft:fireworks_rocket','minecraft:npc','minecraft:armor_stand','minecraft:item','netease:pet')
def Listen(funcOrStr=None, EN=clientApi.GetEngineNamespace(), ESN=clientApi.GetEngineSystemName()):
    def binder(func):
        eventList.append((EN, ESN, funcOrStr if isinstance(funcOrStr, str)else func.__name__, func))
        return func
    return binder(funcOrStr)if callable(funcOrStr)else binder
class ClientSystem(clientApi.GetClientSystemCls()):
    def __init__(self, namespace, systemName):
        super(ClientSystem, self).__init__(namespace, systemName)
        for EN, ESN, eventName, callback in eventList:
            self.ListenForEvent(EN, ESN, eventName, self, callback)
        self.GlobalSwitch = True
        self.timer = 0
        self.NeedCreate = []
        self.Created = {}
        self.OnRiding = set()

    @Listen
    def LoadClientAddonScriptsAfter(self,data):
        self.aether_ads = clientApi.GetSystem('aether_ads', "ClientSystem")
        if self.aether_ads:
            self.aether_ads.register_ad('《AI山海经》已重磅上线！','textures/aether_ads/classic_of_mountains_and_seas','4679741281933611555')

    def GlobalControl(self,data):
        self.GlobalSwitch = data['bool']
        if data['bool'] == True:
            CF.CreateTextNotifyClient(levelId).SetLeftCornerNotify("[系统]已开启血量显示")
        else:
            CF.CreateTextNotifyClient(levelId).SetLeftCornerNotify("[系统]已关闭血量显示")
            for x in self.Created:
                comp.RemoveTextBoard(self.Created[x])
            self.NeedCreate = []
            self.Created = {}
    @Listen('ServerEvent', DB.ModName, 'ServerSystem')
    def OnGetServerEvent(self, data):
        getattr(self, data['funcName'])(data['funcdata'])
    def CallServer(self, funcName, funcdata):
        self.NotifyToServer('ClientEvent', {'funcName': funcName, 'funcdata': funcdata})
    @Listen
    def UiInitFinished(self, data):
        if self.GlobalSwitch == True:
            self.NeedCreate = []
            Created2 = self.Created.copy()
            for x in Created2:
                comp.RemoveTextBoard(self.Created[x])
                del self.Created[x]
    def Update(self):
        if self.GlobalSwitch == True:
            self.timer +=1
            if self.timer == 5:
                self.timer = 0
                x,y,z = GetPos()
                entityList = []
                for x in CreateGame.GetEntitiesInSquareArea(None, (x-24,y-24,z-24), (x+24,y+24,z+24)):
                    if x != PID and CF.CreateEngineType(x).GetEngineTypeStr() not in EntityBlackList:
                        entityType = CF.CreateEngineType(x).GetEngineType()
                        inBlackList = False
                        for Type in ('Minecart','Projectile','AbstractArrow'):
                            if entityType & getattr(EntityTypeEnum, Type) == getattr(EntityTypeEnum, Type):
                                inBlackList = True
                                break
                        if inBlackList != True:
                            entityList.append(x)
                self.CallServer('GetCanSee',{'entityList':entityList})
    def NeedCreateEntities(self,data):
        if not self.GlobalSwitch:
            return
        
        raw_list = data.get('entityList', [])
        filtered = []

        for eid in raw_list:
            if not CreateGame.CanSee(
                PID,
                eid,
                25.0,
                True,
                180.0,
                180.0
            ):
                continue

            effects = CF.CreateEffect(eid).GetAllEffects() or []
            if any(e.get('effectName') == 'invisibility' for e in effects):
                continue

            filtered.append(eid)

        for old_eid in list(self.Created):
            if old_eid not in filtered or old_eid in self.OnRiding:
                comp.RemoveTextBoard(self.Created[old_eid])
                del self.Created[old_eid]

        self.NeedCreate = filtered
        self.CreateText(filtered)
    def CreateText(self,data):
        if self.GlobalSwitch == True:
            if len(data) > 0:
                if self.Created.has_key(data[0]) or data[0] in self.OnRiding:
                    y = CF.CreateCollisionBox(data[0]).GetSize()[1]
                    if data[0] not in self.OnRiding:
                        if CF.CreateEngineType(data[0]).GetEngineTypeStr() != 'minecraft:player':
                            comp.SetBoardPos(self.Created[data[0]], (0.0, y+0.3, 0.0))
                    self.NeedCreate.remove(data[0])
                    self.CreateText(self.NeedCreate)
                    return
                health = str(CF.CreateAttr(data[0]).GetAttrValue(0)).split('.')
                maxHealth = str(CF.CreateAttr(data[0]).GetAttrMaxValue(0))
                text = '  '+health[0]+'.'+health[1][:1]+'/'+maxHealth+''
                boardId = comp.CreateTextBoardInWorld(text,(1,1,1,1),(0,0,0,0))
                self.Created[data[0]] = boardId
                y = CF.CreateCollisionBox(data[0]).GetSize()[1]
                comp.SetBoardBindEntity(boardId, data[0], (0,y+0.3,0),(0,0,0))
                if CF.CreateEngineType(data[0]).GetEngineTypeStr() == 'minecraft:player':
                    comp.SetBoardPos(boardId, (0.0, 1.1, 0.0))
                comp.SetBoardDepthTest(boardId, False)
                self.NeedCreate.remove(data[0])
                self.CreateText(self.NeedCreate)
    @Listen
    def StartRidingClientEvent(self,data):
        if self.GlobalSwitch == True:
            if data['actorId'] == PID:
                self.OnRiding.add(data['victimId'])
            elif data['victimId'] == PID:
                self.OnRiding.add(data['actorId'])
    @Listen
    def EntityStopRidingEvent(self,data):
        if self.GlobalSwitch == True:
            if data['id'] == PID and data['rideId'] in self.OnRiding:
                self.OnRiding.remove(data['rideId'])
            elif data['rideId'] == PID and data['id'] in self.OnRiding:
                self.OnRiding.remove(data['id'])
    @Listen
    def HealthChangeClientEvent(self,data):
        if self.GlobalSwitch == True:
            if self.Created.has_key(data['entityId']):
                health = str(data['to']).split('.')
                maxHealth = str(CF.CreateAttr(data['entityId']).GetAttrMaxValue(0))
                text = '  '+health[0]+'.'+health[1][:1]+'/'+maxHealth+''
                comp.SetText(self.Created[data['entityId']],text)
    @Listen
    def RemoveEntityClientEvent(self,data):
        if self.Created.has_key(data['id']):
            del self.Created[data['id']]
        