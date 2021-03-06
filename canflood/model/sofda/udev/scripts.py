'''
Created on Jun 11, 2018

@author: cef
'''

#===============================================================================
# IMPORT STANDARD MODS
#===============================================================================
import copy, logging
""" unused
logging, os, sys, imp, time, re, math, inspect, weakref, time
"""

#import pandas as pd
#import numpy as np


from collections import OrderedDict
from weakref import WeakValueDictionary as wdict

#===============================================================================
#  IMPORT CUSTOM MODS ---------------------------------------------------------
#===============================================================================

#import model.sofda.hp.basic as hp_basic
#import model.sofda.hp.dict as hp_dict
#import model.sofda.hp.data as hp_data
import model.sofda.hp.sel as hp_sel
import model.sofda.hp.dyno as hp_dyno
import model.sofda.hp.oop as hp_oop
import model.sofda.hp.sim as hp_sim

mod_logger = logging.getLogger(__name__)
mod_logger.debug('initilized')

#===============================================================================
# import in project mods
#===============================================================================
class Udev( 
            
            hp_sel.Sel_controller, 
            hp_dyno.Dyno_wrap,
            #hp.plot.Plot_o, #need this so children can inherit properly
            hp_sim.Sim_model, #a timestep from teh simulation timeline
            hp_oop.Parent_cmplx,
            hp_oop.Child): 
    
    #===========================================================================
    # program pars
    #========================================================================== 
    # object handling overrides
    
    """
    load_data_f         = True
    raise_kids_f        = False
    'controlled by Session.raise_children'
    raise_in_spawn_f    = False #load all he children before moving on to the next sibling"""
    
    db_f                = True
    
    #inheritance
    try_inherit_anl = ['infil_cnt', 'fhr_nm', 'bucket_size', 'mind']
    #===========================================================================
    # calculated pars
    #===========================================================================
    #sels_d = None # d[selector name] = selector_o
    acts_d = None #d[action name] = action_o
    fhzs_d = None #dictionary of fhz objervts
    
    dyn_vuln_f      = False #dynamic vulnerability (i.e. udev model has some actions)
    
    seq = 1 #model sequence for the hs_stamp
    
    #===========================================================================
    # user pars
    #===========================================================================
    infil_cnt   =   None #nubmer of properties to infil each year
    infil_cnt_delta = 0 #infill count dtimeline delta
    bucket_size = 0
    
    fhr_nm = 'current'
    #pick_type = 'simple'
    
        
    def __init__(self, *args, **kwargs):
        logger = mod_logger.getChild('Udev')
        logger.debug('start _init_')
        #=======================================================================
        # #initilzie teh baseclass  
        #=======================================================================
        super(Udev, self).__init__(*args, **kwargs) 
        
        #=======================================================================
        # special inheritance
        #=======================================================================
        self.fdmg = self.session.fdmg #get the partner model
        
        #building inventory
        self.binv   = self.fdmg.binv
        self.hse_od = self.binv.hse_od #get the collection of houses
        self.hse_d  = self.binv.kids_d #get the collection of houses
        

        
        
        #=======================================================================
        # custom attst
        #=======================================================================
        'todo add a separate tab to inherit these'
        self.infil_cnt = int(self.infil_cnt)
        self.bucket_size = int(self.bucket_size)
        'original copy of this should be captured by the dynp kid'
        
        """just using a bucket_size kwarg
        if self.model.pick_type.startswith('bucket'):
            #get bucket size from kwarg
            _, bucket_size = self.model.pick_type.split('[') #split along the bracket
            
            self.bucket_size = int(bucket_size[:-1])"""
        
        
        #=======================================================================
        # custom loader funcs
        #=======================================================================
        """ this is called by the Session.raise_children() to properly handle the dependencies
        logger.debug('raise_children \n')
        self.raise_children()"""
        
        """ moved all this to Fdmg
        #=======================================================================
        # Udev data workers
        #=======================================================================
        logger.info('loading data objects from \'udev\' tab into udev_d')
        logger.debug('\n \n')

        self.udev_d = self.raise_children_df(self.session.pars_df_d['udev'], 
                                     kid_class = hp_data.Data_o)
        
        logger.debug('set_fhr() \n')
        #update hte building inventory with this data
        self.set_fhr()"""
        
        #=======================================================================
        # dynos
        #=======================================================================
        logger.debug("init_dynos \n")
        self.init_dyno()
        self.logger.info('udev model initialized as %s'%(self.name))
        logger.debug('finished _init_ \n')
        
        if self.db_f: self.check_udev()
        
        return
    
    def check_udev(self):
        logger = self.logger.getChild('check_udev')
        #check intersect on the fhz lvls, names, and binv
        
        """
        #check that the focal fhz is in the data
        if not self.fhr_nm in self.udev_d['fhzs_tbl'].data.columns:
            raise IOError"""
        
        #check the bucket size against the infil_cnt
        if self.bucket_size >0:
            if not self.bucket_size >= self.infil_cnt: 
                logger.error('NOT bucket_size (%i) >= infil_cnt (%i)'%(self.bucket_size, self.infil_cnt))
                raise IOError
            
        #check that youre not trying to pick more housees than there are
        if not self.infil_cnt <= self.binv.cnt: 
            raise IOError('infil_cnt (%i) < inventory size (%i)'
                          %(self.infil_cnt, self.binv.cnt))
        
    
    def raise_children(self):
        """
        #=======================================================================
        # CALLS
        #=======================================================================
        Session.raise_children(0
        """
        logger = self.logger.getChild('raise_children')
        
        #=======================================================================
        # #Selectors
        #=======================================================================
        self.sels_d = self.session.sels_d
        logger.info('notifying %i Selectors Im their model'%len(self.sels_d))
        logger.debug('\n \n')
        for seln, selo in self.sels_d.items(): selo.model = self
        
        #=======================================================================
        # #Dynp
        #=======================================================================
        self.dynp_d = self.session.dynp_d
        logger.info('notifying %i Dynps Im their model'%len(self.dynp_d))
        logger.debug('\n \n')
        for name, obj in self.dynp_d.items(): obj.model = self
        
                        
        logger.debug('finished \n')
                
    def get_results(self):
        #logger = self.logger.getChild('get_results')
        self.state='get_results'
        
        self.binv.calc_binv_stats()
        
    def wrap_up(self):
        logger = self.logger.getChild('wrap_up')
        self.state='wrap_up'
        
        #=======================================================================
        # time flag
        #=======================================================================
        self.last_tstep = copy.copy(self.time)
        
        logger.debug('finished \n')
        self.state='close'
        
        return
        
         

                        
class House_udev(object): #add some develompent functions to the house object
    'see scripts.fdmg.House for most commands'
    
    #===========================================================================
    # development attributes from the binv
    #===========================================================================
    fhz = None
    bfe = None
    
    #gf_area = None #grand father building footprint area
    
    value = None #property value from assessment
    
    #===========================================================================
    # simulation controllers
    #===========================================================================
    def __init__(self, *vars, **kwargs):
        logger = mod_logger.getChild('House_udev')
        logger.debug('start _init_')
        
        super(House_udev, self).__init__(*vars, **kwargs) #initilzie teh baseclass 
        
        #=======================================================================
        # common setup
        #=======================================================================
        
        #=======================================================================
        # unique setup
        #=======================================================================
        if self.reset_d is None: self.reset_d = dict()
        #self.reset_d.update({'value':self.value})
        'is everything captured in the reset_d?'
        
        self.logger.debug("_init_ finished \n")
        
        """ as gis area hasnt loaded yet, we need to put this into load_data
        self.gf_area = self.gis_area"""
        
        
        
    


        

        

        

        
      
    
            
            
            

        