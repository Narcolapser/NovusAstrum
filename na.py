import collections
import random
import math
import os
import time
from multiprocessing import Pool

min_distance = 1

#True G
#G = 6.67408e-11
#Adjusted G
G = 6.67408e-5

#Star = collections.namedtuple('Star','mass x y z vx vy vz ax ay az')
class Star (object):

    def __init__(self,mass,x,y,z,vx,vy,vz,ax,ay,az):
        self.mass = mass
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.ax = ax
        self.ay = ay
        self.az = az

    def __repr__(self):
        return str((self.mass,self.x,self.y,self.z,self.vx,self.vy,self.vz,self.ax,self.ay,self.az))
    
    def calc_accel(self,galaxy):
        fx = 0
        fy = 0
        fz = 0
        
        for star in galaxy:
            x = star.x - self.x
            y = star.y - self.y
            z = star.z - self.z
            
            dist2 = x*x + y*y + z*z
            if dist2 < min_distance:
                # This is done to prevent stars that are too close causing crazy
                # things to happen. And prevent a star moving on its self.
                continue
            
            force = G*star.mass*self.mass/dist2
            
            full = math.sqrt(dist2)
            
            fx += force * x / full
            fy += force * y / full
            fz += force * z / full
        
        self.ax = fx / self.mass
        self.ay = fy / self.mass
        self.az = fz / self.mass
        
        return self
        
    def calc_move(self):
        self.vx += self.ax
        self.vy += self.ay
        self.vz += self.az
        
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        return self



def random_star():
    return Star(random.random()*1000,
        random.random()*200-100,
        random.random()*200-100,
        random.random()*200-100,
        0,0,0,0,0,0)

def print_galaxy(galaxy,start):
    rows, columns = os.popen('stty size', 'r').read().split()
    columns = int(columns)
    rows = int(rows) - 4 - 2
    prows = []
    
    top =         100
    bottom =    -100
    right =         100
    left =        -100
    
    vincrement = (top - bottom)/rows
    hincrement = (right - left)/columns

    result = "Novus Astrum 2D viewer".center(columns,' ') + '\n'

    for row in range(rows):
        prow = []
        for star in galaxy:
            if (top - vincrement * row) > star.y > (top - vincrement * (row + 1)):
                prow.append(star)
        prows.append(prow)
    
    for row in range(rows):
        if len(prows[row]) == 0:
            result += '\n'
        else:
            out_row = ''
            for col in range(columns):
                star_present = False
                for star in prows[row]:
                    if (right - hincrement * col) > star.x > (right - hincrement * (col + 1)):
                        star_present = True
                out_row += '*' if star_present else ' '
            result += out_row + '\n'
    
    total_v = sum([abs(s.vx)+abs(s.vy)+abs(s.vz) for s in galaxy])
    result += 'Total Velocity: {} Seconds per frame: {}'.format(total_v,time.time()-start).center(columns,' ') + '\n'
    #result += 'done'
    print(result)

def step(stars):
    for star in stars:
        star.calc_accel(stars)
    for star in stars:
        star.calc_move()
    return stars

def calc_star_accel(vals):
    return vals[0].calc_accel(vals[1])

def calc_star_move(star):
    return star.calc_move()

pool = Pool(processes=24)
def pool_step(stars):
    stars2 = pool.map(calc_star_accel,[(star,stars) for star in stars])
    stars3 = pool.map(calc_star_move,stars2)
#    for star in stars2:
#        star.calc_move()
    return stars3

def frame(galaxy,steps):
    for i in range(steps):
#        galaxy = step(galaxy)
        galaxy = pool_step(galaxy)
    return galaxy


if __name__ == "__main__":
    stars = [random_star() for i in range(10000)]

    for i in range(1):
        start = time.time()
        stars = frame(stars,100)
        print_galaxy(stars,start)
