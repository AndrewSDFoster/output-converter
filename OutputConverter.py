from mpi4py import MPI
import numpy as np
from config.py import *
import src

'''
 * MPI CommLoop - Python Worker
 * by Madison Stemm
 * Completed 3/24/2014
 *
 * This file is part of CommLoop.
 *
 * CommLoop is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * CommLoop is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CommLoop.  If not, see <http://www.gnu.org/licenses/>.
'''

#asdf: this will only have one type of worker, deleting irrelevant code, 
#see http://github.com/astromaddie/commloop for full worker.py implementation

# Open communications with the Master
comm = MPI.Comm.Get_parent()
rank  = comm.Get_rank()
size  = comm.Get_size()

################### MPI Functions ###################
def comm_scatter(array):
  comm.Barrier()
  comm.Scatter(None, array, root=0)
  return array

def comm_gather(array, type):
  comm.Barrier()
  comm.Gather([array, type], None, root=0)

def comm_barrier():
  comm.Barrier()

def worker_loop(placeholder, starfl, RpRs):
  for i in range(len(filters)):
    spectrum = comm_scatter(placeholder)
    specrat  = (spectrum/starfl)*RpRs*RpRs
    integrated = wine.bandintegrate(spectrum, specwn, nifilter[i], wnindices[i])
    comm_gather(integrated, MPI.DOUBLE)
  
#####################################################

#allocate memory, things of indeterminate size are empty lists that will be
#appended to
filtwaven  = np.ones(len(filters), dtype="double")
filttransm = np.ones(len(filters), dtype="double")
nifilter   = []
istarfl    = []
wnindices  = []

#Initialization:
#get stellar model
starfl, starwn, tmodel, gmodel = wine.readkurucz(kuruczfile, Tstar, logg)

#for each filter, read the filter and resample it, record everything
for i in range(len(filters)):
  filtwaven[i], filttransm[i] 	= wine.readfilter(filters[i])
  nifilt, strfl, wnind		= wine.resample(specwn, filtwaven, \
						filttransm, starwn, starfl)
  nifilter.append(nifilter)
  istarfl.append(strfl)
  wnindices.append(wnind)

#create MPI passing arrays
spectrumsize = len(wnindices[1])
placeholder = np.ones(spectrumsize, dtype='d')
end_loop = np.zeros(1, dtype='i')

# Worker loop, communicating with Master
while end_loop[0] == False:
  worker_loop(placeholder, starfl, RpRs) #ASK PATRICIO what kurucz model to use
  end_loop = comm_scatter(end_loop)

# Close communications and disconnect
comm.Barrier()
comm.Disconnect()
