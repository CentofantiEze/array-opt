import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import numpy.random as rnd
from PIL import Image

def random_antenna_pos(x_lims = 1000, y_lims =1000):
    # Return (x,y) random location for single dish
    return rnd.random_sample(2)*np.array([x_lims,y_lims]) - np.array([x_lims, y_lims])/2

def radial_antenna_arr(n_antenna= 3, x_lims=1000, y_lims=1000, r=300):
    # Return list of 'n' antenna locations (x_i, y_i) equally spaced over a 'r' radius circumference.
    return np.array([[np.cos(angle)*r, np.sin(angle)*r] for angle in [2*np.pi/n_antenna*i for i in range(n_antenna)]])

def y_antenna_arr(n_antenna=5, r=500, alpha=0):
    # Return list of 'n' antenna locations (x_i, y_i) equispaced on three (120 deg) radial arms.
    step = r/n_antenna
    return np.array([ [np.array([(i+1)*step*np.cos(angle/180*np.pi), (i+1)*step*np.sin(angle/180*np.pi)]) for i in range(n_antenna)] for angle in [alpha, alpha+120, alpha+240] ]).reshape((3*n_antenna,2))

def random_antenna_arr(n_antenna=3, x_lims=1000, y_lims=1000):
    # Return list of 'n' antenna locations (x_i, y_i) randomly distributed.
    return np.array([random_antenna_pos(x_lims, y_lims) for i in range(n_antenna)])

def get_baselines(array):
    # Get the baseline for every combination of antennas i-j.
    # Remove the i=j baselines: np.delete(array, list, axis=0) -> delete the rows listed on 'list' from array 'array'. 
    return np.delete(np.array([antenna_i-antenna_j for antenna_i in array for antenna_j in array]), [(len(array)+1)*n for n in range(len(array))], 0)

def uv_time_int(baselines, array_latitud=35/180*np.pi,source_declination=35/180*np.pi, track_time=8, delta_t=5/60, t_0=-2):
    # visibility rotation matrix
    def M(h):
        return np.array([[np.sin(h/12*np.pi), -np.cos(h/12*np.pi), 0],
                        [-np.sin(source_declination)*np.cos(h/12*np.pi), -np.sin(source_declination)*np.sin(h/12*np.pi), np.cos(source_declination)]])
    # Baseline transformation from (north,east,elev=0) to (x,y,z)
    B = np.array([[-np.sin(array_latitud) , 0],
            [0 , -1],
            [np.cos(array_latitud) , 0]])

    n_samples = int(track_time/delta_t)
    track = []
    # Swap baselines (delta_x_i, delta_y_i) -> (delta_y_i, delta_x_i)
    baselines_sw = baselines[:,[1, 0]]
    # For each time step get the transformed uv point.
    for t in range(n_samples):
        track.append(baselines_sw.dot(B.T).dot(M(t_0+t*delta_t).T))
    # Reshape list of arrays into one long list
    return np.array(track).reshape((-1,2))


def get_uv_plane(baseline, uv_dim=128):
    # Count number of samples per uv grid
    x_lim=np.max(np.absolute(baseline))#*1.1
    y_lim=x_lim
    uv_plane, _, _ = np.histogram2d(baseline[:,0],baseline[:,1],bins=uv_dim, range=[[-x_lim,x_lim],[-y_lim,y_lim]])
    return np.fliplr(uv_plane.T)#/np.sum(uv_plane, axis=(0,1))

def get_uv_mask(uv_plane):
    # Get binary mask from the uv sampled grid
    uv_plane_mask = uv_plane.copy()
    uv_plane_mask[np.where(uv_plane>0)] = 1
    return uv_plane_mask

def get_beam(uv_mask):
    return np.abs(np.fft.ifft2(uv_mask))

def plot_beam(beam, pRng = (-0.1, 0.5), ax=None, fig=None):
    # Imshow min and max values.
    zMin = np.nanmin(beam)
    zMax = np.nanmax(beam)
    zRng = zMin - zMax
    zMin -= zRng * pRng[0]
    zMax += zRng * pRng[1]
    if ax==None or fig==None:
        fig, ax = plt.subplots(1,1)
    im = ax.imshow(np.fft.ifftshift(beam), vmin=zMin, vmax=zMax)
    fig.colorbar(im, ax=ax)
    if ax==None or fig==None:
        plt.show()

def plot_antenna_arr(array):
    fig = plt.figure(figsize=(5, 5))
    plt.scatter(array[:,0], array[:,1],s=20, c='gray')
    for i, txt in enumerate(range(1,len(array)+1,1)):
        plt.annotate(txt, (array[i,0], array[i,1]))
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        x_lim=max(abs(array[:,0]))*1.1
        y_lim=max(abs(array[:,1]))*1.1
        plt.xlim(-x_lim, x_lim)
        plt.ylim(-y_lim, y_lim)
    plt.show()

def plot_uv_plane(visibilities, n_baselines=None):
    fig = plt.figure(figsize=(5, 5))
    plt.scatter(visibilities[:,0], visibilities[:,1],s=0.4, c='gray')
    if n_baselines is not None:
        delta = int(visibilities.shape[0]/2)
        plt.scatter(visibilities[delta:delta+n_baselines,0], visibilities[delta:delta+n_baselines,1], s=2,c='k')
    plt.xlabel(r'u x $\lambda$ [m]')
    plt.ylabel(r'v x $\lambda$ [m]')
    plt.xlim([np.min(visibilities), np.max(visibilities)])
    plt.ylim([np.min(visibilities), np.max(visibilities)])
    plt.show()

def load_sky_model(path):
    return np.array(Image.open(path).convert("L"))

def plot_sky(image):
    plt.imshow(image)
    plt.show()
    print('Image shape:', image.shape)
    print('Image range: ({},{})'.format(np.min(image), np.max(image)))

def get_sky_uv(sky):
    return np.fft.fft2(sky)

def plot_sky_uv(sky_uv):
    plt.imshow(np.abs(np.fft.fftshift(sky_uv)), norm=matplotlib.colors.LogNorm())
    plt.show()

def get_obs_uv(sky_uv, mask):
    return np.fft.fftshift(sky_uv).copy()*mask

def plot_sampled_sky(sky_uv):
    plt.imshow(np.abs(sky_uv)+1e-3, norm=matplotlib.colors.LogNorm())
    plt.colorbar()
    plt.show()

def get_obs_sky(obs_uv, abs=False):
    return np.abs(np.fft.ifft2(np.fft.ifftshift(obs_uv))) if abs else np.fft.ifft2(np.fft.ifftshift(obs_uv))
