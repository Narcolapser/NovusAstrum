import collections
import random
import math
import os
from multiprocessing import Pool

Star = collections.namedtuple('Star','mass x y z vx vy vz ax ay az')
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

#True G
#G = 6.67408e-11
#Adjusted G
G = 6.67408e-7

def random_star():
	return Star(random.random()*1000,
		random.random()*200-100,
		random.random()*200-100,
		random.random()*200-100,
		0,0,0,0,0,0)

def calc_gravity(star1, star2):
	x = star1.x - star2.x
	y = star1.y - star2.y
	z = star1.z - star2.z
	
	dist2 = x*x + y*y + z*z
	
	force = G*star1.mass*star2.mass/dist2
	
	full = math.sqrt(dist2)
	
	fx = force * x / full
	fy = force * y / full
	fz = force * z / full
	
	return (fx,fy,fz)

def create_map(galaxy):
#	process_map = {}
#	for i,star1 in enumerate(galaxy):
#		for j in range(len(galaxy))[i+1:]:
#			process_map["{}:{}".format(i,j)] = (star1,galaxy[j])
#	return process_map
	args = []
	for i,star1 in enumerate(galaxy):
		for j in range(len(galaxy))[i+1:]:
			args.append((i,j,star1,galaxy[j]))
	return map(process_item,args)

def process_item(item):
	return calc_gravity(item[0],item[1])
#	print(item)
#	return (item[0],item[1],calc_gravity(item[2],item[3]))

def reduce_map(results,galaxy):
	for star in galaxy:
		star.ax = 0
		star.ay = 0
		star.az = 0

	for key in results:
		s1,s2 = [int(i) for i in key.split(':')]
		acc = [-1.0 * galaxy[s1].mass*results[key][i] for i in range(3)]
		galaxy[s1].ax += acc[0]
		galaxy[s1].ay += acc[1]
		galaxy[s1].az += acc[2]
		
		acc = [ 1.0 * galaxy[s2].mass*results[key][i] for i in range(3)]
		galaxy[s2].ax += acc[0]
		galaxy[s2].ay += acc[1]
		galaxy[s2].az += acc[2]
	
	for star in galaxy:
		star.vx += star.ax
		star.vy += star.ay
		star.vz += star.az
	
	for star in galaxy:
		star.x += star.vx
		star.y += star.vy
		star.z += star.vz
	
	return galaxy

def print_galaxy(galaxy):
	rows, columns = os.popen('stty size', 'r').read().split()
	columns = int(columns)
	rows = int(rows) - 4
	prows = []
	
	top =		 100
	bottom =	-100
	right =		 100
	left =		-100
	
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
	result += 'Total Velocity: {}'.format(total_v).center(columns,' ') + '\n'
	#result += 'done'
	print(result)

def step(stars):
	pmap = create_map(stars)

	rmap = {}

	for key in pmap:
		rmap[key] = process_item(pmap[key[0]])
	stars = reduce_map(rmap,stars)
	return stars

def frame(galaxy,steps):
	for i in range(steps):
		galaxy = step(galaxy)
	return galaxy


if __name__ == "__main__":
	stars = [random_star() for i in range(20)]

	print_galaxy(stars)
	for i in range(100):
		stars = frame(stars,100)
		print_galaxy(stars)
