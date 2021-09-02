import sys

from ChangeAnnotation.Annotation import *
from ChangeAnnotation.jpms import *
from ChangeAnnotation.a2a import *
from preproces_mod.preprocess import Preprocess
# from category_analysis.change import *
commit_type = ["ADD","MODIFY","DELETE"]
repository_dirs = "repository_dir"
commit_dirs = "commit_dir"
all_sample_dir ="sample_dir" ###########This should be the main samples
relation_folders = "relation_folder"
relation_test_folders = "relation_test_folder"
local_dir = "local_dir"
semantic_save = "semantic_save_dir"
def M2MChangeRelationExtraction():

    LOCAL_DIR =Preprocess.textFile("ChangeAnnotation/"+local_dir)
    COMMIT_FILE_DIR = Preprocess.textFile("ChangeAnnotation/"+all_sample_dir)#Preprocess.textFile("ChangeAnnotation/"+commit_dirs)
    RELATION_SAVE_DIR = Preprocess.textFile("ChangeAnnotation/"+relation_folders)
    N_projects = len(LOCAL_DIR)
    for i in range(0,N_projects):
        print(COMMIT_FILE_DIR[i])
        annotation = A2A(repo_path=LOCAL_DIR[i],filter_path=COMMIT_FILE_DIR[i],save_path="", project_name="")
        annotation.changeRelations(RELATION_SAVE_DIR[i])
        annotation.changeRelationAnalyze(RELATION_SAVE_DIR[i])

#TODO- this method takes files from change relations, base annotated commits, and then combine them into one file
def analyzeSemanticOPs():
    RELATION_TEST =Preprocess.textFile("ChangeAnnotation/"+relation_folders)
    COMMIT_FILE_DIR = Preprocess.textFile("ChangeAnnotation/"+all_sample_dir)#    COMMIT_FILE_DIR = Preprocess.textFile("ChangeAnnotation/"+commit_dirs)
    SEMANTIC_SAVE_DIR = Preprocess.textFile("ChangeAnnotation/"+semantic_save)
    N_projects = len(COMMIT_FILE_DIR)
    for i in range(0,N_projects):
        print(COMMIT_FILE_DIR[i])
        annotation = A2A(filter_path=COMMIT_FILE_DIR[i])
        # annotation.extractOperationRules(RELATION_TEST[i],SEMANTIC_SAVE_DIR[i])
        annotation.extractOperationRuleName(RELATION_TEST[i], SEMANTIC_SAVE_DIR[i])
print("-------------- 1 m2m relation summary extraction -------------------")
print("-------------- 4 m2m SSC extraction -------------------")
choice = int(input("Enter option:"))

if(choice==1):
    M2MChangeRelationExtraction()
if(choice==4):
    analyzeSemanticOPs()
