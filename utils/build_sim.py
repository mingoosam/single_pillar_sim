import meep as mp

def build_sim(params):

    geometry = [mp.Block(size=mp.Vector3(mp.inf,mp.inf, params['pml']['thickness'] 
                                        + params['fusedSilica']['width']), 
                         center=mp.Vector3(0,0,params['fusedSilica']['center']),
                         material=mp.Medium(index=params['fusedSilica']['n'])),

                mp.Block(size=mp.Vector3(mp.inf,mp.inf, params['amorphousSi']['height'] 
                                        + params['PDMS']['width'] + params['pml']['thickness']),
                         center=mp.Vector3(0,0,params['PDMS']['center']),
                         material=mp.Medium(index=params['PDMS']['n']))]

    sources = [mp.Source(mp.ContinuousSource(frequency=params['freq']),
                    component=params['source']['cmpt'],
                    center=mp.Vector3(0,0,params['source']['center']),
                    size=mp.Vector3(params['cell']['x'],params['cell']['y'],0))]

    sim = mp.Simulation(cell_size=params['cell_size'],
                    geometry=geometry,
                    sources=sources,
                    k_point=params['k_point'],
                    boundary_layers=params['pml']['layers'],
                    symmetries=params['symmetries'],
                    resolution=params['resolution'])

    flux_region = mp.FluxRegion(center=mp.Vector3(0,0,params['flux']['center']), 
                            size=mp.Vector3(params['cell']['x'], params['cell']['y'], 0))

    
    flux_object = sim.add_flux(params['freq'], params['flux']['df'],
                               params['flux']['nfreq'], flux_region)

    return geometry, sources, sim, flux_region, flux_object

