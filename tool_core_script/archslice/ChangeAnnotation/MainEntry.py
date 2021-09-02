import sys

from ChangeAnnotation.Annotation import *
from ChangeAnnotation.jpms import *
from ChangeAnnotation.a2a import *
from preproces_mod.preprocess import Preprocess
from category_analysis.change import *
commit_type = ["ADD","MODIFY","DELETE"]
PROJS=["hibernate","hadoop","javaclient","jvm","linuxtools"]
COMMIT_REPO=["https://github.com/hibernate/hibernate-orm/commit", "https://github.com/apache/hadoop/commit","https://github.com/appium/java-client/commit","https://github.com/couchbase/couchbase-jvm-core/commit","https://github.com/eclipse/linuxtools/commit" ]
# MODULE_CODE_REPO=["/mnt/hadoop/vlab/azure-sdk-for-java", "/mnt/hadoop/vlab/atrium","/mnt/hadoop/vlab/speedment","/mnt/hadoop/vlab/bach","/mnt/hadoop/vlab/vooga","/mnt/hadoop/vlab/webfx","/mnt/hadoop/vlab/experiment_repo/aion","/mnt/hadoop/vlab/imgui","/mnt/hadoop/vlab/mvvmFX","/mnt/hadoop/vlab/hibernate-search"]
MODULE_CODE_REPO=["/mnt/hadoop/vlab/experiment_repo/azure-sdk-for-java", "/mnt/hadoop/vlab/experiment_repo/atrium","/mnt/hadoop/vlab/experiment_repo/speedment","/mnt/hadoop/vlab/experiment_repo/bach","/mnt/hadoop/vlab/experiment_repo/vooga","/mnt/hadoop/vlab/experiment_repo/webfx","/mnt/hadoop/vlab/experiment_repo/aion","/mnt/hadoop/vlab/experiment_repo/imgui","/mnt/hadoop/vlab/experiment_repo/mvvmFX","/mnt/hadoop/vlab/experiment_repo/hibernate-search"]
MODULE_PROJS = ["azure", "atrium","speedment","bach","vooga","webfx","aion","imgui","mvvmfx","hiber_search"]

MODULE_COMMIT_REPO=["https://github.com/Azure/azure-sdk-for-java/commit", "https://github.com/robstoll/atrium/commit","https://github.com/speedment/speedment/commit","https://github.com/sormuras/bach/commit","https://github.com/anna-dwish/vooga/commit","https://github.com/webfx-project/webfx/commit","https://github.com/aionnetwork/aion/commit" ,"https://github.com/kotlin-graphics/imgui/commit","https://github.com/sialcasa/mvvmFX/commit","https://github.com/hibernate/hibernate-search/commit"]
repository_dirs = "repository_dir"
commit_dirs = "commit_dir"
relation_folders = "relation_folder"
relation_test_folders = "relation_test_folder"
local_dir = "local_dir"

def a2aChangeInfo():
    result = []
    for i in range(0,10):
        annotation = A2A(MODULE_CODE_REPO[i],"/mnt/hadoop/vlab/jpms_commit_ids/"+ MODULE_PROJS[i]+ ".csv","/mnt/hadoop/vlab/jpmsproject/structure_modification/"+ MODULE_PROJS[i]+"_newa2a.csv", MODULE_PROJS[i])
        annotation.a2aFilter("/mnt/hadoop/vlab/jpmschange_info/", MODULE_COMMIT_REPO[i])


def validation():
    prepared = []
    result = []
    for i in range(0,10):
        # a2aO = A2A(MODULE_CODE_REPO[i],"/mnt/hadoop/vlab/jpmsproject/"+ MODULE_PROJS[i]+ ".csv","/mnt/hadoop/vlab/jpmsproject/"+ MODULE_PROJS[i]+"_a2a.csv", MODULE_PROJS[i])
        a2aO = A2A(MODULE_CODE_REPO[i], "/mnt/hadoop/vlab/jpmsproject/structure_modification/" + MODULE_PROJS[i] + "_correct.csv",
                   "/mnt/hadoop/vlab/jpmsproject/structure_modification/" + MODULE_PROJS[i] + "_predicted.csv", MODULE_PROJS[i]+"1")
        # prepared= a2aO.getCommitSamples(change_idx=3)
        # a2aO.a2aFilter("/mnt/hadoop/vlab/jpmschange_info/", MODULE_COMMIT_REPO[i])
        a2aO.changeDataParse("/mnt/hadoop/vlab/jpmschange_info/")
        a2aO.a2achange()

def downloadCommitIds():
    for i in range(0, 10):
        annotation = Annotaion(MODULE_CODE_REPO[i], "/mnt/hadoop/vlab/jpms_commit_ids/" + MODULE_PROJS[i] + ".csv",
                               "/mnt/hadoop/vlab/jpms_commit_ids/" + MODULE_PROJS[i] + ".csv")
        annotation.commitIdsInRange()

print("-------------- 10 download commit ids -------------------")
print("-------------- 11 structural change information extraction -------------------")
print("-------------- 12 detect m2m from commits list -------------------")

choice = int(input("Enter option:"))
if(choice==10):
    downloadCommitIds()
if(choice==11):
    a2aChangeInfo() # common strcutural change extraction
if(choice==12):
    validation() # m2m change detection
