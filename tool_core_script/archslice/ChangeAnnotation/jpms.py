from git import Repo
import csv
import nltk
from nltk.corpus import stopwords
import re
import gc
import time
import sys
import datetime
from pathlib import Path
import string
import operator
import itertools
import collections
from ChangeAnnotation.testing import Testing
from ChangeAnnotation.Annotation import Annotaion
from preproces_mod.codechange import ModuleFind
from pydriller import RepositoryMining, GitRepository
from pydriller.domain.commit import Commit
from category_analysis.change import *
csv.field_size_limit(2**16)
csv.field_size_limit(sys.maxsize)
commit_type = ["ADD","MODIFY","DELETE"]
allcategory = Change("All")


class ModuleAnnotate(ModuleFind, Annotaion):
    def __init__(self,repo_path, filter_path, save_path, project_name=None):
        super().__init__(repo_path, filter_path, save_path, project_name)
        self.modules = {}
        self.modules_dlete = {}
        self.delete_commit = 0
        self.other_commit = 0
        self.co_impact = 0
        self.co_impact_on_delete = 0
        self.class_impact_on_delete = set()
        self.class_impact_others = set()

        self.direct_impact_cls = set()
        self.total_mo = 0
        self.diret_impact_commit = 0
        self.co_impact_others = 0
        self.only_module_count =0
        self.only_import_count = 0
        self.count=0

    # def duality():
    #     projects_file = ["aion", "atrium", "azure", "bach", "hiber_search", "imgui", "speedment", "vooga", "webfx",
    #                      "mvvmfx"]
    #     for csvfil in projects_file:
    #         print(csvfil)
    #         preprocs = Preprocess("/mnt/hadoop/vlab/jpmsproject/" + csvfil + ".csv", csvfil)
    #         preprocs.readCsv()
    #         preprocs.stemmingSamples(1)
    #         # other noise cleaning techniques would be fruitful
    #         catg = Category(preprocs.content)
    #         mod = model.Model("adjusted_weight.csv")
    #         mod.readModel()
    #         catg.assignModel(mod.weight)
    #         catg.dualCategory(csvfil + "_annotate.csv", csvfil)
    #
    #     jpms_fl.close()
    #
    #     def calAndprint(obj):
    #         obj.normalize()
    #         obj.normalizeOperation()
    #         obj.normalizeDelOperation()
    #         obj.print()
    #         obj.printOpDistribution()
    #         obj.printDelOpDistribution()
    #         obj.graphGenerate()
    #
    #     calAndprint(perfectiveO)
    #     calAndprint(preventiveO)
    #     calAndprint(correctiveO)
    #     calAndprint(adaptiveO)
    #     calAndprint(allcategory)

    def moduleCheck(self, strn):
        if ("module-info.java" in strn):
            return True
        return False

    def moduleClassStat(self, is_delete, tmp_class_impact, types, files, files_delete):
        if types != set():
            self.co_impact += 1
        # print(types)
        if is_delete:  # only delete operation within the module file
            if types != set():
                self.co_impact_on_delete += 1
                for itm in tmp_class_impact:
                    self.class_impact_on_delete.add(itm)
            self.delete_commit += 1
        else:
            if types != set():
                self.co_impact_others += 1
                for itm in tmp_class_impact:
                    self.class_impact_others.add(itm)
            self.other_commit += 1
        # print(files)
        for name in files:
            if (name in self.modules.keys()):
                self.modules[name] += 1
            else:
                self.modules[name] = 1
        for name in files_delete:
            if (name in self.modules_dlete.keys()):
                self.modules_dlete[name] += 1
            else:
                self.modules_dlete[name] = 1
    def saveOutputToText(self, stat):
        file = open(self.project_name + ".txt", "w")
        i = 0
        file.write(str(stat) + '\n')
        file.write("----- contextual impacted classes -----" + '\n')
        for sample in self.direct_impact_cls:
            file.write(sample + '\n')

            i += 1
        file.write("----- non-contextual impacted classes -----" + '\n')
        for sample in self.no_direct_impact_cls:
            file.write(sample + '\n')

            i += 1
        file.write("----- bug impacted classes -----" + '\n')
        for sample in self.bug_cls:
            file.write(sample + '\n')

            i += 1

        file.write("----- contextual bug impacted classes -----" + '\n')
        for sample in self.contxt_bug_cls:
            file.write(sample + '\n')

            i += 1

        file.write("----- non-contextual bug impacted classes -----" + '\n')
        for sample in self.nocontxt_bug_cls:
            file.write(sample + '\n')

            i += 1
        file.write("----- non-contextual buggy classes oldest date-----" + '\n')
        for sample in self.buggy_cls.keys():
            file.write(sample+":"+self.buggy_cls.get(sample) + '\n')

            i += 1

        file.close()

    def parseMO(self, parsed_lines, modification, added_stat, added, deleted_stat, deleted, files_delete, files, is_module_operation):

        if (len(parsed_lines["added"]) > 0):

            for add_tuple in parsed_lines["added"]:
                name_part = add_tuple[1]
                if(self.findComment(name_part)):
                    # print(name_part)
                    pass
                    # if (name_part.lstrip(' ').find('//', 0) == 0):
                    #     None
                else:

                    # need to remove comments
                    only_modules = name_part.split('//')[0].strip().strip(",").strip(";").strip("{").strip(
                        "}").replace('\n', '')
                    if (only_modules is not ''):
                        is_module_operation = True
                        # print("Added: ", only_modules)
                        ## spliting a text having: operation_name module_name
                        module_operation = only_modules.split()
                        if (len(module_operation) > 1):

                            if (module_operation[0] not in added_stat.keys()):
                                added_stat[module_operation[0]] = 1
                            else:
                                added_stat[module_operation[0]] += 1
                            if ("transitive" in only_modules):
                                if ("transitive" not in added_stat.keys()):
                                    added_stat["transitive"] = 1
                                else:
                                    added_stat["transitive"] += 1
                        added.append(only_modules)
        if (len(parsed_lines["deleted"]) > 0):

            for del_tuple in parsed_lines["deleted"]:
                name_part = del_tuple[1]
                if (name_part.lstrip(' ').find('//', 0) == 0):
                    None
                else:

                    # need to remove comments
                    only_modules = name_part.split('//')[0].strip().strip(",").strip(";").strip("{").strip(
                        "}").replace('\n', '')
                    if (only_modules is not ''):
                        is_delete = True
                        is_module_operation = True
                        file_path = self.existedPath(modification.new_path, modification.old_path)
                        files_delete.add(file_path)
                        module_operation = only_modules.split()
                        if (len(module_operation) > 1):

                            if (module_operation[0] not in deleted_stat.keys()):
                                deleted_stat[module_operation[0]] = 1
                            else:
                                deleted_stat[module_operation[0]] += 1
                            if ("transitive" in only_modules):
                                if ("transitive" not in deleted_stat.keys()):
                                    deleted_stat["transitive"] = 1
                                else:
                                    deleted_stat["transitive"] += 1
                        deleted.append(only_modules)
        if (is_module_operation):
            if (modification.new_path is not None):
                files.add(modification.new_path)
            else:
                files.add(modification.old_path)
    def fileCheck(self, strn):
        if (".java" in strn or ".kt" in strn):
            if("package-info." in strn):
                return False
            return True
        return False
    def checkTest(self, strn):
        if ("test/" not in strn and "Test/" not in strn):
            return True
        return False
    def moduleChange(self, url):
        print("Repo: ", self.repo_path)
        fl = open(self.save_path, 'w')
        csv_write = csv.writer(fl)
        repo = Repo(self.repo_path)

        print("Wait commits downloading............")
        allcommits = repo.iter_commits()
        print("loaded ")
        count = 0
        all_commits = []
        for com in allcommits:
            all_commits.append(com)
            count = count+1
            #print(count)
        print("---total---", count)
        #allcommits = RepositoryMining(self.repo_path, since=datetime.datetime(2011, 1, 1), to=datetime.datetime(2018, 1, 1)).traverse_commits()
        for com in all_commits:
            found=False
            # for file in list(com.stats.files):
            #     if(".exe" in file or ".apk" in file or ".jar" in file or ".zip" in file or "chromedriver_" in file):
            #         found=True
            # if(found):
            #     continue
            commit = Commit(com,self.repo_path, None)
            #print(commit.hash)



            #print("---------------------commits-----------------------------------------", commit.hash)
            del_change = False
            mod_change = False
            change = False
            import_found = False
            java_import = False
            for modification in commit.modifications:
                if(self.__moduleCheck(modification.filename)):
                    mod_change = True
                    print("---------------------found")

            get_time = time.strftime("%Y-%m-%d", time.gmtime(float(com.committed_date)))
            if(mod_change):

                csv_write.writerow([url + "/" + commit.hash, commit.msg, get_time, "yes", "nocheck"])


    def moduleChangePattern(self, url):

        gr = GitRepository(self.repo_path)


        print("Repo: ", self.repo_path)
        fl = open(self.save_path, 'w')
        csv_write = csv.writer(fl)
        repo = Repo(self.repo_path)

        print("Wait commits downloading............")
        allcommits = repo.iter_commits()
        print("loaded ")
        count = 0
        all_commits = []
        for com in allcommits:
            all_commits.append(com)
            count = count+1
            #print(count)
        print("---total---", count)
        #allcommits = RepositoryMining(self.repo_path, since=datetime.datetime(2011, 1, 1), to=datetime.datetime(2018, 1, 1)).traverse_commits()
        for com in all_commits:
            found=False
            commit = Commit(com,self.repo_path, None)
            del_change = False
            mod_change = False
            change = False
            import_found = False
            java_import = False
            added = []
            added_stat= {}
            deleted_stat = {}
            deleted = []
            gr.get_commit(commit.hash)
            types = []
            for modification in commit.modifications:
                if(self.__moduleCheck(modification.filename)):
                    #print(commit.hash)
                    mod_change = True
                    types.append(modification.change_type.name)
                    print("---------------------found")
                    if("RENAME" in modification.change_type.name ):
                        print("Rename", modification.diff)
                    parsed_lines  = gr.parse_diff(modification.diff)
                    if(len(parsed_lines["added"])>0 ):

                        for add_tuple in parsed_lines["added"]:
                            name_part = add_tuple[1]
                            if(name_part.lstrip(' ').find('//', 0) ==0):
                                None
                            else:

                                #need to remove comments
                                only_modules = name_part.split('//')[0].strip().strip(",").strip(";").strip("{").strip("}").replace('\n','')
                                if(only_modules is not ''):
                                    print("Added: ", only_modules)
                                    ## spliting a text having: operation_name module_name
                                    module_operation = only_modules.split()
                                    if(len(module_operation)>1):

                                        if(module_operation[0] not in added_stat.keys()):
                                            added_stat[module_operation[0]] = 1
                                        else:
                                            added_stat[module_operation[0]] += 1
                                        if("transitive" in only_modules):
                                            if ("transitive" not in added_stat.keys()):
                                                added_stat["transitive"] = 1
                                            else:
                                                added_stat["transitive"] += 1
                                    added.append(only_modules)
                    if (len(parsed_lines["deleted"])>0):

                        for del_tuple in parsed_lines["deleted"]:
                            name_part = del_tuple[1]
                            if(name_part.lstrip(' ').find('//', 0)==0):
                                None
                            else:

                                # need to remove comments
                                only_modules = name_part.split('//')[0].strip().strip(",").strip(";").strip("{").strip("}").replace('\n','')
                                if (only_modules is not ''):
                                    print("Deleted: ", only_modules)
                                    module_operation = only_modules.split()
                                    if (len(module_operation) > 1):

                                        if (module_operation[0] not in deleted_stat.keys()):
                                            deleted_stat[module_operation[0]] = 1
                                        else:
                                            deleted_stat[module_operation[0]] += 1
                                        if ("transitive" in only_modules):
                                            if ("transitive" not in deleted_stat.keys()):
                                                deleted_stat["transitive"] = 1
                                            else:
                                                deleted_stat["transitive"] += 1
                                    deleted.append(only_modules)

            get_time = time.strftime("%Y-%m-%d", time.gmtime(float(com.committed_date)))
            if(mod_change):
                 # print("Addition: ", added_stat)
                 # print("Deletion: ", deleted_stat)

                csv_write.writerow([url + "/" + commit.hash, commit.msg, get_time, types, added_stat, deleted_stat])

    def commitIdFromUrl(self):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        gr = GitRepository(self.repo_path)
        delete_commit = 0
        other_commit = 0
        print(self.repo_path)
        fl = open(self.save_path, 'w')
        csv_write = csv.writer(fl)
        co_impact = 0
        f_impact = set()
        co_impact_on_delete = 0
        class_impact_on_delete = set()
        class_impact_others = set()
        co_impact_others = 0
        count=0
        for row in reader:
            is_module_operation = False
            parts = row[0].split("/")
            ID= parts[len(parts)-1]
            self.commit_ids.append(ID)
            commit = gr.get_commit(ID)
            files = set()
            files_delete = set()
            added = []
            added_stat = {}
            deleted_stat = {}
            deleted = []
            is_delete =False
            types = set()
            tmp_class_impact = set()
            #print("project path: " + row[0])
            for modification in commit.modifications:

                if (self.__moduleCheck(modification.filename)):
                    if(modification.new_path is not None):
                        files.add(modification.new_path)
                    else:
                        files.add(modification.old_path)
                    if(modification.change_type.name is not "MODIFY"):
                        is_module_operation = True
                    parsed_lines = gr.parse_diff(modification.diff)
                    if (len(parsed_lines["added"]) > 0):

                        for add_tuple in parsed_lines["added"]:
                            name_part = add_tuple[1]
                            if (name_part.lstrip(' ').find('//', 0) == 0):
                                None
                            else:

                                # need to remove comments
                                only_modules = name_part.split('//')[0].strip().strip(",").strip(";").strip("{").strip(
                                    "}").replace('\n', '')
                                if (only_modules is not ''):
                                    is_module_operation=True
                                    #print("Added: ", only_modules)
                                    ## spliting a text having: operation_name module_name
                                    module_operation = only_modules.split()
                                    if (len(module_operation) > 1):

                                        if (module_operation[0] not in added_stat.keys()):
                                            added_stat[module_operation[0]] = 1
                                        else:
                                            added_stat[module_operation[0]] += 1
                                        if ("transitive" in only_modules):
                                            if ("transitive" not in added_stat.keys()):
                                                added_stat["transitive"] = 1
                                            else:
                                                added_stat["transitive"] += 1
                                    added.append(only_modules)
                    if (len(parsed_lines["deleted"]) > 0):

                        for del_tuple in parsed_lines["deleted"]:
                            name_part = del_tuple[1]
                            if (name_part.lstrip(' ').find('//', 0) == 0):
                                None
                            else:

                                # need to remove comments
                                only_modules = name_part.split('//')[0].strip().strip(",").strip(";").strip("{").strip(
                                    "}").replace('\n', '')
                                if (only_modules is not ''):
                                    is_delete=True
                                    is_module_operation = True
                                    file_path = None
                                    if (modification.new_path is not None):
                                        file_path = modification.new_path
                                    else:
                                        file_path = modification.old_path

                                    files_delete.add(file_path)
                                    module_operation = only_modules.split()
                                    if (len(module_operation) > 1):

                                        if (module_operation[0] not in deleted_stat.keys()):
                                            deleted_stat[module_operation[0]] = 1
                                        else:
                                            deleted_stat[module_operation[0]] += 1
                                        if ("transitive" in only_modules):
                                            if ("transitive" not in deleted_stat.keys()):
                                                deleted_stat["transitive"] = 1
                                            else:
                                                deleted_stat["transitive"] += 1
                                    deleted.append(only_modules)
                elif (self.fileCheck(modification.filename)):
                    fil_path =None
                    if(modification.new_path is not None):
                        fil_path = modification.new_path
                    elif (modification.old_path is not None):
                        fil_path = modification.old_path
                    if("atrium" in self.save_path or self.checkTest(fil_path)):
                        #types.append(modification.change_type.name)
                        imports = None
                        ischange = False
                        if(modification.change_type.name is "RENAME"):
                            # print("NAME: old--" + str(modification.old_path) + " new----" + str(modification.new_path))
                            types.add(modification.change_type.name)
                            ischange = True
                        elif(modification.change_type.name is "MODIFY"):
                            imports = self.parseModify(modification)
                            # print("MODIFY: old--" + str(modification.old_path) + " new----" + str(modification.new_path))
                        elif (modification.change_type.name is "DELETE"):
                            # print("DELETE: old--" + str(modification.old_path) + " new----" + str(modification.new_path))
                            types.add(modification.change_type.name)
                            ischange = True
                        elif (modification.change_type.name is "ADD"):
                            # print("ADD: old--" + str(modification.old_path) + " new----" + str(modification.new_path))
                            types.add(modification.change_type.name)
                            ischange = True
                        if imports is not None:
                            for imprt in imports:
                                if(imprt is not ""):
                                    ischange = True
                                    types.add(imprt)
                        if ischange:
                            if modification.old_path:
                                tmp_class_impact.add(modification.old_path)
                                f_impact.add(modification.old_path)
                            elif modification.new_path:
                                f_impact.add(modification.new_path)
                                tmp_class_impact.add(modification.new_path)
            if(is_module_operation):
                if types != set():
                    co_impact += 1

                # print(types)
                if is_delete:  # only delete operation within the module file
                    if types != set():
                        co_impact_on_delete += 1
                        for itm in tmp_class_impact:
                            class_impact_on_delete.add(itm)
                    delete_commit += 1
                else:
                    if types != set():
                        co_impact_others += 1
                        for itm in tmp_class_impact:
                            class_impact_others.add(itm)
                    other_commit += 1
                # print(files)
                for name in files:
                    if (name in self.modules.keys()):
                        self.modules[name] += 1
                    else:
                        self.modules[name] = 1
                for name in files_delete:
                    if (name in self.modules_dlete.keys()):
                        self.modules_dlete[name] += 1
                    else:
                        self.modules_dlete[name] = 1

                count+=1
                row.append(types)
                if is_delete:
                    row.append("delete")
                csv_write.writerow(row)
        # print("------------------Modules operation ----------------------")
        # for name in collections.OrderedDict(sorted(self.modules.items(), key=operator.itemgetter(1),reverse=True)):
        #     print(name+": "+ str(self.modules[name]))
        print("Total commit: ",count)
        print("------------------Stat ----------------------")
        total = 0
        for name in collections.OrderedDict(sorted(self.modules_dlete.items(), key=operator.itemgetter(1),reverse=True)):
            total+=self.modules_dlete[name]
            #print(name+": "+ str(self.modules_dlete[name]))
        stat = {}
        stat["C"] = delete_commit # number of commits contain delete within a module
        stat["OC"] = other_commit # number of commits that do not contain delete within a module
        stat["F"] = len(self.modules_dlete.items())
        stat["T"] = total
        stat["CI"] = co_impact # all commits containing module operations that have impacted class connection
        stat["FI"] = len(f_impact) # all commits containing module operations that have impacted class connection
        stat["DCI"] = co_impact_on_delete # all commits containing module delete operations that have impacted class connection
        stat["DFI"] = len(class_impact_on_delete) # impacted classes in all commits containing module delete operations
        stat["OCI"] = co_impact_others # number of commits impacted class connections that do not contain delete within a module
        stat["OFI"] = len(class_impact_others) # number of classes impacted for connections that do not contain delete within a module
        print(stat)
        print("----------------------------------------------------------")

        csvfile.close()
        fl.close()

    # Find link among the modules
    def checkModuleContext(self, mod_list1, other_list):
        found = set()

        md_keys = list(mod_list1.keys())
        other_keys = list(other_list.keys())
        for md in md_keys:
            modl = mod_list1.get(md)
            for other in other_keys:
                other_modl = other_list.get(other)
                if(self.findLink(modl, other_modl)):
                    found.add(md)
                    found.add(other)
        return found



    def moduleContentHashing(self, source_code_before, fil_path, module_paths, module_codes ):
        module_path = self.repo_path + "/" + fil_path
        module_paths.add(module_path)
        try:

            codes = self.readProgramFile(module_path)  # modification.source_code.split('\n')#
            module_codes[module_path] = self.parseModuleFile(codes)

        except Exception as e:
            try:
                codes = source_code_before.split('\n')  # self.readProgramFile(module_path)
                module_codes[module_path] = self.parseModuleFile(codes)
            except:
                pass
    def findModuleName(self, mod_content):
        for conent in mod_content: # content --> module, operation
            if("module" in conent):
                if(conent[0]=='module'):
                    return conent[1]
        return None
    def extractModuleNameFromFile(self, all_modules):
        module_names = dict()
        for module_path in all_modules:
            try:
                codes = self.readProgramFile(module_path)
                mod_content = self.parseModuleFile(codes)
                module_names[self.importFullReformation(self.findModuleName(mod_content))] = self.onlyModPart(module_path.replace(self.repo_path+"/", ""))
            except:
                # print(e)
                pass
        return module_names
    def contextualModuleHashing(self,fil_path, other_module_paths, other_module_codes ):
        if ("main/java/" in fil_path):
            module_path = self.repo_path + "/" + fil_path.split("main/java/")[0] + "main/java/module-info.java"
        else:
            module_path = self.repo_path + "/" + fil_path.split("src/")[0] + "src/module-info.java"
        # mds = list(module_paths)
        if (module_path in other_module_paths):
            pass
        else:

            try:
                codes = self.readProgramFile(module_path)
                other_module_codes[module_path] = self.parseModuleFile(codes)
            except Exception as e:

                if ("main/java/" in fil_path):
                    first_part = fil_path.split("main/java/")[0]
                    second_part = fil_path.split("main/java/")[1].split("/")[0]
                    module_path = self.repo_path + "/" + first_part + "main/java/" + second_part + "/module-info.java"
                    if (module_path in other_module_paths):
                        pass
                    else:
                        other_module_paths.add(module_path)
                        try:
                            codes = self.readProgramFile(module_path)
                            other_module_codes[module_path] = self.parseModuleFile(codes)
                        except:
                            # print(e)
                            pass
                pass

    def purifyCommit(self):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        gr = GitRepository(self.repo_path)
        print(self.repo_path)
        fl = open(self.save_path, 'w')
        csv_write = csv.writer(fl)
        is_tmp_class = False
        is_bug = False
        # test_count = 0
        # only_import_count = 0
        for row in reader:
            is_module_operation = False
            parts = row[0].split("/")
            ID= parts[len(parts)-1]
            self.commit_ids.append(ID)

            commit = gr.get_commit(ID)
            try:
                gr.checkout(ID)
            except:
                # print(ID)
                pass
            is_bug = self.bugFixDetect(row[1])
            if(is_bug):
                self.total_bug +=1
            files = set()
            files_delete = set()
            added = []
            added_stat = {}
            deleted_stat = {}
            deleted = []
            is_delete =False
            types = set()
            tmp_class_impact = set()
            direct_impact = False
            has_live_module = False
            has_test = False
            only_import = True
            module_paths = set()
            module_codes = dict()
            other_module_paths = set()
            other_module_codes = dict()
            only_mod =False
            tmp_test_class = set()
            for modification in commit.modifications:

                if (self.moduleCheck(modification.filename)):

                    fil_path = self.existedPath(modification.new_path, modification.old_path)

                    self.moduleContentHashing(modification.source_code_before, fil_path, module_paths, module_codes)

                    if(self.checkTest(fil_path)):
                        has_live_module=True
                        is_module_operation = False
                        # Do not consider File rename nad modificarion with comments as module change operations
                        if(modification.change_type.name is not "RENAME" and modification.change_type.name is not "MODIFY"):
                            is_module_operation = True
                        parsed_lines = gr.parse_diff(modification.diff)
                        before_del = len(deleted)
                        before_add = len(added)
                        self.parseMO(parsed_lines, modification, added_stat, added, deleted_stat, deleted,files_delete, files, is_module_operation)
                        after_del = len(deleted)
                        after_add = len(added)
                        if(before_del != after_del):
                            is_delete = True
                            is_module_operation = True
                        if (before_add != after_add):
                            is_module_operation = True
                    else:
                        has_test = True
            if(has_live_module):
                for modification in commit.modifications:
                    if (self.moduleCheck(modification.filename)):
                        continue
                    elif (self.fileCheck(modification.filename)):
                        # ensure all modification checked
                        fil_path = self.existedPath(modification.new_path, modification.old_path)

                        if(self.checkTest(fil_path)):
                            if (is_bug):
                                self.bug_cls.add(fil_path)
                            #There are three possible directory of a module: src/module, src/main/java/, src/abc../main/java
                            self.contextualModuleHashing(fil_path, other_module_paths, other_module_codes)
                            if(modification.new_path is not None):
                                if (self.onlyImport(modification, gr) == False):
                                    only_import = False
                            #types.append(modification.change_type.name)
                            self.commitOP(modification, types, tmp_class_impact)
                        else:
                            has_test = True
                            tmp_test_class.add(fil_path)
                # Calculate contextual impact within the module
                if(tmp_class_impact != set()):
                    found = self.checkModuleContext(module_codes, other_module_codes)

                    for cls in tmp_class_impact:
                        if(cls is not None):
                            is_tmp_class = True
                            for mdl in found:
                                mdl_path = str(mdl).replace(self.repo_path + "/", "") .strip("mdoule-info.java")# remove local repo dir part
                                if(mdl_path not in cls):

                                    self.no_direct_impact_cls.add(cls)
                                    if(is_bug):

                                        self.nocontxt_bug_cls.add(cls)
                                        self.buggyClass(cls, row[2])

                                elif(mdl_path in cls):
                                    direct_impact =True
                                    self.direct_impact_cls.add(cls)
                                    if (is_bug):

                                        self.contxt_bug_cls.add(cls)
                elif(len(module_paths)>0):
                    direct_impact = True
                    only_mod = True
            if(is_module_operation):

                self.moduleClassStat(is_delete, tmp_class_impact, types, files, files_delete)
                self.count+=1
                row.append(types)
                if is_delete:
                    row.append("delete")
                if(is_tmp_class == True and direct_impact==False):
                    row.append("NDI")
                    if(is_bug):
                        self.nocontxt_bug +=1
                    self.no_direct_impact_commit +=1
                elif(direct_impact):
                    self.diret_impact_commit +=1
                    row.append("DI")
                    if(is_bug):
                        self.contxt_bug +=1
                if(is_bug):
                    row.append("BUG_FIX")
                if(only_mod):
                    self.only_module_count +=1
                if(has_test):
                    row.append("TEST")
                    self.test_count+=1
                    self.test_cls.update(tmp_test_class)
                if(only_import):
                    row.append("ONLY_IMPORT")
                    self.only_import_count +=1
                csv_write.writerow(row)

        total = 0
        for name in collections.OrderedDict(sorted(self.modules_dlete.items(), key=operator.itemgetter(1),reverse=True)):
            self.total_mo+=self.modules_dlete[name]
            #print(name+": "+ str(self.modules_dlete[name]))
        stat = {}
        stat["NAME"] = self.repo_path
        stat["TOTAL"] = self.count
        stat["DELETE_COMMIT"] = self.delete_commit # number of commits contain delete within a module
        stat["NO_DELETE"] = self.other_commit # number of commits that do not contain delete within a module
        stat["DELETE_MODULES"] = len(self.modules_dlete.items()) # modules contain DO
        stat["TOTAL_MOs"] = self.total_mo
        stat["COMMIT_IMPACT"] = self.diret_impact_commit # all commits containing module operations that have impacted class connection
        stat["FILE_IMPACT"] = len(self.direct_impact_cls) # all commits containing module operations that have impacted class connection
        stat["D_COMMIT_IMPACT"] = self.co_impact_on_delete # all commits containing module delete operations that have impacted class connection
        stat["D_FILE_IMPACT"] = len(self.class_impact_on_delete) # impacted classes in all commits containing module delete operations
        stat["OTHER_COMMIT_IMPACT"] = self.co_impact_others # number of commits impacted class connections that do not contain delete within a module
        stat["OTHER_FILE_IMPACT"] = len(self.class_impact_others) # number of classes impacted for connections that do not contain delete within a module

        stat["NODIRECT_COMMIT"] = self.no_direct_impact_commit
        stat["NODIRECT_FILES"] = len(self.no_direct_impact_cls)

        stat["TEST"] = self.test_count
        stat["TEST_CLS"] = len(self.test_cls)
        stat["ONLY_IMPORT"] = self.only_import_count
        stat["ONLY_MOD"] = self.only_module_count
        stat["BF"] = self.total_bug
        stat["BC"] = len(self.bug_cls)
        stat["BF_CNG"] = self.contxt_bug
        stat["BC_CNG"] = len(self.contxt_bug_cls)
        stat["BF_NC"] = self.nocontxt_bug
        stat["BC_NC"] = len(self.nocontxt_bug_cls)
        if(self.project_name is not None):
            self.saveOutputToText(stat)

        csvfile.close()
        fl.close()
        return stat

