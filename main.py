import os
import sys
import pickle
from tqdm import tqdm

import meep as mp
import matplotlib.pyplot as plt
from IPython.display import Video, display
import cv2
import numpy as np

from utils.update_config import update as update_config
from utils.helpers import load_config, is_mpi_run, delete_outputs, create_folder
from utils.visualizations import display_fields, display_video, display_chars, animate
from utils.build_sim import build_sim

from IPython import embed


def run_experiment(params, geometry, sources, sim, flux_region, flux_object):

    ## Initial run without pillars
    sim.run(until=200)

    initial_flux = mp.get_fluxes(flux_object)[0]  # flux through substrate and PDMS - no pillar  
   
    sim.reset_meep()
 
    data = np.zeros((3,params['experiment']['num']))

    pbar = tqdm(total=params['experiment']['num'],leave=False)
    for i,radius in enumerate(np.linspace(params['amorphousSi']['radius_min'],
                                          params['amorphousSi']['radius_max'],
                                          num=params['experiment']['num'])):

        geometry.append(mp.Cylinder(radius=radius,
                            height=params['amorphousSi']['height'],
                            axis=mp.Vector3(0,0,1),
                            center=mp.Vector3(0,0,params['amorphousSi']['center']),
                            material=mp.Medium(index=params['amorphousSi']['n'])))
    
        sim = mp.Simulation(cell_size=params['cell_size'],
                            geometry=geometry,
                            sources=sources,
                            k_point=params['k_point'],
                            boundary_layers=params['pml']['layers'],
                            symmetries=params['symmetries'],
                            resolution=params['resolution'])
        
        flux_object = sim.add_flux(params['freq'], params['flux']['df'],
                                   params['flux']['nfreq'], flux_region)  
    
        sim.run(until=200)

        res = sim.get_eigenmode_coefficients(flux_object, [1], eig_parity=mp.ODD_Y)
        coeffs = res.alpha
    
        flux = abs(coeffs[0,0,0]**2)
        phase = np.angle(coeffs[0,0,0]) 
        
        data[0,i] = radius
        data[1,i] = flux / initial_flux 
        data[2,i] = phase
        
        if radius < params['amorphousSi']['radius_max']:
            sim.reset_meep()
            geometry.pop()

        pbar.update(1)
    
    pbar.close()

    return data, sim
    
if __name__=="__main__":

    params = load_config(sys.argv)
    params = update_config(params)

    geometry, sources, sim, flux_region, flux_object = build_sim(params)

    rel_path = 'vis'
    abs_path = os.path.abspath(rel_path)
    create_folder(abs_path)

    if params['experiment']['animate'] == 1:

        if is_mpi_run():

            print("Error: MPI detected. Please do not use mpirun to generate animations.")         
            sys.exit(1)

        else:

            print("problem")

        radius = 0.1625
        geometry.append(mp.Cylinder(radius=radius,
                            height=params['amorphousSi']['height'],
                            axis=mp.Vector3(0,0,1),
                            center=mp.Vector3(0,0,params['amorphousSi']['center']),
                            material=mp.Medium(index=params['amorphousSi']['n'])))

        sim = mp.Simulation(cell_size=params['cell_size'],
                            geometry=geometry,
                            sources=sources,
                            k_point=params['k_point'],
                            boundary_layers=params['pml']['layers'],
                            symmetries=params['symmetries'],
                            resolution=params['resolution'])

       
        video_path = f"vis/animation_radius_{radius}.mp4"
        animate(params, sim, geometry, radius, video_path)        
        display_video(video_path)

    elif params['experiment']['animate'] == 0:

        data, sim = run_experiment(params, geometry, sources, sim, flux_region, flux_object)
        eps_data = sim.get_epsilon()
        display_fields(params, sim, rad=data[0,-1])
        display_chars(params, data)
        delete_outputs(params) # comment this line if you want to preserve the output files

    else:
        raise NotImplementedError 

