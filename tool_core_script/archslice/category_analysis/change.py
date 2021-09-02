
import csv
import operator
import collections
import os

class ChangedCommit():
    def __init__(self):
        self.project_name = "project"
        self.samples = []

class Change:
    def __init__(self, type):
        self.type = type
        self.word_p = {} #probaility of each word calculated from frequency # it could be operation types as well --> add, delete, rename, import_add, import_del, function_add, function_delete
        self.samples = [] # simply all words with duplicacy
        self.classes_impacted = set()
        self.total = 0
    def putHash(self,word):
        if(word=='NON_M2M'):
            return
        self.samples.append(word)
        if word not in self.word_p.keys():
            self.word_p[word] = 1
        else:
            self.word_p[word] += 1
    def setOperation(self, ops):
        for op in ops:
            self.putHash(op)

    def setImpactedClasses(self, impacted):
        for cls in impacted:
            self.classes_impacted.add(cls)
    def setTotal(self, tot):
        self.total += tot
    def getKeys(self):
        return sorted(self.word_p.keys())
    def getValue(self, word):
        if(word in self.word_p.keys()):
            return self.word_p[word]
        else:
            return 0
    def normalize(self):
        for word in self.word_p:
            self.word_p[word] = round(self.word_p[word]/self.total,2)
    def print(self):
        print("------------------" + self.type+"-----------------")
        sorted_prev = sorted(self.word_p.items(), key=lambda kv: kv[1], reverse=True)
        for wordp in sorted_prev:
            print('(',wordp[0], ",", wordp[1],')')

    def save(self, csvfl):

        sorted_prev = sorted(self.word_p.items(), key=lambda kv: kv[1], reverse=True)
        for wordp in sorted_prev:
            csvfl.writerow([wordp[0], wordp[1]])
    def saveInText(self):
        os.mkdir(self.type)
        i= 0
        for sample in self.samples:
            file = open(self.type+"/"+str(i)+".txt", "w")
            file.write(sample[1])
            file.close()
            i+=1
    def saveInFile(self, dir,text_indx=1):
        file = open(dir + self.type + ".txt", "a")
        i= 0
        for sample in self.samples:

            file.write(sample[text_indx].replace('\n', ' ') + '\n')

            i+=1
        file.close()
    def savefoldFile(self, dir):
        try:
            dd = os.mkdir(dir)
        except:
            pass
        file = open(dir+"/" + self.type + ".txt", "a")
        i= 0
        for sample in self.samples:
            if(sample[1] is None or sample[1] ==''):
                continue
            file.write(sample[1].replace('NON_M2M', '').replace(',', ' ').replace('\n', ' ') + '\n')

            i+=1
        file.close()

    def saveConceptFile(self, dir, indx=6):
        try:
            dd = os.mkdir(dir)
        except:
            pass
        import ast
        file = open(dir + "/" + self.type + ".txt", "a")
        i = 0
        for sample in self.samples:
            if (sample[indx] is None or sample[indx] == ''):
                continue
            # ops= []
            # try:
            #     ops= ast.literal_eval(sample[indx])
            # except:
            #     print(sample[indx])
            #     ops = sample[indx].replace('[','').replace("'",'').replace(']','').split(',')
            file.write(" ".join(sample[indx]) +" " +sample[1].replace("NON_M2M","")+'\n')
            # file.write(sample[indx] + '\n')
            i += 1
        file.close()
    def saveTextAndSCO(self, dir, text_indx=2, op_indx=1):
        try:
            dd = os.mkdir(dir)
        except:
            pass
        file = open(dir+"/" + self.type + ".txt", "a")
        i= 0
        for sample in self.samples:
            txt = sample[text_indx].replace('\n', ' ')
            file.write( txt + ' ' + sample[op_indx].replace(',', ' ').replace('NON_M2M','') + '\n')

            i+=1
        file.close()
    def saveTextAndOPForWeka(self,dir, text_indx=2, op_indx=1):
        os.mkdir(dir+"/" +self.type)
        i= 0
        for sample in self.samples:
            file = open(dir+"/" +self.type+"/"+str(i)+".txt", "w")
            txt = sample[text_indx].replace('\n', ' ')
            file.write(txt + ' ' + sample[op_indx].replace(',', ' '))
            file.close()
            i+=1
    def saveOPForWeka(self,dir, op_indx=1):
        os.mkdir(dir+"/" +self.type)
        i= 0
        for sample in self.samples:
            file = open(dir+"/" +self.type+"/"+str(i)+".txt", "w")
            file.write(sample[op_indx].replace(',', ' '))
            file.close()
            i+=1

class ModuleChange(Change):
    def __init__(self, type):
        super().__init__(type)
        self.module_operation={}
        self.module_del_operation = {}
        self.jpms = dict()
        self.classes=dict()
    def putOperationHash(self,word, val):

        if word not in self.module_operation.keys():
            self.module_operation[word] = val
        else:
            self.module_operation[word] += val

    def putDelOperationHash(self,word, val):

        if word not in self.module_del_operation.keys():
            self.module_del_operation[word] = val
        else:
            self.module_del_operation[word] += val
    def normalizeOperation(self):
        for word in self.module_operation:
            self.module_operation[word] = round(self.module_operation[word]/self.total,2)
    def normalizeDelOperation(self):
        for word in self.module_del_operation:
            self.module_del_operation[word] = round(self.module_del_operation[word]/self.total,2)
    def getOpValue(self, word):
        if(word in self.module_operation.keys()):
            return self.module_operation[word]
        else:
            return 0

    def printOpDistribution(self):
        print("------------------module operation distribution-----------------")
        sorted_prev = sorted(self.module_operation.items(), key=lambda kv: kv[1], reverse=True)
        for wordp in sorted_prev:
            print(wordp[0], ": ", wordp[1])

    def printDelOpDistribution(self):
        print("------------------module operation distribution-----------------")
        sorted_prev = sorted(self.module_del_operation.items(), key=lambda kv: kv[1], reverse=True)
        for wordp in sorted_prev:
            print(wordp[0], ": ", wordp[1])

    def graphGenerate(self):
        import matplotlib.pyplot as plt
        plt.rcdefaults()
        import numpy as np
        import matplotlib.pyplot as plt

        objects = []


        performance = []
        fl = open(self.type + "_jpms.csv", 'w')
        csv_write = csv.writer(fl)

        for word in collections.OrderedDict(sorted(self.word_p.items(), key=operator.itemgetter(1),reverse=True)):
            objects.append(word)
            performance.append(self.word_p[word])
            #csv_write.writerow([word,self.word_p[word] ])
        for word in collections.OrderedDict(sorted(self.module_operation.items(), key=operator.itemgetter(1),reverse=True)):
            if("/" in word or "*" in word):
                None
            else:
                objects.append(word)
                performance.append(self.module_operation[word])
                csv_write.writerow([word, self.module_operation[word]])
        for word in collections.OrderedDict(sorted(self.module_del_operation.items(), key=operator.itemgetter(1),reverse=True)):
            if ("/" in word or "*" in word):
                None
            else:
                objects.append("D_" + word)
                performance.append(self.module_del_operation[word])
                csv_write.writerow(["D_" + word, self.module_del_operation[word]])
        fl.close()
        objects.append("scale")
        performance.append(10)
        y_pos = np.arange(len(objects))
        plt.bar(y_pos, performance, align='center', alpha=0.5)
        plt.xticks(y_pos, objects,fontsize=8, rotation=60)
        plt.ylabel('Distribution')
        plt.title(self.type+  " change")

        plt.show()

    def putJpms(self, jpm):
        if jpm not in self.jpms.keys():
            self.jpms[jpm] = 1
        else:
            self.jpms[jpm] += 1

    def putClasses(self, cls):
        if cls not in self.classes.keys():
            self.classes[cls] = 1
        else:
            self.classes[cls] += 1

    def getJpmsInfo(self):
        hotspot = []
        keys = self.jpms.keys()
        lngth = len(keys)
        for ky in keys:
            val = self.jpms.get(ky)
            if((val/self.total)>=0.10):
                hotspot.append(ky)
        return [lngth, len(hotspot)]

    def getClassesInfo(self):
        hotspot = []
        keys = self.classes.keys()
        lngth = len(keys)
        for ky in keys:
            val = self.classes.get(ky)
            if ((val / self.total) >= .10):
                hotspot.append(ky)
        return [lngth, len(hotspot)]

    def a2aGist(self):
        return [self.total, self.getJpmsInfo(), self.getClassesInfo()]
#
# test_data = ["add", "change", "add"]
#
# adaptive = Change("adaptive")
# for data in test_data:
#     adaptive.putHash(data)
#
# adaptive.setTotal(3)
# adaptive.normalize()
# adaptive.print()
