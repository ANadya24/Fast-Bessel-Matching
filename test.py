import numpy as np
import scipy as sp
from scipy import misc
from scipy.integrate import simps
import pandas as pd
from scipy.ndimage.interpolation import geometric_transform
import os
from timeit import default_timer as timer
import tqdm

def FBT(pol, m, x_net, u_net, theta_net):
    f1 = np.exp(-1j*m*theta_net)
    f2 = pol * f1
    fm = np.trapz(f2, theta_net, axis=1)
    fm = fm / (2 * np.pi)
    Fm = np.zeros(x_net.shape, dtype=fm.dtype)
#     flag = m < 0
    ff = sp.special.jn(m, u_net.reshape(-1, 1).
                       dot(x_net.reshape(1, -1))) * fm.reshape(-1,1) * u_net.reshape(-1,1)
#     ff = sp.special.jn(m, u_net.dot(x_net)) * fm * u_net

    Fm = np.trapz(np.real(ff), u_net, axis=0) + 1j * np.trapz(np.imag(ff), u_net, axis=0)
    return Fm

def polar_trfm(Im, ntheta, nrad, rmax):
    #Polar Transform
    rows, cols = Im.shape
    cx = (rows+1)/2
    cy = (cols+1)/2
#     rmax=(rows-1)/2
#     deltatheta = 2 * np.pi/(ntheta)
#     deltarad = rmax/(nrad-1)
    theta_int = np.linspace(0, 2*np.pi, ntheta)
    r_int = np.linspace(0, rmax, nrad)
    theta, radius = np.meshgrid(theta_int, r_int)
    def transform(coords):
        theta = 2.0*np.pi*coords[1] / ntheta
        radius = rmax * coords[0] / nrad
        i = cx + radius*np.cos(theta)
        j = radius*np.sin(theta) + cy
        return i, j
#     xi = radius * np.cos(theta) + cx
#     yi = radius * np.sin(theta) + cy
    PolIm = geometric_transform(Im.astype(float), transform, order=1, mode='constant', output_shape=(nrad, ntheta))
    PolIm[np.isnan(PolIm[:])] = 0
    return PolIm

B = 192
A = 64
ang_s = 2.8
ro = 7
b = ro/2
theta_net = np.linspace(0, 2*np.pi, 2*B)
x_net = np.linspace(0, B/A, 2*B/np.pi)
u_net = np.linspace(0, A, 2*B/np.pi)
k = 50
eps = np.pi/(2*k)
psi_net = np.linspace(0, 2*np.pi, int(np.pi*k))
eta_net = np.linspace(0, 2*np.pi, k)
omega_net = np.linspace(0, 2*np.pi, B)
Im1 = np.arange(-np.pi*k/2, np.pi*k/2, dtype=int)
Ih1 = np.arange(-k/2, k/2, dtype=int)
Imm = np.arange(0, B, dtype=int)

path_in = "/Users/anoshin_alexey/Documents/Projects/Fast-Bessel-Matching/"

im1 = misc.imread(path_in + "imm.png")
pol1 = polar_trfm(im1, 2*B, int(2*B/np.pi), A)

print("Precount FBM of im1")

Fm_arr = np.zeros((len(Im1) + len(Ih1) + len(Imm), len(x_net)), dtype='complex')
c2_coefs = np.zeros((len(Ih1), len(x_net)))
c1_coefs = np.zeros((len(Im1), len(x_net)))
for it_m1 in tqdm.tqdm(range(len(Im1))):
    m1 = Im1[it_m1]
    c1 = sp.special.jn(m1, b * x_net) * x_net
    c1_coefs[it_m1, :] = c1
    for it_h1 in range(len(Ih1)):
        h1 = Ih1[it_h1]
        if it_m1 == 0:
            c2 = sp.special.jn(h1, b * x_net)
            c2_coefs[it_h1, :] = c2
        for it_mm in range(len(Imm)):
            mm = Imm[it_mm]
            if Fm_arr[it_m1 + it_h1 + it_mm, :].sum() == 0:
                Fm = FBT(pol1, m1+h1+mm, x_net, u_net, theta_net)
                Fm_arr[it_m1 + it_h1 + it_mm, :] = Fm

# cols = ['GT_angle', 'GT_x', 'GT_y', 'angle', 'x', 'y','psi', 'etta', 'omega', 'time']
# df = pd.DataFrame(columns=cols)

im2 = misc.imread(path_in + "test/1/imm29.png")


start = timer()
Tf = np.zeros((len(Im1), len(Ih1), len(Imm)), dtype='complex')
print(Tf.shape)
pol2 = polar_trfm(im2, int(2*B), int(2*B/np.pi), A)

Gm_arr = np.zeros((len(Imm), len(x_net)), dtype='complex')
for it_mm in range(len(Imm)):
            mm = Imm[it_mm]
            Gm_arr[it_mm] = FBT(pol2, mm, x_net, u_net, theta_net)

for it_m1 in tqdm.tqdm(range(len(Im1))):
    m1 = Im1[it_m1]
    # c1 = sp.special.jn(m1, b * x_net) * x_net
    c1 = c1_coefs[it_m1, :]
    for it_h1 in range(len(Ih1)):
        h1 = Ih1[it_h1]
        c2 = c2_coefs[it_h1, :] * c1
        # c2 = sp.special.jn(h1, b * x_net) * c1
        for it_mm in range(len(Imm)):
            mm = Imm[it_mm]
            coef = 2*np.pi * np.exp(1j*(h1+mm)*eps)
            # Fm = FBT(pol1, m1+h1+mm, x_net, u_net, theta_net)
#             Fm_arr[it_m1 + it_h1 + it_mm] = Fm
            Fm = Fm_arr[it_m1 + it_h1 + it_mm]
            Gm = Gm_arr[it_mm]
            func = Fm*np.conj(Gm)*c2
            Tf[it_m1, it_h1, it_mm] = np.trapz(sp.real(func), x_net) \
                                      + 1j*np.trapz(sp.imag(func), x_net)
            Tf[it_m1, it_h1, it_mm] *= coef

# for it_m1 in tqdm.tqdm(range(len(Im1))):
#     m1 = Im1[it_m1]
#     c1 = sp.special.jn(m1, b * x_net) * x_net
#     for it_h1 in range(len(Ih1)):
#         h1 = Ih1[it_h1]
#         # c2 = c2_coefs[it_m1, it_h1, :]
#         c2 = sp.special.jn(h1, b * x_net) * c1
#         for it_mm in range(len(Imm)):
#             mm = Imm[it_mm]
#             coef = 2*np.pi * np.exp(1j*(h1+mm)*eps)
#             # Fm = FBT(pol1, m1+h1+mm, x_net, u_net, theta_net)
# #             Fm_arr[it_m1 + it_h1 + it_mm] = Fm
#             Fm = Fm_arr[it_m1 + it_h1 + it_mm]
#             Gm = FBT(pol2, mm, x_net, u_net, theta_net)
#             func = Fm*np.conj(Gm)*c2
#             Tf[it_m1, it_h1, it_mm] = np.trapz(sp.real(func), x_net) \
#                                       + 1j*np.trapz(sp.imag(func), x_net)
#             Tf[it_m1, it_h1, it_mm] = Tf[it_m1, it_h1, it_mm] * coef

T = np.fft.ifftn(Tf)
# print(T.shape)
[ipsi, ietta, iomegga] = np.unravel_index(np.argmax(T, axis=None), T.shape)

psi = psi_net[ipsi]
etta = eta_net[ietta]
omegga = omega_net[iomegga]
print(b, np.degrees(psi), np.degrees(etta-psi), np.degrees(omegga-etta))
alpha = eps + omegga
# phi = omegga - etta - psi #np.angle( np.exp(1j*(etta - psi + eps)))
# rho = np.abs(b * np.sqrt(2*(1 + np.cos(etta - psi + eps))))
rho = np.abs(np.complex(b+b*np.exp(etta - psi + eps)))
phi = np.angle(np.exp(1j*psi)*b*(1 + np.exp(1j*(etta - psi + eps))))
x = rho * np.cos(phi)
y = rho * np.sin(phi)
# x1 = rho * np.cos(phi)
# y1 = rho * np.sin(phi)
a = alpha * 180 / np.pi - 360
end = timer()
time = end - start
print(abs(alpha * 180 / np.pi - 360))
# print(x, y, rho)
