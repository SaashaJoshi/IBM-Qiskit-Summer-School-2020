import numpy as np

def get_transmon(dt):
  from qiskit.providers.aer.pulse import duffing_system_model
  dim_oscillators = 3
  oscillator_freqs = [5.042e9]
  anharm_freqs = [-0.33e9]
  drive_strengths = [0.02e9]
  coupling_dict = {}
  
  return duffing_system_model(dim_oscillators=dim_oscillators,
                              oscillator_freqs=oscillator_freqs,
                              anharm_freqs=anharm_freqs,
                              drive_strengths=drive_strengths,
                              coupling_dict=coupling_dict,
                              dt=dt)
  
  

def get_params(exp_type, gv):
  
  exp_dict = {}

  if exp_type == 'rabi':
    exp_dict = {
      'experiments': gv['rabi_schedules'],
      'backend': gv['backend_sim'],
      'qubit_lo_freq': gv['qubit_lo_freq'],
      'meas_level': 1,
      'meas_return': 'avg',
      'shots': 512
      }

  if exp_type == 'ramsey':
    sb_freq = 8.675309e6
    exp_dict = {
      'experiments': gv['ramsey_schedules'],
      'backend': gv['backend_sim'],
      'qubit_lo_freq': [gv['qubit_lo_freq'][0]+sb_freq],
      'meas_level': 1,
      'meas_return': 'avg',
      'shots': 512
      }

  if exp_type == 'spec01':
    exp_dict = {
      'experiments': gv['spec_schedules'],
      'backend': gv['backend_sim'],
      'qubit_lo_freq': gv['qubit_lo_freq'],
      'meas_level': 1,
      'meas_return': 'avg',
      'shots': 512
      }
  
  if exp_type == 'spec12':
    exp_dict = {
      'experiments': gv['spec_schedules'],
      'backend': gv['backend_sim'],
      'qubit_lo_freq': gv['qubit_lo_freq'],
      'meas_level': 1,
      'meas_return': 'avg',
      'shots': 512
      }

  return exp_dict

def sinusoid(x, A, B, drive_period, phi):
  return A*np.cos(2*np.pi*x/drive_period - phi) + B

def fit_sinusoid(x_vals, y_vals, init_params):
  from scipy.optimize import curve_fit  

  fit_params, conv = curve_fit(sinusoid, x_vals, y_vals, init_params)
  y_fit = sinusoid(x_vals, *fit_params)
  
  return fit_params, y_fit

def lorentzian(x, A, q_freq, B, C):
  return (A/np.pi)*(B/((x-q_freq)**2 + B**2)) + C

def fit_lorentzian(x_vals, y_vals, init_params):
  from scipy.optimize import curve_fit  

  fit_params, conv = curve_fit(lorentzian, x_vals, y_vals, init_params)
  y_fit = lorentzian(x_vals, *fit_params)
  
  return fit_params, y_fit

def apply_sideband(pulse, sb_freq, dt):
  from qiskit.pulse import SamplePulse
  
  t_samples = np.linspace(0, dt*pulse.duration, pulse.duration)
  sine_pulse = np.sin(2*np.pi*sb_freq*t_samples)
 
  sideband_pulse = SamplePulse(np.multiply(np.real(pulse.samples), sine_pulse), name='sideband_pulse')

  return sideband_pulse

def get_values_from_result(exp_result, qubit):

  exp_values = []
  for ii in range(len(exp_result.get_counts())):
    exp_values.append(np.real(exp_result.get_memory(ii)[qubit]))

  return exp_values
