import yaml
import re
class ModuleFind:
    def classInModule(self, repo_path, mdl, cls):
        mdl_path = str(mdl).replace(repo_path + "/", "").strip("module-info.java")  # remove local repo dir part
        if (mdl_path in cls):
            return True
        return False

    def onlyModPart(self,mdl):
        if ("/src/main/java/" in mdl):
            return mdl.split("/src/main/java/")[0]
        elif ("/src/main/kotlin/" in mdl):
            return mdl.split("/src/main/kotlin/")[0]
        elif ("/main/java/" in mdl):
            return mdl.split("/main/java/")[0]
        elif ("/src/" in mdl):
            return mdl.split("/src/")[0]
        else:
            return mdl
    def findModuleFor(self, module_names, class_dir):
        mod_name = None
        to_search = class_dir.split("/src/")[0] + "/src/"
        to_search2 = class_dir.split("/main/java/")[0] + "/main/java/"
        to_search3 = class_dir.split("/src/main/java/")[0] + "/src/main/java/"
        # print(to_search)
        for mdl in module_names:
            if (to_search in mdl or to_search2 in mdl or to_search3 in mdl):
                return mdl
        return None
    def stripFileExtension(self, name):
        return name.replace("module-info.java","").replace(".java","").replace(".kt", "")

    def findImportFor(self, module_names, imprt):
        found = []
        # print(to_search)
        for mdl in module_names:
            if("test/" in mdl):
                continue
            if("." in mdl):
                mdl = mdl.replace(".","/")
            if (imprt in mdl):
                parts = mdl.split(imprt)

                if(len(parts) == 1 or parts[1]==""):
                    if("/src/main/java/" in mdl):
                        return mdl.split("/src/main/java/")[0]
                    elif("/main/java/" in mdl):
                        return mdl.split("/main/java/")[0]
                    elif("/src/main/kotlin/" in mdl):
                        return mdl.split("/src/main/kotlin/")[0]
                    elif("/src/" in mdl):
                        return mdl.split("/src/")[0]

        return None

    def selfModuleNameCheck(self,imprt, in_file_names=dict(), self_name=None):
        mod_name = in_file_names.get(imprt)
        if(mod_name == self_name):
            print(mod_name)
            return mod_name
        else:
            return None

    def newFindImport(self, module_names, imprt, in_file_names=dict(), self_name=None):
        found = dict()
        if(imprt is None):
            return None
        # print(to_search)
        name_keys=list(in_file_names.keys())
        if(len(name_keys)>0):
            for name_ky in name_keys:
                if(imprt == name_ky):
                    mdl = in_file_names.get(name_ky)
                    return mdl
        for mdl in module_names:
            if("test/" in mdl):
                continue
            if("." in mdl):
                mdl = mdl.replace(".","/")
            if (imprt in mdl):

                if("/src/main/java/" in mdl):
                    found[mdl.split("/src/main/java/")[0]]=mdl
                elif("/main/java/" in mdl):
                    found[mdl.split("/main/java/")[0]]=mdl
                elif("/src/main/kotlin/" in mdl):
                    found[mdl.split("/src/main/kotlin/")[0]]=mdl
                elif("/src/" in mdl):
                    found[mdl.split("/src/")[0]]=mdl
        if(found==dict()):
            return None
        else:
            solid_match = False
            solid_module=None
            doubt_module = None
            for fnd_key in found.keys():
                mdl = found[fnd_key]
                try:
                    parts = mdl.split(imprt)
                except Exception as e:
                    print('probably empty imprt')
                    return None

                if(len(parts) == 1 or parts[1]==""):
                    solid_module= fnd_key
                    solid_match = True
                else:
                    doubt_module = fnd_key
            if(solid_match):
                return solid_module
            else:
                return doubt_module
        return None
    def termVariationMatching(self, term, code):
        term = term.strip(" ")
        term1 = term + " "
        term2 = term + "."
        term3 = term + ")"
        term4 = term + ">"
        term5 = term + "("
        if (term in code or term1 in code or term2 in code or term3 in code or term4 in code or term5 in code):
            return True

    def importToClass(self, imprt):
        class_part = imprt.replace('+','').replace('import ','').replace('-','').replace(";",'').split('.')
        reformed = "/".join(class_part[:len(class_part)])
        return reformed
    #TODO- return from aa.bb.cc to aa/bb/
    def importReformation(self, imprt):
        class_part = imprt.replace('+','').replace('import ','').replace('-','').replace(";",'').replace("static ","").split('.')
        if(len(class_part)<2):
            return class_part[0]
        if("static " in imprt): # static import only method
            reformed = "/".join(class_part[:len(class_part) - 2])
        else:
            reformed = "/".join(class_part[:len(class_part) - 1])
        return reformed

    # TODO- return from aa.bb.cc to aa/bb/cc
    def importFullReformation(self, imprt):
        class_part = imprt.replace('+','').replace('import ','').replace('-','').replace(";",'').replace("static ","").split('.')
        if (len(class_part) < 2):
            return class_part[0]
        if("static " in imprt): # static import only method
            reformed = "/".join(class_part[:len(class_part) - 1])
        else:
            reformed = "/".join(class_part[:len(class_part)])
        return reformed

class ChangeRelation(ModuleFind):
    CONNECT="connect" #TODO-- probably JPMS connect
    DISCONNECT="disconnect" #TODO--probably JPMS disconnect
    MO_ADD = "mo_add"
    MO_DELETE = "mo_delete"
    KEY_CONNECT="_"+CONNECT
    KEY_DISCONNECT="_"+DISCONNECT
    KEY_API="<<API>>"
    KEY_METHOD="methods"
    KEY_ADDED_CLS="added_class"
    KEY_DELETED_CLS="deleted_class"
    KEY_MODIFIED_CLS="modified_class"
    KEY_NOT_M2M="not_in_m2m"

    def __init__(self):

        self.id = None
        self.modules = []
        self.all_modules = [] # all the modules in the project directory
        self.all_packages=[] # packages are primarliy used for searching modules
        self.module_names = []
        self.module_names_in_file = dict() # module name within module-info.java file: module_name --> module relative directory
        self.repo_path=None
        self.n_modules=[]
        self.n_only_connect_mo = [] #TODO- considers only module-info.java
        self.n_only_disconnect_mo = [] #TODO- considers only module-info.java
        self.n_m2m_classes= []
        self.n_non_m2m_classes= []
        self.n_connected_classes=[]
        self.n_disconnected_classes=[]
        self.n_connected_modules=[]
        self.n_connected_api=[]
        self.n_disconnected_api=[]
        self.n_disconnected_modules=[]
        self.n_new_methods = []
        self.n_new_methods_api = []
        self.n_deleted_methods=[]
        self.n_deleted_methods_api=[]
        self.total_m2m=0
        self.total_non_m2m = 0
        self.total_deleted_cls = 0
        self.total_added_cls = 0
        self.total_modified_cls = 0
        self.contain_only_add_mthd= 0
        self.contain_only_delete_mthd=0
        self.contain_add_delete_mthd = 0
        self.contain_only_add_mthd_with_api = 0
        self.contain_only_delete_mthd_with_api = 0
        self.contain_add_delete_mthd_with_api = 0
        self.modify_connect = 0
        self.modify_disconnect = 0
        self.n_add_mo = 0
        self.n_delete_mo = 0
    def setModuleNameInFile(self, names):
        self.module_names_in_file = names
    def getNModuleSize(self):
        return len(self.n_modules)
    def getNM2MClsSize(self):
        return len(self.n_m2m_classes)
    def getNonM2MClsSize(self):
        return len(self.n_non_m2m_classes)
    def getConnectClsSize(self):
        return len(self.n_connected_classes)
    def getDisconnectClsSize(self):
        return len(self.n_disconnected_classes)
    def getConnectModSize(self):
        return len(self.n_connected_modules)
    def getDisConnectModSize(self):
        return len(self.n_disconnected_modules)
    def getConnectMOSize(self): #TODO- considers only module-info.java
        return len(self.n_only_connect_mo)
    def getDisConnectMOSize(self): #TODO- considers only module-info.java
        return len(self.n_only_disconnect_mo)
    def getConnectApiSize(self):
        return len(self.n_connected_api)
    def getDisConnectApiSize(self):
        return len(self.n_disconnected_api)
    def getNewMthdSize(self):
        return len(self.n_new_methods)
    def getDeletMthdSize(self):
        return len(self.n_deleted_methods)
    def getNewAPIMthdSize(self):
        return len(self.n_new_methods_api)
    def getDeletAPIMthdSize(self):
        return len(self.n_deleted_methods_api)
    def getAddDeletAPIMthdSize(self):
        return self.contain_add_delete_mthd_with_api
    def getAddDeletMthdSize(self):
        return self.contain_add_delete_mthd
    def setProjectRoort(self,proot):
        self.repo_path = proot
    def setId(self,id):
        self.id = id
    def addModule(self, mod):
        self.modules.append(mod)
    def getModuleName(self):
        self.module_names = self.all_modules
    def allModules(self,mods):
        self.all_modules = mods
    def allPackages(self,packs):
        self.all_packages = packs
    # find the module of a relevent class

    def extendsPacDirs(self,dirs):
        self.all_packages.extend(dirs)
    def findModlOfCls(self, cls):
        for mdl in self.all_modules:
            mdl_path = str(mdl).replace(self.repo_path + "/", "").replace("module-info.java","")  # remove local repo dir part
            if (mdl_path in cls):
                return mdl_path +"module-info.java"
        return None
    def findPackageOfCls(self, cls):
        for mdl in self.all_packages:
            mdl_path = str(mdl).replace(self.repo_path + "/", "").replace("module-info.java","")  # remove local repo dir part
            if (mdl_path in cls):
                return mdl_path +"module-info.java"
        return None
    def analyze(self):
        self.getModuleName()
        for module in self.modules:
            #Make sure that project root is set
            #TODO--find module connection for module-info.java
            #TODO -- find module connection for all modified classes based on import modification
            #TODO -- determine whenther a class is involved in M2M
            #TODO -- find added or deleted methods that contain modified imports
            module.getPackages(self.all_packages)
            if(len(module.ops_add)>0 or len(module.ops_delete)>0):
                module.setTemporaryModnameInFile(self.module_names_in_file)
                module.findModuleConnection(self.repo_path, self.all_packages)
            all_classes = module.added_classes + module.deleted_classes + module.modified_classes
            if(len(all_classes)>0):
                for cls in all_classes:

                    if(len(cls.import_added+cls.import_deleted)>0):
                        cls.findModuleConnection(self.repo_path, module.packages, self.all_packages)
                        cls.importInModifiedMethods()
    def saveAnalysisToYaml(self, data_path):
        all_data = []
        for jpmsmod in self.modules:

            #TODO --print a module
            #TODO -- print an added class
            #TODO-- print a connected module of that class along with impacted classes
            #TODO-- print a deleted class
            # TODO-- print a diconnected module of that class along with impacted classes
            #TODO-- print a modified class
            #TODO -- print added methods impacted with import added
            #TODO-- print connected module with added import [along with impacted classes]
            # TODO -- print deleted methods impacted with import deleted
            # TODO-- print disconnected module with deleted import [along with impacted classes]
            # TODO --  print no-involved M2M class

            modl = []
            if("ADD" in list(jpmsmod.getChangeTypes())):
                modl.append({ChangeRelation.MO_ADD:"only_add"})
            if("DELETE" in list(jpmsmod.getChangeTypes())):
                modl.append({ChangeRelation.MO_DELETE:"only_delete"})
            if(len(jpmsmod.connected_modules.keys())>0):
                modl.append({ChangeRelation.CONNECT: dict(jpmsmod.connected_modules)})
            if (len(jpmsmod.disconnected_modules.keys()) > 0):
                modl.append({ChangeRelation.DISCONNECT: dict(jpmsmod.disconnected_modules)})

            add_data = []
            if(len(jpmsmod.added_classes)>0):
                for cls in jpmsmod.added_classes:
                    connection = []
                    if(len(cls.import_in_add_methods) <1):
                        connection = cls.connected
                    else:
                        connection = [{ChangeRelation.KEY_METHOD:cls.import_in_add_methods}, cls.connected]

                    add_data.append({cls.full_name: {ChangeRelation.KEY_CONNECT: connection}})
                modl.append({ChangeRelation.KEY_ADDED_CLS:add_data})

            delete_data = []
            if(len(jpmsmod.deleted_classes)>0):
                for cls in jpmsmod.deleted_classes:
                    disconnection = []
                    if(len(cls.import_in_delete_methods) <1):
                        disconnection = cls.disconnected
                    else:
                        disconnection = [{ChangeRelation.KEY_METHOD:cls.import_in_delete_methods}, cls.disconnected]
                    delete_data.append({cls.full_name: {ChangeRelation.KEY_DISCONNECT: disconnection}})
                modl.append({ChangeRelation.KEY_DELETED_CLS: delete_data})
            modified_data = []
            if (len(jpmsmod.modified_classes) > 0):
                for cls in jpmsmod.modified_classes:
                    if(len(cls.connected.keys())>0):
                        connection = []
                        if (len(cls.import_in_add_methods) <1):
                            connection = cls.connected
                        else:
                            connection = [{ChangeRelation.KEY_METHOD: cls.import_in_add_methods}, cls.connected]
                        modified_data.append({self.stripFileExtension(cls.full_name):{ChangeRelation.KEY_CONNECT: connection}})
                    if (len(cls.disconnected.keys()) > 0):
                        disconnection = []
                        if (len(cls.import_in_delete_methods) < 1):
                            disconnection = cls.disconnected
                        else:
                            disconnection = [{ChangeRelation.KEY_METHOD: cls.import_in_delete_methods}, cls.disconnected]
                        modified_data.append({self.stripFileExtension(cls.full_name):{ChangeRelation.KEY_DISCONNECT: disconnection}})
                modl.append({ChangeRelation.KEY_MODIFIED_CLS: modified_data})
                for cls in jpmsmod.modified_classes:
                    if(cls.involved_in_m2m==False):
                        modl.append({ChangeRelation.KEY_NOT_M2M: cls.full_name})
            all_data.append({jpmsmod.full_name:modl})

        with open(data_path, 'w') as outfile:
            yaml.dump(all_data, outfile, default_flow_style=False)

    def changeInstanceCount(self):
        all_data = []
        for jpmsmod in self.modules:

            #TODO--count modules involved
            #TODO -- count m2m classes
            #TODO-- count non-m2m classes
            #TODO-- count connected classes
            #TODO-- count disconnected classes
            #TODO-- count connected modules
            #TODO-- count disconnected modules
            #TODO--count connected API
            #TODO-- count disconnected API
            #TODO-- count new methods
            #TODO-- count deleted methods

            self.n_modules.append(jpmsmod.full_name)
            modl = []
            if("ADD" in list(jpmsmod.getChangeTypes())):
                self.n_add_mo +=1
            if("DELETE" in list(jpmsmod.getChangeTypes())):
                self.n_delete_mo +=1
            if(len(jpmsmod.connected_modules.keys())>0):
                for ky in jpmsmod.connected_modules.keys():
                    if ("<<API>>" in ky):
                        self.n_connected_api.append("<<API>>")
                        self.n_only_connect_mo.append(ky)
                    else:
                        self.n_connected_modules.append(ky)
                        self.n_only_connect_mo.append(ky)
                    con_classes = jpmsmod.connected_modules.get(ky)
                    if (type(con_classes) is list):
                        for con_cls in con_classes:
                            self.n_connected_classes.append(con_cls)
                    else:
                        if(con_classes is not None):
                            self.n_connected_classes.append(con_classes)
            if (len(jpmsmod.disconnected_modules.keys()) > 0):
                for ky in jpmsmod.disconnected_modules.keys():
                    if ("<<API>>" in ky):
                        self.n_disconnected_api.append("<<API>>")
                        self.n_only_disconnect_mo.append(ky)
                    else:
                        self.n_disconnected_modules.append(ky)
                        self.n_only_disconnect_mo.append(ky)
                    dis_classes = jpmsmod.disconnected_modules.get(ky)
                    if(type(dis_classes) is list):
                        for d_cls in dis_classes:
                            self.n_disconnected_classes.append(d_cls)
                    else:
                        if (dis_classes is not None):
                            self.n_disconnected_classes.append(dis_classes)

            add_data = []
            add_len =  len(jpmsmod.added_classes)
            if(add_len>0):
                self.total_added_cls +=add_len
                for cls in jpmsmod.added_classes:
                    connection = []
                    self.n_m2m_classes.append(cls.full_name)
                    if(len(cls.connected.keys())>0):
                        for ky in cls.connected.keys():
                            if("<<API>>" in ky):
                                self.n_connected_api.append("<<API>>")
                            else:
                                self.n_connected_modules.append(ky)
                            con_classes = cls.connected.get(ky)
                            if(type(con_classes) is list):
                                for con_cls in con_classes:
                                    self.n_connected_classes.append(con_cls)
                            else:
                                if(con_classes is not None):
                                    self.n_connected_classes.append(con_classes)

            delete_data = []
            delete_len = len(jpmsmod.deleted_classes)
            if(delete_len>0):
                self.total_deleted_cls +=delete_len
                for cls in jpmsmod.deleted_classes:
                    self.n_m2m_classes.append(cls.full_name)
                    if(len(cls.disconnected.keys())>0):
                        for ky in cls.disconnected.keys():
                            if("<<API>>" in ky):
                                self.n_disconnected_api.append("<<API>>")
                            else:
                                self.n_disconnected_modules.append(ky)
                            con_classes = cls.disconnected.get(ky)
                            if(type(con_classes) is list):
                                for con_cls in con_classes:
                                    self.n_disconnected_classes.append(con_cls)
                            else:
                                if(con_classes is not None):
                                    self.n_disconnected_classes.append(con_classes)
                    if(len(list(cls.import_in_delete_methods))>0):
                        for mthd in list(cls.import_in_delete_methods):
                            self.n_deleted_methods.append(mthd)

            modified_data = []
            modi_len = len(jpmsmod.modified_classes)
            modify_connect = False
            modify_disconnect= False
            if (modi_len > 0):
                self.total_modified_cls += modi_len
                for cls in jpmsmod.modified_classes:
                    has_add_mthd = False
                    has_delete_mthd = False
                    has_add_api = False
                    has_delete_api = False
                    has_add_class = False
                    has_delete_class = False

                    if(cls.involved_in_m2m):
                        self.n_m2m_classes.append(cls.full_name)
                    else:
                        self.n_non_m2m_classes.append(cls.full_name)
                    if(len(cls.connected.keys())>0):
                        modify_connect = True
                        for ky in cls.connected.keys():
                            if("<<API>>" in ky):
                                self.n_connected_api.append("<<API>>")
                            else:
                                self.n_connected_modules.append(ky)
                            con_classes = cls.connected.get(ky)
                            if(type(con_classes) is list):
                                for con_cls in con_classes:
                                    self.n_connected_classes.append(con_cls)
                            else:
                                if(con_classes is not None):
                                    self.n_connected_classes.append(con_classes)
                        if(len(list(cls.import_in_add_methods))>0):
                            has_add_mthd = True
                            for mthd in list(cls.import_in_add_methods):
                                if("<<>>" in mthd): #TODO-- we assume that <<>> indicates API class import and >> indicates usual class import
                                    has_add_api = True
                                    self.n_new_methods_api.append(mthd)
                                else:
                                    has_add_class = True
                                    self.n_new_methods.append(mthd)
                    if(len(cls.disconnected.keys())>0):
                        modify_disconnect = True
                        for ky in cls.disconnected.keys():
                            if("<<API>>" in ky):
                                self.n_disconnected_api.append("<<API>>")
                            else:
                                self.n_disconnected_modules.append(ky)
                            con_classes = cls.disconnected.get(ky)
                            if(type(con_classes) is list):
                                for con_cls in con_classes:
                                    self.n_disconnected_classes.append(con_cls)
                            else:
                                if(con_classes is not None):
                                    self.n_disconnected_classes.append(con_classes)
                        if(len(list(cls.import_in_delete_methods))>0):
                            has_delete_mthd = True
                            for mthd in list(cls.import_in_delete_methods):
                                if("<<>>" in mthd): #TODO-- we assume that <<>> indicates API class import and >> indicates usual class import
                                    has_delete_api = True
                                    self.n_deleted_methods_api.append(mthd)
                                else:
                                    has_delete_class = True
                                    self.n_deleted_methods.append(mthd)

                    if(has_delete_mthd and has_add_mthd):
                        if(has_add_api and has_delete_api):
                            self.contain_add_delete_mthd_with_api +=1
                        else:
                            self.contain_add_delete_mthd +=1
                    # if (has_delete_mthd == False and has_add_mthd == True):
                    #     if (has_add_api):
                    #         self.contain_only_add_mthd_with_api +=1
                    #     else:
                    #         self.contain_only_add_mthd += 1
                    # if (has_delete_mthd == True and has_add_mthd == False):
                    #     if(has_delete_api):
                    #         self.contain_only_delete_mthd_with_api +=1
                    #     else:
                    #         self.contain_only_delete_mthd += 1
            if(modify_connect):
                self.modify_connect +=1
            if(modify_disconnect):
                self.modify_disconnect +=1


    def changeStat(self):
        print("modules:",len(self.n_modules), "classes:", len(self.n_m2m_classes), "non_m2m_classes:", len(self.n_non_m2m_classes), "connected_modules:", len(self.n_connected_modules), "disconected_modules:", len(self.n_disconnected_modules),
              "connect_api:", len(self.n_connected_api), "disconnect_api:", len(self.n_disconnected_api), "connected_cls:", len(self.n_connected_classes), "disconnected_cls:", len(self.n_disconnected_classes), "new_method:",len(self.n_new_methods))
    def totalInstances(self):
        self.total_m2m = len(self.n_modules)+ len(self.n_m2m_classes)+len(self.n_connected_modules)+ len(self.n_disconnected_modules)+len(self.n_connected_api)+len(self.n_disconnected_api)+ len(self.n_connected_classes)\
            +len(self.n_disconnected_classes)+ len(self.n_new_methods) + len(self.n_deleted_methods)
        self.total_non_m2m = len(self.n_non_m2m_classes)
        print("total m2m:", self.total_m2m, "total non m2m:", self.total_non_m2m)

    def yamlChangeElement(self,tag, j_class, connect_info):
        if(connect_info == dict()):
            return
        if(type(connect_info) is dict):
            connect_keys = list(connect_info.keys())
            for connect_key in connect_keys:
                associated_class = connect_info.get(connect_key)
                if(tag == ChangeRelation.KEY_CONNECT):
                    j_class.addConnected(connect_key, associated_class)
                else:
                    j_class.addDisConnected(connect_key, associated_class)
        else:
            for info in connect_info:
                connect_keys = list(info.keys())
                for connect_key in connect_keys:
                    if (ChangeRelation.KEY_METHOD in connect_key):
                        mthds = list(info.get(ChangeRelation.KEY_METHOD))
                        if (tag == ChangeRelation.KEY_CONNECT):
                            j_class.import_in_add_methods.update(mthds)
                        else:
                            j_class.import_in_delete_methods.update(mthds)
                    # elif (ChangeRelation.KEY_API in connect_key):
                    #     associated_class = info.get(ChangeRelation.KEY_API)
                    #     print("     API--", info.get(ChangeRelation.KEY_API))
                    #     j_class.addConnected(connect_key,associated_class)
                    else:
                        associated_class= info.get(connect_key)
                        if (tag == ChangeRelation.KEY_CONNECT):
                            j_class.addConnected(connect_key,associated_class)
                        else:
                            j_class.addDisConnected(connect_key, associated_class)
    def yamlElementForConfig(self,tag, jpms, connect_info):
        if(connect_info == dict() or connect_info is None):
            return
        if(type(connect_info) is dict):
            connect_keys = list(connect_info.keys())
            for connect_key in connect_keys:
                associated_class = connect_info.get(connect_key)
                if(tag == ChangeRelation.CONNECT):
                    jpms.addConnectModule(connect_key,associated_class)
                else:
                    jpms.addDisconnectModule(connect_key,associated_class)
        else:
            for info in connect_info:
                connect_key = list(info.keys())[0]
                if (ChangeRelation.KEY_METHOD in connect_key):

                    mthds = list(info.get(ChangeRelation.KEY_METHOD))
                    if (tag == ChangeRelation.CONNECT):
                        jpms.import_in_add_methods.update(mthds)
                    else:
                        jpms.import_in_delete_methods.update(mthds)
                # elif (ChangeRelation.KEY_API in connect_key):
                #     associated_class = info.get(ChangeRelation.KEY_API)
                #     print("     API--", info.get(ChangeRelation.KEY_API))
                #     j_class.addConnected(connect_key,associated_class)
                else:
                    associated_class= info.get(connect_key)
                    if (tag == ChangeRelation.CONNECT):
                        jpms.addConnectModule(connect_key,associated_class)
                    else:
                        jpms.addDisconnectModule(connect_key,associated_class)
    def yamlClassEelement(self, tag, classes):
        mod_classes = []
        for ad_cls in classes:
            j_class = JPMSClass()
            cls_name = list(ad_cls.keys())[0]
            cls_info = ad_cls.get(cls_name)
            j_class.setName(cls_name)
            for ad_key in list(cls_info.keys()):
                if (ChangeRelation.KEY_CONNECT in ad_key):
                    connect_info = cls_info.get(ChangeRelation.KEY_CONNECT)
                    self.yamlChangeElement(ChangeRelation.KEY_CONNECT, j_class, connect_info)
                if (ChangeRelation.KEY_DISCONNECT in ad_key):
                    connect_info = cls_info.get(ChangeRelation.KEY_DISCONNECT)
                    self.yamlChangeElement(ChangeRelation.KEY_DISCONNECT, j_class,connect_info)
                if (ChangeRelation.KEY_API in ad_key):
                    connect_info = cls_info.get(ChangeRelation.KEY_API)
            j_class.involved_in_m2m=True
            mod_classes.append(j_class)
        return mod_classes

    def extractYaml(self, data_path):
        a_yaml_file = open(data_path)
        parsed_yaml_file = yaml.load(a_yaml_file, Loader=yaml.Loader)
        for yaml_p in parsed_yaml_file:
            key = list(yaml_p.keys())
            modul = JPMSMod()
            modul.setName(key[0])
            classes = yaml_p.get(key[0])
            for clas in classes:
                cls_keys = list(clas.keys())
                if(ChangeRelation.KEY_ADDED_CLS in cls_keys):
                    added_clses = clas[ChangeRelation.KEY_ADDED_CLS]
                    for ad_cls in self.yamlClassEelement(ChangeRelation.KEY_ADDED_CLS, added_clses):
                        modul.addedClass(ad_cls)

                if (ChangeRelation.KEY_DELETED_CLS in cls_keys):
                    deleted_clses = clas[ChangeRelation.KEY_DELETED_CLS]
                    for d_cls in self.yamlClassEelement(ChangeRelation.KEY_DELETED_CLS, deleted_clses):
                        modul.deletedClass(d_cls)
                if (ChangeRelation.KEY_MODIFIED_CLS in cls_keys):
                    modified_clses = clas[ChangeRelation.KEY_MODIFIED_CLS]
                    for mod_cls in self.yamlClassEelement(ChangeRelation.KEY_MODIFIED_CLS, modified_clses):
                        modul.modifiedClass(mod_cls)
                if (ChangeRelation.MO_ADD in cls_keys): # this is for module-info.java
                    modul.setChangeType("ADD")
                if (ChangeRelation.MO_DELETE in cls_keys): # this is for module-info.java
                    modul.setChangeType("DELETE")
                if (ChangeRelation.CONNECT in cls_keys): # this is for module-info.java
                    connect_info = clas.get(ChangeRelation.CONNECT)
                    self.yamlElementForConfig(ChangeRelation.CONNECT, modul, connect_info)
                if (ChangeRelation.DISCONNECT in cls_keys):
                    connect_info = clas.get(ChangeRelation.DISCONNECT) # this is for module-info.java
                    self.yamlElementForConfig(ChangeRelation.DISCONNECT, modul,connect_info)
                if(ChangeRelation.KEY_NOT_M2M in cls_keys):
                    no_in_m2m = clas[ChangeRelation.KEY_NOT_M2M]
                    if(type(no_in_m2m) is list):
                        for n_cls in no_in_m2m:
                            n_mod_cls = JPMSClass()
                            n_mod_cls.setName(n_cls)
                            modul.modifiedClass(n_mod_cls)
                    else:
                        n_mod_cls = JPMSClass()
                        n_mod_cls.setName(no_in_m2m)
                        modul.modifiedClass(n_mod_cls)

            self.addModule(modul)





#this a jpms module
class JPMSMod(ModuleFind):
    def __init__(self):
        self.full_name = None
        self.type = "JPMS" # it could be third party
        self.connected_modules = dict() # class_name: [JPMSMod]
        self.disconnected_modules = dict() # class_name: [JPMSMod]
        self.added_classes = []
        self.deleted_classes = []
        self.modified_classes = []
        self.ops_add = []
        self.ops_delete = []
        self.packages = [] # all the associated packages with this module
        self.jpms_mod_in_file = dict() # same as
        self.change_types = set()
    def setChangeType(self,c_type):
        self.change_types.add(c_type)
    def getChangeTypes(self):
        return self.change_types
    def setTemporaryModnameInFile(self,names):

        self.jpms_mod_in_file=names

    def setName(self, name):
        self.full_name = name
    def setType(self, type): # set if it is a third party library
        self.type = type
    def getPackages(self, all_packs):
        a_module = self.full_name.replace("module-info.java","")

        for pack in all_packs:
            if("test/" in pack):
                continue
            if (a_module+"/" in pack):
                self.packages.append(pack)

    def addConnectModule(self, mod,class_name):
        if(type(class_name) is list):
            for cls_name in class_name:
                self.connected_modules.setdefault(mod, []).append(cls_name)
        else:
            self.connected_modules.setdefault(mod, []).append(class_name)
    def addDisconnectModule(self,mod,class_name):
        if(type(class_name) is list):
            for cls_name in class_name:
                self.disconnected_modules.setdefault(mod, []).append(cls_name)
        self.disconnected_modules.setdefault(mod, []).append(class_name)
    def addedClass(self,jclass):
        self.added_classes.append(jclass)
    def deletedClass(self,jclass):
        self.deleted_classes.append(jclass)
    def modifiedClass(self,jclass):
        self.modified_classes.append(jclass)
    def opsAddInModule(self,op):
        self.ops_add.extend(op)
    def opsDeleteInModule(self,op):
        self.ops_delete.extend(op)
    def findModuleConnection(self, repo_path, rootmodules):
        #TODO-- when finding the corresponding module should consider full name of aa.bb.cc
        #TODO-- Example: com.azure.storage.blob.cryptography,
        if(len(self.ops_add)>0):
            imports_add = self.ops_add
            for imprt_line in imports_add:
                if("exports " in imprt_line or "opens " in imprt_line):
                    continue

                imports = [lin for lin in imprt_line.replace("transitive ","").split(" ") if("." in lin)]
                for imprt in imports:
                    # TODO--import need to be changed to be directory
                    reformed = self.importFullReformation(imprt)
                    reformed_packge =self.importReformation(imprt) # module includes full class name
                    # if (self.classInModule(repo_path, self.full_name, reformed) == False):
                    if (self.selfModuleNameCheck(reformed, self.jpms_mod_in_file, self.full_name) is None and  self.newFindImport(self.packages, reformed) is None):
                        mdl = self.newFindImport(rootmodules, reformed, self.jpms_mod_in_file, self.full_name) # search within module packges
                        if(mdl is None):
                            mdl = self.newFindImport(rootmodules, reformed_packge)
                        if (mdl is not None):
                            self.addConnectModule(mdl.replace(repo_path+"/",""), self.importToClass(imprt))
                        else:  # other wise it might be third party module or native module
                            self.addConnectModule("<<API>>", self.importToClass(imprt))

        if (len(self.ops_delete) > 0):
            imports_delete = self.ops_delete
            for imprt_line in imports_delete:
                if("exports " in imprt_line or "opens " in imprt_line):
                    continue
                imports = [lin for lin in imprt_line.replace("transitive ","").split(" ") if("." in lin)]
                for imprt in imports:
                    # TODO--import need to be changed to be directory
                    reformed = self.importFullReformation(imprt)
                    reformed_packge =self.importReformation(imprt) # module includes full class name
                    if (self.selfModuleNameCheck(reformed, self.jpms_mod_in_file, self.full_name) is None and self.newFindImport(self.packages, reformed) is None):
                        mdl = self.newFindImport(rootmodules, reformed, self.jpms_mod_in_file, self.full_name)
                        if (mdl is None):
                            mdl = self.newFindImport(rootmodules, reformed_packge)

                        if (mdl is not None):
                            self.addDisconnectModule(mdl.replace(repo_path+"/",""), self.importToClass(imprt))
                        else:  # other wise it might be third party module or native module
                            self.addDisconnectModule("<<API>>", self.importToClass(imprt))


                # TODO-- need to find through all root modules

class JPMSClass(ModuleFind):
    def __init__(self):
        self.full_name = None
        self.added_methods = [] # JPMSMethod types
        self.deleted_methods = [] # JPMSMethod types
        self.import_in_deleted_code = dict() # imprt:[lines]
        self.import_in_added_code = dict()
        self.empty_import = []
        self.import_added=[]
        self.import_deleted = []
        self.involved_in_m2m=False
        self.connected= dict() # modulename: classes
        self.disconnected = dict() # modulename: classes
        self.import_in_add_methods = set()
        self.import_in_delete_methods = set()
        self.is_import_in_method = False

    def setName(self,name):
        self.full_name = name
    def addDeleteMethod(self,mthd):
        self.deleted_methods.extend(mthd)
    def addAddedMethod(self,mthd):
        self.added_methods.extend(mthd)
    def addImport(self,imprt):
        self.import_added.extend(imprt)
    def deleteImport(self, imprt):
        self.import_deleted.extend(imprt)
    def imprtInDeletedCode(self, import_del):
        self.import_in_deleted_code.update(import_del)
    def imprtInAddedCode(self, imprt_add):
        self.import_in_added_code.update(imprt_add)
    def addConnected(self, mdl, cls_name):
        if(type(cls_name) is list):
            for c_name in cls_name:
                self.connected.setdefault(mdl, []).append(c_name)
        else:
            self.connected.setdefault(mdl, []).append(cls_name)

    def addDisConnected(self, mdl, cls_name):
        if (type(cls_name) is list):
            for c_name in cls_name:
                self.disconnected.setdefault(mdl, []).append(c_name)
        else:
            self.disconnected.setdefault(mdl, []).append(cls_name)

    def wholeCodeString(self, code_list):
        return " ".join(code_list)

    def findTermInCode(self, terms, code):
        # code = self.wholeCodeString(code)
        for term in terms:
            term = term.strip(" ")
            term1 = term+" "
            term2  = term+"."
            term3 = term+")"
            term4 = term+">"
            term5 = term+"("

            if(term in code or term1 in code or term2 in code or term3 in code or term4 in code or term5 in code):
                    return True
        return False

    def getPureCodeText(self, line):

        return line.strip("public ").strip("static ").strip("private ").strip("protected ").strip("void ").strip("for ").strip("for(").strip("if(").strip("if ").strip("throw ")\
            .strip(";").strip(",").strip("(").strip(")").strip("=").strip("<").strip(">").strip("new ").strip("null").strip("{").strip("}").strip("true").strip("false").split(" ")
    @staticmethod
    def keyTokExtraction(toks, filtered_toks):
        if (len(toks) > 1):
            toks = toks[0].split(" ")  # could be A objb=BB() or object=BB(), our target is to get objb
            tokens = list(filter(('').__ne__, toks))
            if (len(tokens) > 1):
                filtered_toks.append(tokens[len(tokens) - 1])
                return filtered_toks
            else:
                if(len(tokens)>0):
                    filtered_toks.append(tokens[0])
                return filtered_toks
        else:
            if ("(" in toks[0]):
                return JPMSClass.keyTokExtraction(toks[0].split("("), filtered_toks)

            toks = toks[0].split(" ")
            filtered_toks = list(filter(('').__ne__, toks))
            return filtered_toks

    def getPureCodeTokens(self,line, imprt_cls):
        match = re.findall(r'[\<+]+[\w]+[\>+]?', line)  # <aa>
        matched = []

        if (len(match) > 0):
            for i in range(0, len(match)):
                temp = match[i].replace("<", "").replace(">", "")
                if (imprt_cls != temp):
                    matched.append(temp)

        toks = line.replace("public ", "").replace("static ", "").replace("private ", "").replace("protected ",
                                                                                                  "").replace("final ",
                                                                                                              "").replace(
            "void ", "").replace(
            "for ", "").replace("for(", " ").replace("if(", " ").replace("if ", " ").replace("throw ", "") \
            .replace(";", "").replace(",", " ").replace(".", " ").replace(")", " ").replace("<", " ").replace(">",
                                                                                                              " ").replace(
            "new ", " ").replace("null", " ").replace(
            "{", " ").replace("}", " ").replace("true", "").replace("false", "")
        toks = toks.split("=")
        key_toks = []
        filtered_toks = JPMSClass.keyTokExtraction(toks, key_toks)
        for m in matched:
            filtered_toks = list(filter((m).__ne__, filtered_toks))
        return filtered_toks
    def stringSanityCheck(self, token):
        return token.replace("<>","")
    def importSearchInMethods(self,connection, import_in_methods, modified_code, modified_methods):
        in_method = False
        if(len(modified_methods)>0 and len(connection.keys())>0):
            for ky in connection.keys():
                imprts = connection.get(ky) #TODO -- ky could be a module name or <<API>>
                for imprt in imprts:
                    splitted = imprt.split("/")
                    imp_cls = splitted[len(splitted)-1]
                    # print(imp_cls)
                    import_dir = imprt
                    imprt = imprt.replace("/", ".") # gets like aa.bb.cc
                    lines = modified_code.get("import " + imprt+";") # making like import aa.bb.cc;
                    #this logic cannot search for aa.bb.cc.*; like patterns
                    if(lines is None):
                        return in_method
                    for line in lines:
                    # parts = self.getPureCodeText(lines) # could be, Put pt; Put pt = new Put() or abc = (Put)ab.get(); put = Put.get()
                        for mthd in modified_methods:
                            code = self.wholeCodeString(mthd.code)
                            if(line in code):#TODO- searching for Put in code Put pt =  or Put.get() or  <Put> or(Put)
                                if("<<API>>" in ky):
                                    import_in_methods.add(self.stringSanityCheck(
                                        mthd.name) + "<<>>" + import_dir)  # TODO- should save information as  method_name>>class_name, we can add special symbol for api such as <<>>, and usual class as >>

                                else:
                                    import_in_methods.add(self.stringSanityCheck(mthd.name)+">>"+import_dir) #TODO- should save information as  method_name>>class_name, we can add special symbol for api such as <<>>, and usual class as >>
                                in_method = True
                            else:
                                if(self.findTermInCode(self.getPureCodeTokens(line, imp_cls), code)):
                                    if("<<API>>" in ky):
                                        import_in_methods.add(self.stringSanityCheck(mthd.name) + "<<>>" + import_dir)

                                    else:
                                        import_in_methods.add(self.stringSanityCheck(mthd.name)+">>"+import_dir)
                                    in_method = True
        return in_method
    def importInModifiedMethods(self):
        self.is_import_in_method = self.importSearchInMethods(self.connected, self.import_in_add_methods, self.import_in_added_code, self.added_methods)
        self.importSearchInMethods(self.disconnected, self.import_in_delete_methods, self.import_in_deleted_code,
                                self.deleted_methods)


    def findModuleConnection(self, repo_path, packages, rootmodules):
        if(len(self.import_added)>0):
            imports_add = self.import_added
            for imprt in imports_add:
                # TODO--import statement is changed to directory
                reformed = self.importReformation(imprt)
                # if (self.classInModule(repo_path, modul, reformed) == False):
                if (self.newFindImport(packages, reformed) is None): # search in the beloning module
                    mdl = self.newFindImport(rootmodules, reformed)
                    self.involved_in_m2m = True
                    if (mdl is not None):
                        self.addConnected(mdl.replace(repo_path+"/",""), self.importToClass(imprt))
                    else: #other wise it might be third party module or native module
                        self.addConnected("<<API>>", self.importToClass(imprt))


        if (len(self.import_deleted) > 0):
            imports_delete = self.import_deleted
            for imprt in imports_delete:
                # TODO--import statement is changed to directory
                reformed = self.importReformation(imprt)
                if (self.newFindImport(packages, reformed) is None):
                    mdl = self.newFindImport(rootmodules, reformed)
                    self.involved_in_m2m = True
                    if (mdl is not None):
                        self.addDisConnected(mdl.replace(repo_path+"/",""), self.importToClass(imprt))
                    else: #other wise it might be third party module or native module
                        self.addDisConnected("<<API>>", self.importToClass(imprt))

                # TODO-- need to find through all root modules

class JPMSMethod:
    def __init__(self):
        self.name = None
        self.code =None
    def setName(self,name):
        self.name = name
    def setCode(self,code):
        self.code = code