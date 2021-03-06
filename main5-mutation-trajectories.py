import pickle
import csv
import numpy as np
from numpy import linalg as LA
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout, Flatten
from keras.utils import np_utils
from keras.layers.convolutional import Convolution1D
from keras.layers.convolutional import MaxPooling1D
from utils_EC2 import *
from keras.layers.normalization import BatchNormalization
from keras.models import load_model 

# get dict of PI:plasmid counts above threshold
max_seq_length = 8000
cnn_filter_length = 48

# load data
sorted_pi_list = np.load('/mnt/sorted_pi_list.out')
model = load_model('best_model.h5')
print("Loaded model")
print(model.summary())

# make model that ends at last neuron pre-softmax
c1 = model.get_layer("conv1d_1")
b1 = model.get_layer("batch_normalization_1")
d1 = model.get_layer("dense_1")
b2 = model.get_layer("batch_normalization_2")
d2 = model.get_layer("dense_2")
model2 = Sequential()
model2.add(Convolution1D(input_shape=(16048,4), filters=128, kernel_size=12, \
                        activation="relu", padding="same", weights=c1.get_weights()))
model2.add(MaxPooling1D(pool_size=16048))
model2.add(BatchNormalization(weights=b1.get_weights()))
model2.add(Flatten())
model2.add(Dense(input_dim=128,units=64, weights=d1.get_weights()))
model2.add(Activation("relu"))
model2.add(BatchNormalization(weights=b2.get_weights()))
model2.add(Dense(units=827, weights=d2.get_weights()))
model2.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=["accuracy"])

num_trajectories = 30 # how many mutation trajectories total
steps_per_trajectory = 1000 # how many mutations per trajectory
fail_point = np.zeros(num_trajectories)
all_trajectories = np.zeros((num_trajectories,steps_per_trajectory))

for traj in range(num_trajectories):
    
    # pCI-YFP
    unpadded_seq = ['TACTAGTAGCGGCCGCTGCAGTCCGGCAAAAAAACGGGCAAGGTGTCACCACCCTGCCCTTTTTCTTTAAAACCGAAAAGATTACTTCGCGTTATGCAGGCTTCCTCGCTCACTGACTCGCTGCGCTCGGTCGTTCGGCTGCGGCGAGCGGTATCAGCTCACTCAAAGGCGGTAATCTCGAGTCCCGTCAAGTCAGCGTAATGCTCTGCCAGTGTTACAACCAATTAACCAATTCTGATTAGAAAAACTCATCGAGCATCAAATGAAACTGCAATTTATTCATATCAGGATTATCAATACCATATTTTTGAAAAAGCCGTTTCTGTAATGAAGGAGAAAACTCACCGAGGCAGTTCCATAGGATGGCAAGATCCTGGTATCGGTCTGCGATTCCGACTCGTCCAACATCAATACAACCTATTAATTTCCCCTCGTCAAAAATAAGGTTATCAAGTGAGAAATCACCATGAGTGACGACTGAATCCGGTGAGAATGGCAAAAGCTTATGCATTTCTTTCCAGACTTGTTCAACAGGCCAGCCATTACGCTCGTCATCAAAATCACTCGCATCAACCAAACCGTTATTCATTCGTGATTGCGCCTGAGCGAGACGAAATACGCGATCGCTGTTAAAAGGACAATTACAAACAGGAATCGAATGCAACCGGCGCAGGAACACTGCCAGCGCATCAACAATATTTTCACCTGAATCAGGATATTCTTCTAATACCTGGAATGCTGTTTTCCCGGGGATCGCAGTGGTGAGTAACCATGCATCATCAGGAGTACGGATAAAATGCTTGATGGTCGGAAGAGGCATAAATTCCGTCAGCCAGTTTAGTCTGACCATCTCATCTGTAACATCATTGGCAACGCTACCTTTGCCATGTTTCAGAAACAACTCTGGCGCATCGGGCTTCCCATACAATCGATAGATTGTCGCACCTGATTGCCCGACATTATCGCGAGCCCATTTATACCCATATAAATCAGCATCCATGTTGGAATTTAATCGCGGCCTCGAGCAAGACGTTTCCCGTTGAATATGGCTCATAACACCCCTTGTATTACTGTTTATGTAAGCAGACAGTTTTATTGTTCATGATGATATATTTTTATCTTGTGCAATGTAACATCAGAGATTTTGAGACACAACGTGGCTTTGTTGAATAAATCGAACTTTTGCTGAGTTGAAGGATCAGATCACGCATCTTCCCGACAACGCAGACCGTTCCGTGGCAAAGCAAAAGTTCAAAATCACCAACTGGTCCACCTACAACAAAGCTCTCATCAACCGTGGCTCCCTCACTTTCTGGCTGGATGATGGGGCGATTCAGGCCTGGTATGAGTCAGCAACACCTTCTTCACGAGGCAGACCTCAGCGCTAGCGGAGTGTATACTGGCTTACTATGTTGGCACTGATGAGGGTGTCAGTGAAGTGCTTCATGTGGCAGGAGAAAAAAGGCTGCACCGGTGCGTCAGCAGAATATGTGATACAGGATATATTCCGCTTCCTCGCTCACTGACTCGCTACGCTCGGTCGTTCGACTGCGGCGAGCGGAAATGGCTTACGAACGGGGCGGAGATTTCCTGGAAGATGCCAGGAAGATACTTAACAGGGAAGTGAGAGGGCCGCGGCAAAGCCGTTTTTCCATAGGCTCCGCCCCCCTGACAAGCATCACGAAATCTGACGCTCAAATCAGTGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCTGGCGGCTCCCTCGTGCGCTCTCCTGTTCCTGCCTTTCGGTTTACCGGTGTCATTCCGCTGTTATGGCCGCGTTTGTCTCATTCCACGCCTGACACTCAGTTCCGGGTAGGCAGTTCGCTCCAAGCTGGACTGTATGCACGAACCCCCCGTTCAGTCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGAAAGACATGCAAAAGCACCACTGGCAGCAGCCACTGGTAATTGATTTAGAGGAGTTAGTCTTGAAGTCATGCGCCGGTTAAGGCTAAACTGAAAGGACAAGTTTTGGTGACTGCGCTCCTCCAAGCCAGTTACCTCGGTTCAAAGAGTTGGTAGCTCAGAGAACCTTCGAAAAACCGCCCTGCAAGGCGGTTTTTTCGTTTTCAGAGCAAGAGATTACGCGCAGACCAAAACGATCTCAAGAAGATCATCTTATTAAGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGAGACCCACGCTCACCGGCTCCAGATTTATCAGCAATAAACCAGCCAGCCGGAAGGGCCGAGCGCAGAAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGTCTATTCCATGGTGCCACCTGACGTCTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAGGCGTATCACGAGGCAGAATTTCAGATAAAAAAAATCCTTAGCTTTCGCTAAGGATGATTTCTGGAATTCGCGGCCGCTTCTAGAGTAACACCGTGCGTGTTGACTATTTTACCTCTGGCGGTGATAATGGTTGCTACTAGAGAAAGAGGAGAAATACTAGATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAGTTCAGCGTGTCCGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCAAGCTGCCCGTGCCCTGGCCCACCCTCGTGACCACCTTCGGCTACGGCCTGCAATGCTTCGCCCGCTACCCCGACCACATGAAGCTGCACGACTTCTTCAAGTCCGCCATGCCCGAAGGCTACGTCCAGGAGCGCACCATCTTCTTCAAGGACGACGGCAACTACAAGACCCGCGCCGAGGTGAAGTTCGAGGGCGACACCCTGGTGAACCGCATCGAGCTGAAGGGCATCGACTTCAAGGAGGACGGCAACATCCTGGGGCACAAGCTGGAGTACAACTACAACAGCCACAACGTCTATATCATGGCCGACAAGCAGAAGAACGGCATCAAGGTGAACTTCAAGATCCGCCACAACATCGAGGACGGCAGCGTGCAGCTCGCCGACCACTACCAGCAGAACACCCCCATCGGCGACGGCCCCGTGCTGCTGCCCGACAACCACTACCTGAGCTACCAGTCCGCCCTGAGCAAAGACCCCAACGAGAAGCGCGATCACATGGTCCTGCTGGAGTTCGTGACCGCCGCCGGGATCACTCTCGGCATGGACGAGCTGTACAAGTAATAATACTAGAGCCAGGCATCAAATAAAACGAAAGGCTCAGTCGAAAGACTGGGCCTTTCGTTTTATCTGTTGTTTGTCGGTGAACGCTCTCTACTAGAGTCACACTGGCTCACCTTCGGGTGGGCCTTTCTGCGTTTATA','N']
    
    # randomly pick random locations for mutagenesis, without replacement
    muts = np.random.choice(len(unpadded_seq[0]), steps_per_trajectory, replace=False)
    
    for mut in range(len(muts)):
        
        mut_location = muts[mut]
        mut_letter = np.random.randint(3) # only three because removing the actual one in next step
        alternate_letters = ['A','T','G','C']
        alternate_letters.remove(unpadded_seq[0][mut_location])
        
        # make edit to a different nucleotide at mut location
        unpadded_seq[0] = unpadded_seq[0][:mut_location] + alternate_letters[mut_letter] + unpadded_seq[0][mut_location+1:]
        dna_seq_of_interest = pad_dna(unpadded_seq,max_seq_length)
        dna_seq_of_interest = append_rc(dna_seq_of_interest,cnn_filter_length)
        total_plasmid_size = len(dna_seq_of_interest[-1])
        interest_dna_seqs_onehot = np.transpose(convert_onehot2D(dna_seq_of_interest), axes=(0,2,1))

        # calculate output probability for voigt lab
        predicted_vector = model.predict(np.expand_dims(interest_dna_seqs_onehot[0], axis=0),verbose=0)[0]
        out_vector = model2.predict(np.expand_dims(interest_dna_seqs_onehot[0], axis=0),verbose=0)[0] #output neuron no softmax
        voigt_prob = predicted_vector[745]
        if fail_point[traj] == 0 and np.argmax(predicted_vector) != 745: #check if voigt still top prediction
            fail_point[traj] = mut
        all_trajectories[traj][mut] = voigt_prob

# print average num muts for failed prediction, save trajectories
print("Average number of mutations = ", np.mean(fail_point))
np.savetxt('mutation_trajectories.out', all_trajectories, delimiter=',')




