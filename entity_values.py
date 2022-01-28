import os
import csv

#A class to keep track of the replaced entity values for replacing ignored values and logging them.
class EntityValues():
    def __init__(self):
        self._entity_values={}

    def get_value(self,id):
        return self._entity_values.get(id,None)

    def set_value(self,id,value):
        if id not in self._entity_values:
            self._entity_values[id] = value
        
        return value

    def set_label_value(self,label,ix,value):
        newLabel = label+ "-"+str(ix)
        self.set_value(newLabel,value)
        return newLabel

    def write_csv(self, filepath):
        a_file = open(filepath, "w")
        writer = csv.writer(a_file)
        for key, value in self._entity_values.items():
            writer.writerow([key, value])
        a_file.close()
