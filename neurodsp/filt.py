"""Filter a neural signal using a bandpass, highpass, lowpass, or bandstop filter."""

import warnings

import numpy as np
from scipy import signal

from neurodsp.plts.filt import plot_frequency_response

###################################################################################################
###################################################################################################

def filter_signal(sig, fs, pass_type, fc, n_cycles=3, n_seconds=None,
                  iir=False, butterworth_order=None,
                  plot_freq_response=False, return_kernel=False,
                  verbose=True, compute_transition_band=True, remove_edge_artifacts=True):
    """Apply a bandpass, bandstop, highpass, or lowpass filter to a neural signal.

    Parameters
    ----------
    sig : 1d array
        Time series.
    fs : float
        The sampling rate, in Hz.
    pass_type : {'bandpass', 'bandstop', 'lowpass', 'highpass'}
        Which kind of filter to apply:

        * 'bandpass': apply a bandpass filter
        * 'bandstop': apply a bandstop (notch) filter
        * 'lowpass': apply a lowpass filter
        * 'highpass' : apply a highpass filter
    fc : tuple or float
        Cutoff frequency(ies) used for filter.
        Should be a tuple of 2 floats for bandpass and bandstop.
        Can be a tuple of 2 floats, or a single float, for low/highpass.
        If float, it's taken as the cutoff frequency. If tuple, it's assumed
        as (None, f_hi) for LP, and (f_lo, None) for HP.
    n_cycles : float, optional, default: 3
        Length of filter in terms of number of cycles at 'f_lo' frequency.
        This parameter is overwritten by 'n_seconds', if provided.
    n_seconds : float, optional
        Length of filter, in seconds.
    iir : bool, optional
        If True, use an infinite-impulse response (IIR) filter.
        The only IIR filter to be used is a butterworth filter.
    butterworth_order : int, optional
        Order of the butterworth filter.
        See input 'N' in scipy.signal.butter.
    plot_freq_response : bool, optional
        If True, plot the frequency response of the filter
    return_kernel : bool, optional
        If True, return the complex filter kernel
    verbose : bool, optional
        If True, print optional information
    compute_transition_band : bool, optional
        If True, the function computes the transition bandwidth,
        defined as the frequency range between -20dB and -3dB attenuation,
        and warns the user if this band is longer than the frequency bandwidth.
    remove_edge_artifacts : bool, optional
        If True, replace the samples that are within half a kernel's length to
        the signal edge with np.nan.

    Returns
    -------
    sig_filt : 1d array
        Filtered time series.
    kernel : length-2 tuple of arrays
        Filter kernel. Only returned if 'return_kernel' is True.
    """

    if iir:
        _iir_checks(n_seconds, butterworth_order, remove_edge_artifacts)
        return filter_signal_iir(sig, fs, pass_type, fc, butterworth_order, plot_freq_response,
                                 return_kernel, compute_transition_band)
    else:
        return filter_signal_fir(sig, fs, pass_type, fc, n_cycles, n_seconds, plot_freq_response,
                                 return_kernel, compute_transition_band, remove_edge_artifacts)





def filter_signal_fir(sig, fs, pass_type, fc, n_cycles, n_seconds, plot_freq_response,
                      return_kernel, compute_transition_band, remove_edge_artifacts):
    """Words, words, words."""

    # Design filter
    kernel = design_fir_filter(pass_type, fc, n_cycles, n_seconds, fs, len(sig))

    # Compute transition bandwidth
    if compute_transition_band:
        a_vals, b_vals = 1, kernel
        check_filter_properties(b_vals, a_vals, fs, pass_type, fc)

    # Remove any NaN on the edges of 'sig'
    sig, sig_nans = _remove_nans(sig)

    # Apply filter
    sig_filt = np.convolve(kernel, sig, 'same')

    # Remove edge artifacts
    if remove_edge_artifacts:
        sig_filt = _drop_edge_artifacts(sig_filt, len(kernel))

    # Add NaN back on the edges of 'sig', if there were any at the beginning
    sig_filt = _restore_nans(sig_filt, sig_nans)

    # Plot frequency response, if desired
    if plot_freq_response:
        plot_frequency_response(fs, kernel)

    if return_kernel:
        return sig_filt, kernel
    else:
        return sig_filt


def filter_signal_iir(sig, fs, pass_type, fc, butterworth_order, plot_freq_response,
                      return_kernel, compute_transition_band):
    """Words, words, words."""

    # Design filter
    b_vals, a_vals = design_iir_filter(pass_type, fc, butterworth_order, fs)

    # Compute transition bandwidth
    if compute_transition_band:
        check_filter_properties(b_vals, a_vals, fs, pass_type, fc)

    # Remove any NaN on the edges of 'sig'
    sig, sig_nans = _remove_nans(sig)

    # Apply filter
    sig_filt = signal.filtfilt(b_vals, a_vals, sig)

    # Add NaN back on the edges of 'sig', if there were any at the beginning
    sig_filt = _restore_nans(sig_filt, sig_nans)

    # Plot frequency response, if desired
    if plot_freq_response:
        plot_frequency_response(fs, b_vals, a_vals)

    if return_kernel:
        return sig_filt, (b_vals, a_vals)
    else:
        return sig_filt


def design_fir_filter(pass_type, fc, n_cycles, n_seconds, fs, sig_length):
    """Words, words, words."""

    # Check filter definition
    f_lo, f_hi = check_filter_definition(pass_type, fc)
    filt_len = _fir_checks(pass_type, f_lo, f_hi, n_cycles, n_seconds, fs, sig_length)

    f_nyq = compute_nyquist(fs)
    if pass_type == 'bandpass':
        kernel = signal.firwin(filt_len, (f_lo, f_hi), pass_zero=False, nyq=f_nyq)
    elif pass_type == 'bandstop':
        kernel = signal.firwin(filt_len, (f_lo, f_hi), nyq=f_nyq)
    elif pass_type == 'highpass':
        kernel = signal.firwin(filt_len, f_lo, pass_zero=False, nyq=f_nyq)
    elif pass_type == 'lowpass':
        kernel = signal.firwin(filt_len, f_hi, nyq=f_nyq)

    return kernel


def design_iir_filter(pass_type, fc, butterworth_order, fs):
    """Words, words, words."""

    # Warn about only recommending IIR for bandstop
    if pass_type != 'bandstop':
        warnings.warn('IIR filters are not recommended other than for notch filters.')

    # Check filter definition
    f_lo, f_hi = check_filter_definition(pass_type, fc)

    f_nyq = compute_nyquist(fs)
    if pass_type in ('bandpass', 'bandstop'):
        win = (f_lo / f_nyq, f_hi / f_nyq)
    elif pass_type == 'highpass':
        win = f_lo / f_nyq
    elif pass_type == 'lowpass':
        win = f_hi / f_nyq

    # Design filter
    b_vals, a_vals = signal.butter(butterworth_order, win, pass_type)

    return b_vals, a_vals


def check_filter_definition(pass_type, fc):
    """Words, words, words."""

    if pass_type not in ['bandpass', 'bandstop', 'lowpass', 'highpass']:
        raise ValueError('Filter passtype not understood.')

    ## Check that frequency cutoff inputs are appropriate
    # For band filters, 2 inputs required & second entry must be > first
    if pass_type in ('bandpass', 'bandstop'):
        if isinstance(fc, tuple) and fc[0] >= fc[1]:
            raise ValueError('Second cutoff frequency must be greater than first.')
        elif isinstance(fc, (int, float)) or len(fc) != 2:
            raise ValueError('Two cutoff frequencies required for bandpass and bandstop filters')

        # Map fc to f_lo and f_hi
        f_lo, f_hi = fc

    # For LP and HP can be tuple or int/float
    #   Tuple is assumed to be (0, f_hi) for LP; (f_lo, f_nyq) for HP
    if pass_type == 'lowpass':
        if isinstance(fc, (int, float)):
            f_hi = fc
        elif isinstance(fc, tuple):
            f_hi = fc[1]
        f_lo = None

    if pass_type == 'highpass':
        if isinstance(fc, (int, float)):
            f_lo = fc
        elif isinstance(fc, tuple):
            f_lo = fc[0]
        f_hi = None

    return f_lo, f_hi


def check_filter_properties(b_vals, a_vals, fs, pass_type, fc, transitions=(-20, -3)):
    """Words, words, words."""

    f_lo, f_hi = check_filter_definition(pass_type, fc)

    # Compute the frequency response
    f_db, db = compute_frequency_response(b_vals, a_vals, fs)

    # Check that frequency response goes below transition level (has significant attenuation)
    if np.min(db) >= transitions[0]:
        warnings.warn("The filter attenuation never goes below -20dB."\
                      "Increase filter length.".format(transitions[0]))
        # If there is no attenuation, cannot calculate bands - so return here
        return

    # Check that both sides of a bandpass have significant attenuation
    if pass_type == 'bandpass':
        if db[0] >= transitions[0] or db[-1] >= transitions[0]:
            warnings.warn("The low or high frequency stopband never gets attenuated by"\
                          "more than {} dB. Increase filter length.".format(abs(transitions[0])))

    # Compute pass & transition bandwidth
    pass_bw = compute_pass_band(pass_type, fc, fs)
    transition_bw = compute_transition_band(f_db, db, transitions[0], transitions[1])

    # Raise warning if transition bandwidth is too high
    if transition_bw > pass_bw:
        warnings.warn('Transition bandwidth is  {:.1f}  Hz. This is greater than the desired'\
                      'pass/stop bandwidth of  {:.1f} Hz'.format(transition_bw, pass_bw))

    # Print out things
    print('Transition bandwidth is {:.1f} Hz.'.format(transition_bw))
    print('Pass/stop bandwidth is {:.1f} Hz'.format(pass_bw))


def compute_frequency_response(b_vals, a_vals, fs):
    """Compute frequency response."""

    w_vals, h_vals = signal.freqz(b_vals, a_vals)
    f_db = w_vals * fs / (2. * np.pi)
    db = 20 * np.log10(abs(h_vals))

    return f_db, db


def compute_pass_band(pass_type, fc, fs):
    """Compute pass bandwidth."""

    f_lo, f_hi = check_filter_definition(pass_type, fc)
    if pass_type in ['bandpass', 'bandstop']:
        pass_bw = f_hi - f_lo
    elif pass_type == 'highpass':
        pass_bw = compute_nyquist(fs) - f_lo
    elif pass_type == 'lowpass':
        pass_bw = f_hi

    return pass_bw


def compute_transition_band(f_db, db, low, high):
    """Compute transition bandwidth."""

    # This gets the indices of transitions to the values in searched for range
    inds = np.where(np.diff(np.logical_and(db > low, db < high)))[0]
    # This steps through the indices, in pairs, selecting from the vector to select from
    trans_band = np.max([(b - a) for a, b in zip(f_db[inds[0::2]], f_db[inds[1::2]])])

    return trans_band


def compute_nyquist(fs):
    """Compute the nyquist frequency."""

    return fs / 2.

###################################################################################################
###################################################################################################

def _remove_nans(sig):
    """Words, words, words."""

    sig_nans = np.isnan(sig)
    sig_removed = sig[np.where(~np.isnan(sig))]

    return sig_removed, sig_nans


def _restore_nans(sig, sig_nans):
    """Words, words, words."""

    sig_restored = np.ones(len(sig_nans)) * np.nan
    sig_restored[~sig_nans] = sig

    return sig_restored


def _drop_edge_artifacts(sig, filt_len):
    """Words, words, words."""

    n_rmv = int(np.ceil(filt_len / 2))
    sig[:n_rmv] = np.nan
    sig[-n_rmv:] = np.nan

    return sig


def _fir_checks(pass_type, f_lo, f_hi, n_cycles, n_seconds, fs, sig_length):
    """Check for running an FIR filter, including figuring out the filter length."""

    # Compute filter length if specified in seconds
    if n_seconds is not None:
        filt_len = int(np.ceil(fs * n_seconds))
    else:
        if pass_type == 'lowpass':
            filt_len = int(np.ceil(fs * n_cycles / f_hi))
        else:
            filt_len = int(np.ceil(fs * n_cycles / f_lo))

    # Force filter length to be odd
    if filt_len % 2 == 0:
        filt_len = int(filt_len + 1)

    # Raise an error if the filter is longer than the signal
    if filt_len >= sig_length:
        raise ValueError(
            """The designed filter (length: {:d}) is longer than the signal (length: {:d}).
            The filter needs to be shortened by decreasing the n_cycles or n_seconds parameter.
            However, this will decrease the frequency resolution of the filter.""".format(filt_len, sig_length))

    return filt_len


def _iir_checks(n_seconds, butterworth_order, remove_edge_artifacts):
    """Checks for using an IIR filter if called from the general filter function."""

    # Check inputs for IIR filters
    if remove_edge_artifacts:
        warnings.warn('Edge artifacts are not removed when using an IIR filter.')
    if n_seconds is not None:
        raise TypeError('n_seconds should not be defined for an IIR filter.')
    if butterworth_order is None:
        raise TypeError('butterworth_order must be defined when using an IIR filter.')
