import random
import math
import os

#Star = collections.namedtuple('Star','mass x y z vx vy vz ax ay az')

# True G
# G = 6.67408e-11
# Adjusted G
G = 6.67408e-7

class Star (object):

	def __init__(self,mass,x,y,z,vx,vy,vz,ax,ay,az,sid):
		self.sid = sid if sid else random.randint(0,1000000000)
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
		return str((self.sid,self.mass,self.x,self.y,self.z,self.vx,self.vy,self.vz,self.ax,self.ay,self.az))

	def calc_gravity(self, other):
		if self.sid == other.sid:
			return (0,0,0)

		x = self.x - other.x
		y = self.y - other.y
		z = self.z - other.z
		
		dist2 = x*x + y*y + z*z
		
		force = G*self.mass*other.mass/dist2
		
		full = math.sqrt(dist2)
		
		fx = force * x / full
		fy = force * y / full
		fz = force * z / full
	
		return (fx,fy,fz)
	
	def move_on_galaxy(self, galaxy):
		fx, fy, fz = 0, 0, 0
		for star in galaxy:
			tx, ty, tz = self.calc_gravity(star)
			fx += tx
			fy += ty
			fz += tz
		fx *= -1
		fy *= -1
		fz *= -1
		vx = self.vx + fx/self.mass
		vy = self.vy + fy/self.mass
		vz = self.vz + fz/self.mass
		x = self.x + vx
		y = self.y + vy
		z = self.z + vz
		return Star(self.mass,x,y,z,vx,vy,vz,0,0,0,self.sid)

def random_star(sid):
	return Star(random.random()*1000,
		random.random()*200-100,
		random.random()*200-100,
		random.random()*200-100,
		0,0,0,0,0,0,sid=sid)


def print_galaxy(galaxy, frame=None, ftime=None):
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
	status_row = 'Total Velocity: {} '.format(total_v)
	if frame:
		status_row += 'Frame #{} '.format(frame)
	if ftime:
		status_row += 'Processing time: {}s'.format(ftime)
	status_row = status_row.center(columns,' ') + '\n'
	result += status_row
	#result += 'done'
	print(result)
