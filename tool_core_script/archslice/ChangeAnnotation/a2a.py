import sys
import git
from pydriller import RepositoryMining, GitRepository
from pydriller.domain.commit import Commit
from category_analysis.change import *
csv.field_size_limit(2**16)
csv.field_size_limit(sys.maxsize)
from ChangeAnnotation.jpms import  ModuleAnnotate
from preproces_mod.codechange import *
# from semanticAnalysis import category_concept
from postprocess.semanticop import *
commit_type = ["ADD","MODIFY","DELETE", "RENAME"]
class CommitState:
    def __init__(self, id):
        self.id = id
        self.packages = []
        self.jpms = []
        self.module_modify = []
        self.module_add = []
        self.module_delete = []
        self.module_rename = []
        self.mo_add = {}
        self.mo_delete = {}
        self.class_add = []
        self.class_delete= []
        self.class_rename = []
        self.class_modify=[]
        self.class_context = []
        self.class_noncontext = []
        self.class_bug_context = []
        self.class_bug_noncontext = []
        self.test_class = []
        self.only_import =[]
        self.import_dependency = {}

        self.a2aClass = []


class A2A(ModuleAnnotate):
    def __init__(self,repo_path=None, filter_path=None, save_path=None, project_name=None):
        super().__init__(repo_path, filter_path, save_path, project_name)
        self.commits_state=[]
        self.commit_cat = dict()
        self.jpmshot = {}
        self.change_relations = []
        self.classhot = {}
        self.perfectiveO = ModuleChange("perfective")
        self.correctiveO = ModuleChange("corrective")
        self.preventiveO = ModuleChange("preventive")
        self.adaptiveO = ModuleChange("adaptive")
        self.codechange_relations = []
        self.detected = None

    def jpmsModules(self):

        from os import walk

        f = set()
        pkg = set()
        # print(self.repo_path)
        for (dirpath, dirnames, filenames) in walk(self.repo_path):
            ifjava=False
            for filename in filenames:

                if('module-info.java' in filename):
                    f.add(dirpath+"/"+filename)
                elif(".java" in filename or ".kt" in filename):
                    ifjava=True
            if(ifjava):
                pkg.add(dirpath)


        return (f,pkg)

    def getIncludeDependency(self, modification):

        imprts = []

        del_import = modification.diff.count("-import")
        ad_import = modification.diff.count("+import")
        add_pack_count = modification.diff.count("+package")
        del_pack_count = modification.diff.count("-package")
        if ((del_import + ad_import + add_pack_count + del_pack_count) > 0):
            for imprt in modification.diff.split('\n'):
                # add_line_count = modification.diff.count("+\n")
                # del_line_count = modification.diff.count("-\n")
                # add_slash_count = modification.diff.count("\\+[\s]*//") + modification.diff.count("\\+[\s]*/")
                # add_at_count = modification.diff.count("+@")
                # del_slash_count = modification.diff.count("-[\s]*//") + modification.diff.count("-[\s]*/")
                # del_at_count = modification.diff.count("+@")
                # add_todo_count = len(re.findall("\\+[\s]*TODO", modification.diff))  # modification.diff.count("+ *")
                # del_todo_count = len(re.findall("-[\s]*TODO", modification.diff))  # modification.diff.count("- *")
                # add_star_count = len(re.findall("\\+[\s]*\\*", modification.diff))  # modification.diff.count("+ *")
                # del_star_count = len(re.findall("-[\s]*\\*", modification.diff))
                if(not self.findComment(imprt)):
                    if (imprt.find('-import', 0) == 0):
                        imprts.append(imprt.replace("-",""))
                    if (imprt.find('+import', 0) == 0):
                        imprts.append(imprt.replace("+",""))
                    # if (imprt.find('-package', 0) == 0):
                    #     imprts.append(imprt)
                    # if (imprt.find('+package', 0) == 0):
                    #     imprts.append(imprt)

        return imprts

    def isImportInStatement(self, imprt, statement):
        if(",*" in imprt): # when aa.bb.*;
            return False
        imprt = imprt.strip("import ").strip(";").split(".")
        if(self.termVariationMatching(imprt[len(imprt)-1], statement)):
            return True

    def getSeparateImports(self, parsed_lines):
        deleted = parsed_lines["deleted"]

        import_deletes = []
        final_import_deletes = []
        delete_last = 0
        add_last = 0
        import_in_ad_code=dict()
        import_in_del_code =dict()
        idx = 0
        for line in deleted:
            if(not self.findComment(line[1])):
                if("package " not in line[1]):
                    if(line[1].find('import', 0) == 0):
                        import_deletes.append(line[1])
                        delete_last =idx
            idx +=1
        added = parsed_lines["added"]
        final_import_added = []
        import_added = []
        idx=0
        for line in added:
            if(not self.findComment(line[1])):
                if("package " not in line[1]):
                    if(line[1].find('import', 0) == 0):
                        import_added.append(line[1])
                        add_last = idx
            idx +=1
        final_import_added, final_import_deletes = self.onlyDifferentiateImports(import_added,import_deletes,)
        if(len(final_import_deletes)>0):
            for line in deleted[delete_last+1:]:
                if (not self.findComment(line[1])):
                    for imprt in final_import_deletes:
                        if(self.isImportInStatement(imprt, line[1])):
                            import_in_del_code.setdefault(imprt, []).append(line[1])
                            # if(imprt not in import_in_del_code.keys()):
                            #     import_in_del_code[imprt] = [line[1]]
                            # else:
                            #     import_in_del_code[imprt].extend(line[1])

        if (len(final_import_added) > 0):
            for line in added[add_last + 1:]:
                if (not self.findComment(line[1])):
                    for imprt in final_import_added:
                        if (self.isImportInStatement(imprt, line[1])):
                            import_in_ad_code.setdefault(imprt, []).append(line[1])

        # add_imprts = []
        # delete_imports = []

        # del_import = modification.diff.count("-import")
        # ad_import = modification.diff.count("+import")
        # add_pack_count = modification.diff.count("+package")
        # del_pack_count = modification.diff.count("-package")
        # if ((del_import + ad_import + add_pack_count + del_pack_count) > 0):
        #     for imprt in modification.diff.split('\n'):
        #         # add_line_count = modification.diff.count("+\n")
        #         # del_line_count = modification.diff.count("-\n")
        #         # add_slash_count = modification.diff.count("\\+[\s]*//") + modification.diff.count("\\+[\s]*/")
        #         # add_at_count = modification.diff.count("+@")
        #         # del_slash_count = modification.diff.count("-[\s]*//") + modification.diff.count("-[\s]*/")
        #         # del_at_count = modification.diff.count("+@")
        #         # add_todo_count = len(re.findall("\\+[\s]*TODO", modification.diff))  # modification.diff.count("+ *")
        #         # del_todo_count = len(re.findall("-[\s]*TODO", modification.diff))  # modification.diff.count("- *")
        #         # add_star_count = len(re.findall("\\+[\s]*\\*", modification.diff))  # modification.diff.count("+ *")
        #         # del_star_count = len(re.findall("-[\s]*\\*", modification.diff))
        #         if (imprt.find('-import', 0) == 0):
        #             delete_imports.append(imprt)
        #         if (imprt.find('+import', 0) == 0):
        #             add_imprts.append(imprt)
        #         # if (imprt.find('-package', 0) == 0):
        #         #     imprts.append(imprt)
        #         # if (imprt.find('+package', 0) == 0):
        #         #     imprts.append(imprt)

        return (final_import_added, final_import_deletes, import_in_ad_code, import_in_del_code)



    # ----------------------------------------------------------------------------------
    # This method attempt to detect all types of structural dependency changes, including module operations
    # ----------------------------------------------------------------------------------
    def a2aFilter(self, info_path="/mnt/hadoop/vlab/a2aExtraction/",url="commit/"):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        gr = GitRepository(self.repo_path)
        gr.reset()
        print(self.repo_path)
        fl = open(self.save_path, 'w')
        csv_write = csv.writer(fl)
        is_tmp_class = False
        is_bug = False
        # test_count = 0
        # only_import_count = 0
        structural_change_count = 0

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
            is_bug = self.bugFixDetect(commit.msg)
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
            module_delete = set()
            module_add = set()
            module_modified = set()
            module_rename = set()
            class_delete = set()
            class_add = set()
            class_rename = set()
            class_modified = set()
            nocontext_bug = set()
            context_bug = set()
            direct_class = set()
            nodirect_class = set()
            mo_add_dic = dict()
            mo_delete_dic = dict()
            import_dependency = {}


            for modification in commit.modifications:
                if (self.moduleCheck(modification.filename)): #only module-info.java file

                    fil_path = self.existedPath(modification.new_path, modification.old_path)
                    # ----------------------------------------------------------------------------------
                    # read and parse the content of the module file
                    # ----------------------------------------------------------------------------------
                    self.moduleContentHashing(modification.source_code_before, fil_path, module_paths, module_codes)

                    if(self.checkTest(fil_path)):
                        has_live_module=True
                        is_module_operation = False
                        # Do not consider File rename and modification with comments as module change operations

                        if(modification.change_type.name is commit_type[0]): # ADD
                            module_add.add(modification.new_path)
                        if (modification.change_type.name is commit_type[2]): # DELETE
                            module_delete.add(modification.old_path)
                        if (modification.change_type.name is commit_type[3]): # MODIFY
                            module_rename.add(modification.new_path)

                        parsed_lines = gr.parse_diff(modification.diff)
                        tmp_delete = []
                        tmp_add = []
                        #----------------------------------------------------------------------------------
                        # separate added and deleted lines (MO operations).
                        # Need to handle comment like: //, *, /* within the prased module-info.java content
                        # ----------------------------------------------------------------------------------
                        self.parseMO(parsed_lines, modification, added_stat, tmp_add, deleted_stat, tmp_delete,files_delete, files, is_module_operation)
                        # ----------------------------------------------------------------------------------
                        # store the added or deleted mo operations (exports, requires) into dictionary and list
                        # ----------------------------------------------------------------------------------
                        if(len(tmp_delete)>0):
                            is_delete = True
                            is_module_operation = True
                            mo_delete_dic[fil_path] = tmp_delete
                            deleted.extend(tmp_delete)
                        if (len(tmp_add)):
                            mo_add_dic[fil_path] = tmp_add
                            added.extend(tmp_add)
                            is_module_operation = True
                        # ----------------------------------------------------------------------------------
                        # store the modified file name
                        # ----------------------------------------------------------------------------------
                        if(is_module_operation):
                            module_modified.add(fil_path)
                        if(modification.change_type.name is not "RENAME" and modification.change_type.name is not "MODIFY"):
                            is_module_operation = True
                    else:
                        has_test = True
                # elif (self.fileCheck(modification.filename)): # for .java or .kt file
                #     fil_path =None
                #     if(modification.new_path is not None):
                #         fil_path = modification.new_path
                #     elif (modification.old_path is not None):
                #         fil_path = modification.old_path
                #
                #     if(self.checkTest(fil_path)):
                #         #types.append(modification.change_type.name)
                #         # ----------------------------------------------------------------------------------
                #         # determine program file addition deletion, and import change within a file.
                #         # ----------------------------------------------------------------------------------
                #         self.commitOP(modification, types, tmp_class_impact)

            # ----------------------------------------------------------------------------------
            # This is only if there is module-info.java modification. if Ture then always do that
             # ----------------------------------------------------------------------------------

            if(True):
                for modification in commit.modifications:
                    if (self.moduleCheck(modification.filename)):
                        continue
                    elif (self.fileCheck(modification.filename)):
                        # ensure all modification checked
                        fil_path = self.existedPath(modification.new_path, modification.old_path)

                        if(self.checkTest(fil_path)):
                            if (is_bug):
                                self.bug_cls.add(fil_path)
                            if (modification.change_type.name is commit_type[0]):
                                class_add.add(modification.new_path)
                            if (modification.change_type.name is commit_type[2]):
                                class_delete.add(modification.old_path)
                            if (modification.change_type.name is commit_type[3]):
                                class_rename.add(modification.new_path)
                            # ----------------------------------------------------------------------------------
                            # This determine whether a file modification is aligned within the modified modules (context or non-context)
                            #There are three possible directory of a module: src/module, src/main/java/, src/abc../main/java
                            # ----------------------------------------------------------------------------------
                            self.contextualModuleHashing(fil_path, other_module_paths, other_module_codes) # modifies other_module_path
                            if(modification.new_path is not None):
                                # ----------------------------------------------------------------------------------
                                # determine whether a file modifications are only import change or not. Does not contain modification of other statements
                                # ----------------------------------------------------------------------------------
                                if (self.onlyImport(modification, gr) == False):
                                    only_import = False

                            #types.append(modification.change_type.name)
                            # print(fil_path)
                            if (modification.change_type.name is commit_type[1] or modification.change_type.name is commit_type[3]): # extract import statement from renamed or modified file
                                if(self.similarImportChange(gr.parse_diff(modification.diff))):
                                    continue
                                if(modification.change_type.name is commit_type[1]):
                                    class_modified.add(fil_path)
                                # need to handle cases where import is not in the first place
                                imprts = self.getIncludeDependency(modification)
                                if(len(imprts)>0):
                                    # ----------------------------------------------------------------------------------
                                    # store file name having import change
                                    # ----------------------------------------------------------------------------------
                                    import_dependency[fil_path] = imprts

                                    self.commitOP(modification, types, tmp_class_impact)
                        else:
                            has_test = True
                            tmp_test_class.add(fil_path)
                # ----------------------------------------------------------------------------------
                # Calculate contextual impact within the module involving all types of classes
                # ----------------------------------------------------------------------------------
                if(tmp_class_impact != set()):
                    found = self.checkModuleContext(module_codes, other_module_codes)

                    for cls in tmp_class_impact:
                        if(cls is not None):
                            is_tmp_class = True
                            for mdl in found:
                                mdl_path = str(mdl).replace(self.repo_path + "/", "") .strip("module-info.java")# remove local repo dir part
                                if(mdl_path not in cls):

                                    self.no_direct_impact_cls.add(cls)
                                    nodirect_class.add(cls)
                                    if(is_bug):

                                        self.nocontxt_bug_cls.add(cls)
                                        self.buggyClass(cls, commit.committer_date.strftime("%Y-%m-%d"))
                                        nocontext_bug.add(cls)

                                elif(mdl_path in cls):
                                    direct_impact =True
                                    self.direct_impact_cls.add(cls)
                                    direct_class.add(cls)
                                    if (is_bug):

                                        self.contxt_bug_cls.add(cls)
                                        context_bug.add(cls)
                elif(len(module_paths)>0):
                    direct_impact = True
                    only_mod = True

            # ----------------------------------------------------------------------------------
            # Saving all modification information into text file
            # ----------------------------------------------------------------------------------
            # if(is_module_operation == False and tmp_class_impact == set()):
            #     continue

            structural_change_count +=1
            MO = ""
            if(is_module_operation):
                MO ="MO"

            csv_row = [url+"/" + commit.hash, commit.committer_date.strftime("%Y-%m-%d,%H"), commit.msg.replace(";", ","), commit.author.email, MO]
            csv_write.writerow(csv_row)
            # continue
            file = open(info_path+self.project_name + "/" + ID + ".txt", "w")
            i = 0
            all_mdls, all_pkg = self.jpmsModules()

            file.write("project_modules:\n")
            file.write(str(len(all_mdls)) + '\n')
            for mdl in all_mdls:
                file.write(mdl + '\n')
            file.write(">>>>\n")

            file.write("package_modules:\n")
            file.write(str(len(all_pkg)) + '\n')
            for pkg in all_pkg:
                file.write(pkg + '\n')
            file.write(">>>>\n")
            if(module_delete!=set()):
                file.write("module_delete:\n")
                for dlt in module_delete:
                    file.write(dlt + '\n')
                file.write(">>>>\n")
            if(module_add!=set()):
                file.write("module_add:\n")
                for ad in module_add:
                    file.write(ad + '\n')
                file.write(">>>>\n")
            if(module_rename!=set()):
                file.write("module_rename:\n")
                for rn in module_rename:
                    file.write(rn + '\n')
                file.write(">>>>\n")
            if(module_modified !=set()):
                file.write("module_modify:\n")
                for md in module_modified:
                    file.write(md + '\n')
                file.write(">>>>\n")
            delete_keys = mo_delete_dic.keys()
            if (len(delete_keys) > 0):
                file.write("mo_delete:\n")
                for ky in delete_keys:
                    ky_dls = mo_delete_dic.get(ky)
                    for dls in ky_dls:
                        file.write(ky + "||" + dls + '\n')
                file.write(">>>>\n")
            add_keys = mo_add_dic.keys()
            if(len(add_keys)>0):
                file.write("mo_add:\n")
                for ky in add_keys:
                    ky_ads = mo_add_dic.get(ky)
                    for ads in ky_ads:
                        file.write(ky +"||"+ads + '\n')
                file.write(">>>>\n")
            if(class_delete !=set()):
                file.write("class_delete:\n")
                for dlt in class_delete:
                    file.write(dlt + '\n')
                file.write(">>>>\n")
            if(class_add !=set()):
                file.write("class_add:\n")
                for ad in class_add:
                    file.write(ad + '\n')
                file.write(">>>>\n")
            if(class_rename !=set()):
                file.write("class_rename:\n")
                for rn in class_rename:
                    file.write(rn + '\n')
                file.write(">>>>\n")
            if(class_modified !=set()):
                file.write("class_modify:\n")
                for md in class_modified:
                    file.write(md + '\n')
                file.write(">>>>\n")
            imprt_keys = import_dependency.keys()
            if (len(imprt_keys) > 0):
                # print("import found:", ID)
                file.write("import_dependency:\n")
                for ky in imprt_keys:
                    ky_imprt = import_dependency.get(ky)
                    for imprt in ky_imprt:
                        file.write(ky + "||" + imprt + '\n')
                file.write(">>>>\n")

            if(is_module_operation):

                self.moduleClassStat(is_delete, tmp_class_impact, types, files, files_delete)
                self.count+=1
                row.append(types)
                if is_delete:
                    row.append("delete")
                if(is_tmp_class == True and direct_impact==False):
                    file.write("class_noncontext:\n")
                    for nd in nodirect_class:
                        file.write(nd + '\n')
                    file.write(">>>>\n")
                    row.append("NDI")
                    if(is_bug):
                        self.nocontxt_bug +=1
                        file.write("bug_noncontext:\n")
                        for nb in nocontext_bug:
                            file.write(nb + '\n')
                        file.write(">>>>\n")
                    self.no_direct_impact_commit +=1
                elif(direct_impact):
                    self.diret_impact_commit +=1
                    file.write("class_context:\n")
                    for nd in direct_class:
                        file.write(nd + '\n')
                    file.write(">>>>\n")
                    row.append("DI")
                    if(is_bug):
                        self.contxt_bug +=1
                        file.write("bug_context:\n")
                        for nb in context_bug:
                            file.write(nb + '\n')
                        file.write(">>>>\n")

                if(is_bug):
                    row.append("BUG_FIX")
                if(only_mod):
                    self.only_module_count +=1
                if(has_test):
                    row.append("TEST")
                    file.write("test:\n")
                    for nb in tmp_test_class:
                        file.write(nb + '\n')
                    file.write(">>>>\n")

                    self.test_count+=1
                    self.test_cls.update(tmp_test_class)
                if(only_import):
                    row.append("ONLY_IMPORT")
                    row.append("TEST")
                    file.write("mod_import:\n")
                    file.write("ONLY_IMPORT\n")
                    file.write(">>>>\n")
                    self.only_import_count +=1

                file.close()

        # print(self.project_name,": ", structural_change_count)
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
        # if(self.project_name is not None):
        #     self.saveOutputToText(stat)
        csvfile.close()
        fl.close()
        return stat

    def changeYamlAnalysis(self, info_path="/mnt/hadoop/vlab/a2aExtraction/",url="commit/"):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        idx=0
        for row in reader:

            parts = row[0].split("/")
            ID= parts[len(parts)-1]
            OchangeRelation = ChangeRelation()
            OchangeRelation.setId(ID)
            OchangeRelation.setProjectRoort(self.repo_path)
            OchangeRelation.extractYaml(info_path+"/" + OchangeRelation.id + ".yml")
            OchangeRelation.changeInstanceCount()
            OchangeRelation.changeStat()
            OchangeRelation.totalInstances()
            OchangeRelation.saveAnalysisToYaml(info_path + "/" + str(idx+1) + ".yml")
            idx +=1

        csvfile.close()
    def relationInstance(self, ID, repo_path, file_path):
        OchangeRelation_tool = ChangeRelation()
        OchangeRelation_tool.setId(ID)
        OchangeRelation_tool.setProjectRoort(repo_path)
        OchangeRelation_tool.extractYaml(file_path)
        OchangeRelation_tool.changeInstanceCount()
        OchangeRelation_tool.totalInstances()
        return OchangeRelation_tool

    def extractOperationRules(self, validation_path="", save_path=""):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        fl = open(save_path, 'w')
        csv_write = csv.writer(fl)
        for row in reader:

            parts = row[0].split("/")
            ID= parts[len(parts)-1]

            manual = self.relationInstance(ID, self.repo_path,validation_path + "/" + ID + ".yml")
            op_rule = OperationRule()
            op_rule.extractSemanticOperations(manual)
            csv_write.writerow([row,op_rule.op_list])
            # print(ID, op_rule.op_list)
        fl.close()
        csvfile.close()
    def extractOperationRuleName(self, validation_path="", save_path=""):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        fl = open(save_path, 'w')
        csv_write = csv.writer(fl)
        for row in reader:

            parts = row[0].split("/")
            if (row[3] == "False" or row[3] == "FALSE"):
                continue
            ID= parts[len(parts)-1]
            print(ID)
            manual = self.relationInstance(ID, self.repo_path,validation_path + "/" + ID + ".yml")
            op_rule = RuleName()
            op_rule.extractDetailsSCO(manual)
            csv_write.writerow([row[0],','.join(op_rule.op_list), row[2], row[8], row[18],row[7]])
             # print(ID, op_rule.op_list)
        fl.close()
        csvfile.close()
    # ----------------------------------------------------------------------------------
    # similar to a2aFilter, This method extracts change relations of the commits on: modules, classes, methods, and imports
    # ----------------------------------------------------------------------------------
    def changeRelations(self, info_path="/mnt/hadoop/vlab/a2aExtraction/",url="commit/"):
        csvfile = open(self.filter_path, 'r' , encoding="utf8",errors='ignore')
        reader = csv.reader(csvfile, delimiter=',')
        gr = GitRepository(self.repo_path)
        repo = git.Repo(self.repo_path)
        is_tmp_class = False
        is_bug = False
        # test_count = 0
        # only_import_count = 0
        structural_change_count = 0
        for row in reader:
            if(row[3]=="False" or row[3]=="FALSE"):
                continue

            is_module_operation = False
            parts = row[0].split("/")
            ID= parts[len(parts)-1]
            OchangeRelation = ChangeRelation()
            OchangeRelation.setId(ID)
            self.commit_ids.append(ID)
            commit = gr.get_commit(ID)
            # gr.reset()
            try:
                repo.git.checkout('master')
                gr.checkout(ID)
            except Exception as e:
                print(ID, e)
                pass
            is_bug = self.bugFixDetect(commit.msg)
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
            tmp_test_class = set()
            module_delete = set()
            module_add = set()
            module_modified = set()
            module_rename = set()
            class_delete = set()
            class_add = set()
            class_rename = set()
            class_modified = set()
            mo_add_dic = dict()
            mo_delete_dic = dict()
            import_dependency = {}
            unique_jpms = dict()
            all_mdls, all_pkg = self.jpmsModules()
            OchangeRelation.setProjectRoort(self.repo_path)
            OchangeRelation.allModules(list(all_mdls))
            OchangeRelation.allPackages(list(all_pkg))
            OchangeRelation.setModuleNameInFile(self.extractModuleNameFromFile(all_mdls))
            def onlyModPart(mdl):
                #
                # if("/src/main/java/" in mdl):
                #     return mdl.split("/src/main/java/")[0] + "/src/main/java/"
                # elif("/main/java/" in mdl):
                #     return mdl.split("/main/java/")[0] + "/main/java/"
                # elif("/src/" in mdl):
                #     return mdl.split("/src/")[0] + "/src/"

                if("/src/main/java/" in mdl):
                    return mdl.split("/src/main/java/")[0]
                elif ("/src/main/kotlin/" in mdl):
                    return mdl.split("/src/main/kotlin/")[0]
                elif("/main/java/" in mdl):
                    return mdl.split("/main/java/")[0]
                elif("/src/" in mdl):
                    return mdl.split("/src/")[0]
                else:
                    return mdl

            def onlyClassPart(mdl):

                if("/src/main/java/" in mdl):
                    return mdl.split("/src/main/java/")[1]
                elif ("/src/main/kotlin/" in mdl):
                    return mdl.split("/src/main/kotlin/")[1]
                elif("/main/java/" in mdl):
                    return mdl.split("/main/java/")[1]
                elif("/src/" in mdl):
                    return mdl.split("/src/")[1]
                else:
                    return mdl

            for modification in commit.modifications:

                if (self.moduleCheck(modification.filename)): #only module-info.java file

                    fil_path = self.existedPath(modification.new_path, modification.old_path)

                    # ----------------------------------------------------------------------------------
                    # read and parse the content of the module file
                    # ----------------------------------------------------------------------------------
                    # self.moduleContentHashing(modification.source_code_before, fil_path, module_paths, module_codes)

                    # TODO: need to extract all ops added--done
                    # TODO: need to extract all ops deleted --done

                    if(self.checkTest(fil_path)):
                        Omod = None
                        new_mod = False
                        jpms_name = onlyModPart(fil_path.replace(self.repo_path + "/", ""))
                        allnames = unique_jpms.keys()
                        if(jpms_name in allnames):
                            Omod = unique_jpms[jpms_name]
                        else:
                            Omod = JPMSMod()

                            Omod.setName(jpms_name)
                            new_mod=True
                        has_live_module=True
                        is_module_operation = False
                        # Do not consider File rename and modification with comments as module change operations
                        only_add = False
                        only_delete = False
                        if(modification.change_type.name is commit_type[0]): # ADD
                            only_add = True
                            module_add.add(modification.new_path)
                            Omod.setChangeType(commit_type[0])
                        if (modification.change_type.name is commit_type[2]): # DELETE
                            only_delete = True
                            module_delete.add(modification.old_path)
                            Omod.setChangeType(commit_type[2])
                        if (modification.change_type.name is commit_type[3]): # MODIFY
                            module_rename.add(modification.new_path)
                            Omod.setChangeType(commit_type[3])
                        parsed_lines = gr.parse_diff(modification.diff)
                        tmp_delete = []
                        tmp_add = []
                        #----------------------------------------------------------------------------------
                        # separate added and deleted lines (MO operations).
                        # Need to handle comment like: //, *, /* within the prased module-info.java content
                        # ----------------------------------------------------------------------------------
                        self.parseMO(parsed_lines, modification, added_stat, tmp_add, deleted_stat, tmp_delete,files_delete, files, is_module_operation)
                        # ----------------------------------------------------------------------------------
                        # store the added or deleted mo operations (exports, requires) into dictionary and list
                        # ----------------------------------------------------------------------------------
                        if(len(tmp_delete)>0 and only_add==False):
                            is_delete = True
                            is_module_operation = True
                            mo_delete_dic[fil_path] = tmp_delete
                            Omod.opsDeleteInModule(tmp_delete)
                            deleted.extend(tmp_delete)
                        if (len(tmp_add) and only_delete == False):
                            mo_add_dic[fil_path] = tmp_add
                            added.extend(tmp_add)
                            is_module_operation = True
                            Omod.opsAddInModule(tmp_add)
                        if(only_add or only_delete):
                            is_module_operation=True
                        # ----------------------------------------------------------------------------------
                        # store the modified file name
                        # ----------------------------------------------------------------------------------
                        if(is_module_operation):
                            module_modified.add(fil_path)
                        if(modification.change_type.name is not "RENAME" and modification.change_type.name is not "MODIFY"):
                            is_module_operation = True
                        # OchangeRelation.addModule(Omod)

                        unique_jpms[jpms_name] = Omod


                    else:
                        has_test = True
                elif(self.fileCheck(modification.filename)):
                    # ensure all modification checked

                    fil_path = self.existedPath(modification.new_path, modification.old_path)
                    if(self.checkTest(fil_path)):
                        module_name = OchangeRelation.findModlOfCls(fil_path)
                        if(module_name is not None):
                            module_name = onlyModPart(module_name)

                        Omodule = None
                        new_mod = False
                        allnames = unique_jpms.keys()
                        already_exists = False
                        if (module_name is None):
                            module_name = onlyModPart(fil_path.replace(self.repo_path + "/", ""))

                        if (module_name is not None):
                            for existname in list(allnames):
                                if (module_name == existname):
                                    Omodule = unique_jpms[module_name]
                                    already_exists = True
                                    break
                        if(not already_exists):
                            Omodule = JPMSMod()
                            Omodule.setName(module_name)
                            Omodule.setType("NATIV")
                            new_mod = True
                        if (is_bug):
                            self.bug_cls.add(fil_path)
                        if (modification.change_type.name is commit_type[0]): # ADD operation
                            class_add.add(modification.new_path)
                            Oclass = JPMSClass()
                            Oclass.setName(onlyClassPart(modification.new_path))
                            imprts = self.getIncludeDependency(modification)
                            Oclass.addImport(imprts)
                            #TODO: need to extract all imports for the class -- done
                            Omodule.addedClass(Oclass)

                        if (modification.change_type.name is commit_type[2]): # DELETE operation
                            class_delete.add(modification.old_path)
                            Oclass = JPMSClass()
                            Oclass.setName(onlyClassPart(modification.old_path))
                            imprts = self.getIncludeDependency(modification)
                            Oclass.deleteImport(imprts)
                            # TODO: need to extract all imports for the class -- done
                            Omodule.deletedClass(Oclass)
                        if (modification.change_type.name is commit_type[3]): #RENAME operation
                            class_rename.add(onlyClassPart(modification.new_path))
                        # ----------------------------------------------------------------------------------
                        # This determine whether a file modification is aligned within the modified modules (context or non-context)
                        #There are three possible directory of a module: src/module, src/main/java/, src/abc../main/java

                        if(modification.new_path is not None):
                            # ----------------------------------------------------------------------------------
                            # determine whether a file modifications are only import change or not. Does not contain modification of other statements
                            # ----------------------------------------------------------------------------------
                            if (self.onlyImport(modification, gr) == False):
                                only_import = False

                        #types.append(modification.change_type.name)
                        #print(fil_path)
                        if (modification.change_type.name is commit_type[1] or modification.change_type.name is commit_type[3]): # extract import statement from renamed or modified file
                            # if(self.similarImportChange(gr.parse_diff(modification.diff))):
                            #     continue


                            if(modification.change_type.name is commit_type[1]): # MODIFY operation
                                class_modified.add(fil_path)
                            # need to handle cases where import is not in the first place
                            # imprts = self.getIncludeDependency(modification)
                            add_imprts, del_imports, import_in_ad, import_in_del = self.getSeparateImports(gr.parse_diff(modification.diff))
                            Oclass = JPMSClass()
                            Oclass.setName(onlyClassPart(fil_path))
                            if(len(add_imprts+del_imports)>0):
                                # ----------------------------------------------------------------------------------
                                # store file name having import change
                                # ----------------------------------------------------------------------------------
                                # import_dependency[fil_path] = imprts
                                Oclass.addImport(add_imprts)
                                Oclass.deleteImport(del_imports)
                                Oclass.imprtInAddedCode(import_in_ad)
                                Oclass.imprtInDeletedCode(import_in_del)
                                added_mthds, deleted_mthds = self.extractModifiedMethods(gr,modification, commit.committer_date)
                                Oclass.addAddedMethod(added_mthds)
                                Oclass.addDeleteMethod(deleted_mthds)
                                self.commitOP(modification, types, tmp_class_impact)
                            # self.extractModifiedMethods(gr,modification,commit.committer_date)
                            # TODO: need to extract added methods -- all done
                            # TODO: need to extract deleted methods
                            # TODO: need to extract added imports
                            # TODO: need to extract deleted imports
                            # TODO: need to extract added code with import change
                            # TODO: need to extract deleted code with import change -- all done
                            Omodule.modifiedClass(Oclass)
                        unique_jpms[module_name] = Omodule
                    else:
                        has_test = True
                        tmp_test_class.add(fil_path)
            for ky in unique_jpms.keys():
                OchangeRelation.addModule(unique_jpms.get(ky))
            self.change_relations.append(OchangeRelation)


    def changeRelationAnalyze(self,info_path="a2aExtraction/"):
        import yaml
        # TODO: need to extract all connected modules
        # TODO: need to extract all disconnected modules
        for relation in self.change_relations:
            relation.setProjectRoort(self.repo_path)
            relation.analyze()
            relation.saveAnalysisToYaml(info_path+"/" + relation.id + ".yml")
            # add_data = []
            # for jpmsmod in relation.modules:
            #
            #     uses_data = []
            #     for clss in jpmsmod.added_classes:
            #
            #         uses_data.append({clss.full_name:clss.import_added})
            #     add_data.append({'added':{jpmsmod.full_name: uses_data}})
            #     with open('data.yml', 'a') as outfile:
            #         yaml.dump(add_data, outfile, default_flow_style=False)




    def changeDataParse(self, data_path ="/mnt/hadoop/vlab/a2aExtraction/"):
        print(self.project_name)
        for commit_id in self.commit_ids:
            # parts = commit_id.split("/")
            # ID = parts[len(parts) - 1]
            c_state = CommitState(commit_id)
            mo_addition = []
            mo_deletion = []
            imports = []
            # file = open(data_path + self.project_name + "/" + commit_id + ".txt", "r")
            with open(data_path + self.project_name + "/" + commit_id + ".txt") as file_in:
                lines = []
                tracker = False
                line_data = []
                #need to parse--------------
                #data_name:
                #.....content
                #>>>>
                for line in file_in:
                    line=line.strip()
                    if (line == ">>>>"):
                        tracker = False
                    if (tracker):
                        line_data.append(line)
                        # print(line)
                    if(line == "package_modules:"):
                        # print("package_modules:")
                        tracker = True
                        line_data = c_state.packages
                    if (line == "project_modules:"):
                        # print("project_modules:")
                        tracker = True
                        line_data=c_state.jpms
                    if (line == "module_modify:"):
                        # print("package_modules:")
                        tracker = True
                        line_data = c_state.module_modify
                    if(line == "module_add:"):

                        tracker = True
                        line_data = c_state.module_add
                    if (line == "module_delete:"):
                        tracker = True
                        line_data = c_state.module_delete

                    if (line == "module_rename:"):
                        tracker = True
                        line_data = c_state.module_rename
                    if (line == "mo_add:"):
                        tracker = True
                        line_data = mo_addition
                    if (line == "mo_delete:"):
                        tracker = True
                        line_data = mo_deletion
                    if (line == "class_modify:"):
                        tracker = True
                        line_data = c_state.class_modify
                    if (line == "class_add:"):
                        tracker = True
                        line_data = c_state.class_add
                    if (line == "class_delete:"):
                        tracker = True
                        line_data = c_state.class_delete
                    if (line == "class_rename:"):
                        tracker = True
                        line_data = c_state.class_rename
                    if (line == "import_dependency:"):
                        tracker = True
                        line_data = imports
                    if (line == "class_context:"):
                        tracker = True
                        line_data = c_state.class_context
                    if (line == "class_noncontext:"):
                        tracker = True
                        line_data = c_state.class_noncontext

                    if (line == "bug_context:"):
                        tracker = True
                        line_data = c_state.class_bug_context
                    if (line == "bug_noncontext:"):
                        tracker = True
                        line_data = c_state.class_bug_noncontext
                    if (line == "test:"):
                        tracker = True
                        line_data = c_state.test_class
                    if (line == "mod_import:"):
                        tracker = True
                        line_data = c_state.only_import

            if(len(mo_addition)>0):
                for mo_ad in mo_addition:
                    parts = mo_ad.split("||")
                    if(self.findComment(parts[1])):
                        # print(parts[1])
                        pass
                    else:
                        mo_keys = c_state.mo_add.keys()
                        if (parts[0] in mo_keys):
                            mo_list = c_state.mo_add.get(parts[0])
                            mo_list.append(parts[1])
                            c_state.mo_add[parts[0]] = mo_list
                        else:
                            c_state.mo_add[parts[0]] = [parts[1]]

            if(len(mo_deletion)>0):
                for mo_dl in mo_deletion:
                    parts = mo_dl.split("||")
                    if (self.findComment(parts[1])):
                        # print(parts[1])
                        pass
                    else:
                        mo_keys = c_state.mo_delete.keys()
                        if (parts[0] in mo_keys):
                            mo_list = c_state.mo_delete.get(parts[0])
                            mo_list.append(parts[1])
                            c_state.mo_delete[parts[0]] = mo_list
                        else:
                            c_state.mo_delete[parts[0]] = [parts[1]]
            if (len(imports) > 0):
                for imprt in imports:
                    parts = imprt.split("||")
                    imprt_keys = c_state.import_dependency.keys()
                    # class name is parts[0]
                    if(parts[0] in imprt_keys):
                        imprt_list = c_state.import_dependency.get(parts[0])
                        imprt_list.append(parts[1])
                        c_state.import_dependency[parts[0]] = imprt_list
                    else:
                        c_state.import_dependency[parts[0]] = [parts[1]]
            self.commits_state.append(c_state)

    def findModuleFor(self, com_state, class_dir):
        mod_name = None
        to_search = class_dir.split("/src/")[0]+"/src/"
        to_search2 = class_dir.split("/main/java/")[0] + "/main/java/"
        to_search3 = class_dir.split("/src/main/java/")[0] + "/src/main/java/"
        to_search4 = class_dir.split("/src/")[0] + "/"
        # print(to_search)
        for mdl in com_state.jpms:
            if(to_search in mdl or to_search2 in mdl or to_search3 in mdl or to_search4 in mdl):
                return mdl


        return mod_name


    #temporary modification for checking change with only native java library
    def a2achange(self):
        total_change = 0
        m2m_change = 0
        fl = open(self.save_path, 'w')
        csv_write = csv.writer(fl)
        changed_commit = ChangedCommit()
        for com_state in self.commits_state:
            only_native_import = True
            cross_module_import = False
            is_m2m = False
            class_jpms = {}
            imprt_keys = com_state.import_dependency.keys()  # class names which changed import
            others = set()
            jpms_packges = {}

            for i in range(1, len(com_state.jpms)):
                a_module = com_state.jpms[i].strip("module-info.java")
                asso_package = []
                for j in range(1, len(com_state.packages)):
                    pack = com_state.packages[j]

                    if (a_module in pack):
                        asso_package.append(pack)
                jpms_packges[a_module] = asso_package  # list all the packages within a module

            if (len(imprt_keys) > 0):
                # print(com_state.id, "------------------------------------------")
                for class_name in imprt_keys:  # class names
                    # determine the associated module
                    involved = False
                    # logic for determining whether a class imported class/package from the same module or different modules
                    if ("/src/" in class_name or "/main/java/" in class_name):
                        module = self.findModuleFor(com_state, class_name)
                        if (module is not None):
                            class_jpms[class_name] = module
                            imprt_list = com_state.import_dependency.get(class_name)
                            packs = jpms_packges.get(module.strip("module-info.java"))
                            for imprt in imprt_list:
                                # print("------------:", imprt)
                                class_part = imprt.replace('+import ','').replace('-import ','').replace('+package ','').replace(
                                    '-package ','').replace('import ', '').replace('package  ', '').split('.')  # probably convert "+import java.util.IO" --> java.util.IO --> [java, util, IO]

                                if ("java" not in class_part[0] or "javafx" not in class_part[0]):

                                    only_native_import = False
                                else:
                                    pass
                                    # print(imprt)
                                reformed = "/".join(class_part[:len(class_part) - 1])
                                # print(reformed)
                                class_found = False
                                for pack in packs:
                                    if (reformed in pack.replace(".", "/")): # it indicates import is from same module
                                        class_found = True
                                        # break
                                # if (class_found == True):
                                #     print("*********** inside of module context")
                                if (class_found == False): # otherwise import is from different module
                                    # print("*********** A2A change")
                                    total_change += 1
                                    involved = True
                                    cross_module_import = True
                                    if ("java" not in class_part[0] or "javafx" not in class_part[0]):

                                        only_native_import = False
                                    else:
                                        pass
                                        # print(imprt)


                            # print(ky, module)
                    else:
                        # other wise its in main module dir.......any import change might be a dependency change
                        # print("within main module:", ky)
                        others.add(class_name)
                    if (involved):
                        com_state.a2aClass.append(class_name)

            if (cross_module_import):
                is_m2m = True
            else:
                only_native_import = "undecided"
            if (len(com_state.class_add) > 0 or len(com_state.class_delete) > 0 or len(com_state.module_add) > 0 or len(
                    com_state.module_delete) or len(com_state.mo_delete.keys()) > 0 or len(
                    com_state.mo_add.keys()) > 0):
                is_m2m = True
            if (is_m2m):
                m2m_change += 1
                changed_commit.samples.append([com_state.id, "True"])
            else:
                changed_commit.samples.append([com_state.id, "False"])
            rrow = self.commit_msg.get(com_state.id)
            self.detected=changed_commit
            csv_write.writerow([rrow[0], rrow[1], rrow[2], str(is_m2m), str(only_native_import)])
        # print(self.project_name, " a2a related class change:", m2m_change)
        # for ky in com_state.mo_add.keys():
        #     print(com_state.mo_add.get(ky))
        # for ky in com_state.mo_delete.keys():
        #     print(com_state.mo_delete.get(ky))

    def putHotjpms(self, jpm):
        if jpm not in self.jpmshot.keys():
            self.jpmshot[jpm] = 1
        else:
            self.jpmshot[jpm] += 1

    def putHotcls(self, cls):
        if cls not in self.classhot.keys():
            self.classhot[cls] = 1
        else:
            self.classhot[cls] += 1

    def getJpmsInfo(self):
        hotspot = []
        keys = self.jpmshot.keys()
        lngth = len(keys)
        for ky in keys:
            val = self.jpmshot.get(ky)
            if((val/len(self.commits_state))>=0.10):
                hotspot.append(ky)
        return [lngth, len(hotspot)]

    def getClassesInfo(self):
        hotspot = []
        keys = self.classhot.keys()
        lngth = len(keys)
        for ky in keys:
            val = self.classhot.get(ky)
            if ((val / len(self.commits_state)) >= 0.10):
                hotspot.append(ky)
        return [lngth, len(hotspot)]

    def storeInChangeType(self, typeO,com_state):
        typeO.setTotal(1)
        for md in com_state.module_add:
            typeO.putJpms(md)
            self.putHotjpms(md)
        for md in com_state.module_delete:
            typeO.putJpms(md)
            self.putHotjpms(md)
        for md in com_state.module_modify:
            typeO.putJpms(md)
            self.putHotjpms(md)
        for md in com_state.module_rename:
            typeO.putJpms(md)
            self.putHotjpms(md)
        for cls in com_state.class_add:
            typeO.putClasses(cls)
            self.putHotcls(cls)
        for cls in com_state.class_delete:
            typeO.putClasses(cls)
            self.putHotcls(cls)
        for cls in com_state.class_rename:
            typeO.putClasses(cls)
            self.putHotcls(cls)
        # print(com_state.a2aClass)
        for cls in com_state.a2aClass:
            typeO.putClasses(cls)
            self.putHotcls(cls)
