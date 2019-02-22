"""
Lagged Coherence
================

Compute lagged coherence on neural signals.

This tutorial primarily covers :mod:`neurodsp.laggedcoherence`.
"""

###################################################################################################
#
# Overview
# --------
#
# Lagged coherence is a measure to quantify the rhythmicity of neural signals.
#
# For more details on the lagged coherence measure see Fransen et al., 2015, Neuroimage.
#

###################################################################################################

import numpy as np
import matplotlib.pyplot as plt

from neurodsp.laggedcoherence import lagged_coherence

###################################################################################################

# Set the random seed, for consistency simulating data
np.random.seed(0)

###################################################################################################
#
# Simulate signal with oscillatory bursts
# ---------------------------------------
#

###################################################################################################

# Parameters for simulated signal
n_samples = 5000
fs = 1000
burst_freq = 10
burst_starts = [0, 3000]
burst_seconds = 1
burst_samples = burst_seconds*fs

###################################################################################################

# Design burst kernel
burst_kernel_t = np.arange(0, burst_seconds, 1/fs)
burst_kernel = 2*np.sin(burst_kernel_t*2*np.pi*burst_freq)

# Generate random signal with bursts
times = np.arange(0, n_samples/fs, 1/fs)
sig = np.random.randn(n_samples)
for ind in burst_starts:
    sig[ind:ind+burst_samples] += burst_kernel

###################################################################################################

# Plot example signal
plt.figure(figsize=(12, 3))
plt.plot(times, sig, 'k')

###################################################################################################
#
# Compute lagged coherence for an alpha oscillation
# -------------------------------------------------
#

f_range = (8, 12)
lag_coh_alpha = lagged_coherence(sig, f_range, fs)
print('Lagged coherence = ', lag_coh_alpha)

###################################################################################################
#
# Compute lagged coherence across the frequency spectrum
# ------------------------------------------------------
#
# Notice that lagged coherence peaks around 10Hz (the frequency of our
# oscillator), but it is not very specific to that frequency.
#

lag_coh_by_f, freqs = lagged_coherence(sig, (1, 40), fs, return_spectrum=True)

# Visualize lagged coherence as a function of frequency
plt.figure(figsize=(6, 3))
plt.plot(freqs, lag_coh_by_f, 'k.-')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Lagged coherence')
plt.tight_layout()

###################################################################################################
#
# Compute lagged coherence for time segments with and without burst
# -----------------------------------------------------------------
#
# Note that lagged coherence is greater when analyzing a neural signal that
# has a burst in the frequency range of interest, compared to a signal that
# does not have an oscillator.
#

samp_burst = np.arange(1000)
samp_noburst = np.arange(1000, 2000)

lag_coh_burst = lagged_coherence(sig[samp_burst], f_range, fs)
lag_coh_noburst = lagged_coherence(sig[samp_noburst], f_range, fs)
print('Lagged coherence, bursting = ', lag_coh_burst)
print('Lagged coherence, not bursting = ', lag_coh_noburst)

###################################################################################################
#
# Compute lagged coherence of an example neural signal
# ----------------------------------------------------
#

# Load signal
sig = np.load('./data/sample_data_1.npy')
sig_filt_true = np.load('./data/sample_data_1_filt.npy')
fs = 1000
times = np.arange(0, len(sig)/fs, 1/fs)
f_range = (13, 30)

###################################################################################################

# Plot example signal
plt.figure(figsize=(12, 3))
plt.plot(times, sig, 'k')
plt.xlim((0, 5))
plt.xlabel('Time (s)')
plt.ylabel('Voltage (uV)')
plt.tight_layout()

###################################################################################################

f_range = (13, 30)
lag_coh_beta = lagged_coherence(sig, f_range, fs)
print('Lagged coherence = ', lag_coh_beta)

###################################################################################################
#
# Sphinx settings:
# sphinx_gallery_thumbnail_number = 2
#
