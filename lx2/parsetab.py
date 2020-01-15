
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'DOT LPAREN NUM RPAREN SYMBOL\n    chemical_equation :\n    chemical_equation : species_list\n    species_list :  species_list speciesspecies_list : species\n    species : SYMBOL\n    species : SYMBOL NUM\n    species : SYMBOL LPAREN NUM RPAREN\n    species : SYMBOL LPAREN NUM DOT DOT NUM RPAREN\n    '
    
_lr_action_items = {'$end':([0,1,2,3,4,5,6,9,13,],[-1,0,-2,-4,-5,-3,-6,-7,-8,]),'SYMBOL':([0,2,3,4,5,6,9,13,],[4,4,-4,-5,-3,-6,-7,-8,]),'NUM':([4,7,11,],[6,8,12,]),'LPAREN':([4,],[7,]),'RPAREN':([8,12,],[9,13,]),'DOT':([8,10,],[10,11,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'chemical_equation':([0,],[1,]),'species_list':([0,],[2,]),'species':([0,2,],[3,5,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> chemical_equation","S'",1,None,None,None),
  ('chemical_equation -> <empty>','chemical_equation',0,'p_chemical_equation','chemParser.py',44),
  ('chemical_equation -> species_list','chemical_equation',1,'p_chemical_equation','chemParser.py',45),
  ('species_list -> species_list species','species_list',2,'p_species_list','chemParser.py',54),
  ('species_list -> species','species_list',1,'p_species','chemParser.py',59),
  ('species -> SYMBOL','species',1,'p_single_species','chemParser.py',64),
  ('species -> SYMBOL NUM','species',2,'p_single_species','chemParser.py',65),
  ('species -> SYMBOL LPAREN NUM RPAREN','species',4,'p_single_species','chemParser.py',66),
  ('species -> SYMBOL LPAREN NUM DOT DOT NUM RPAREN','species',7,'p_single_species','chemParser.py',67),
]