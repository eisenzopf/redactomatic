import sys

class EntityMap():
    def __init__(self):
        self._emap={}

    #Check and store aliases (e_val) for a key (e_ix) with for unique conversation_id(d_id) and entity category(e_cat) combinations.
    #Used to consistently replace words with index-numbers during redaction and then consistenly replace index-numers with redacted words during anonymization. 
    def update_entities(self, e_ix, d_id, e_val, e_cat="GLOBAL"):
        #e_ix: the key that we want to store this entity under (i.e. word or index-value)
        #d_id: conversation_id of the conversation to make the record unique to this conversation
        #e_val: the proposed new value of the entity unless it is already in the map
        #e_cat: a category label to further make the entity store unique.

        if d_id not in self._emap:
            self._emap[d_id]={}
        if e_cat not in self._emap[d_id]:
            self._emap[d_id][e_cat]={}
        if e_ix not in self._emap[d_id][e_cat]:
            self._emap[d_id][e_cat][e_ix]={}
        if bool(self._emap[d_id][e_cat][e_ix]):    # if we have an existing value in the self._emap, use it, otherwise use a new one and save it to the self._emap for context
            r = self._emap[d_id][e_cat][e_ix]
            #print("Match  ["+str(d_id)+"]["+str(e_cat)+"]["+str(e_ix)+"]=",r,file=sys.stderr)
        else:
            r = e_val
            self._emap[d_id][e_cat][e_ix] = e_val
            #print("Adding ["+str(d_id)+"]["+str(e_cat)+"]["+str(e_ix)+"]=",e_val,file=sys.stderr)

        return r
