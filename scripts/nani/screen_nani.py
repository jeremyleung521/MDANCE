import sys
sys.path.insert(0, "../../")
import numpy as np
from src.modules.kmeansNANI.nani import KmeansNANI, compute_scores
from src.tools.bts import extended_comparison
import os

# System info
input_traj_numpy = '../../examples/md/backbone.npy'
N_atoms = 50
sieve = 1

# NANI parameters
output_dir = 'outputs'                        
init_types = ['comp_sim']
metric = 'MSD'
start_n_clusters = 5
end_n_clusters = 30

if __name__ == '__main__':
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    traj_numpy = np.load(input_traj_numpy)[::sieve]
    for init_type in init_types:
        if init_type in ['k-means++', 'random', 'vanilla_kmeans++']:
            percentage = ''
        
        # `comp_sim` and `div_select` are ran only once to get the initiators
        elif init_type in ['comp_sim', 'div_select']:
            percentage = 10
            mod = KmeansNANI(data=traj_numpy, n_clusters=end_n_clusters-1, metric=metric, 
                             N_atoms=N_atoms, init_type=init_type, percentage=percentage)
            initiators = mod.initiate_kmeans()
        
        all_scores = []
        for i in range(start_n_clusters, end_n_clusters):
            total = 0

            # Run k-means clustering
            if init_type in ['comp_sim', 'div_select']:
                mod = KmeansNANI(data=traj_numpy, n_clusters=i, metric=metric, 
                                 N_atoms=N_atoms, init_type=init_type, percentage=percentage)
                labels, centers, n_iter = mod.kmeans_clustering(initiators)
            elif init_type in ['k-means++', 'random']:
                mod = KmeansNANI(data=traj_numpy, n_clusters=i, metric=metric, 
                                 N_atoms=N_atoms, init_type=init_type)
                labels, centers, n_iter = mod.kmeans_clustering(initiators=init_type)
            elif init_type == 'vanilla_kmeans++':
                mod = KmeansNANI(data=traj_numpy, n_clusters=i, metric=metric, 
                                 N_atoms=N_atoms, init_type=init_type)
                initiators = mod.initiate_kmeans()
                labels, centers, n_iter = mod.kmeans_clustering(initiators=initiators)
            
            
            # Compute scores
            ch_score, db_score = compute_scores(data=traj_numpy, labels=labels)
            
            # Calculate MSD for each cluster
            dict = {}
            for j in range(i):
                dict[j] = np.where(labels == j)[0]
                dict[j] = traj_numpy[dict[j]]
            for key in dict:
                msd = extended_comparison(np.array(dict[key]), traj_numpy_type='full', 
                                          metric=metric, N_atoms=N_atoms)
                total += msd
            all_scores.append((i, n_iter, ch_score, db_score, total/i))
        
        all_scores = np.array(all_scores)
        header = f'init_type: {init_type}, percentage: {percentage}, metric: {metric}, sieve: {sieve}\n'
        header += 'Number of clusters, Number of iterations, Calinski-Harabasz score, Davies-Bouldin score, Average MSD'
        np.savetxt(f'{output_dir}/{percentage}{init_type}_summary.csv', all_scores, 
                   delimiter=',', header=header, fmt='%s')