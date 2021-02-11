from star import Star, random_star, print_galaxy
import time
from multiprocessing import Pool
import sqlite3
import os

def galmove(seg):
	rets = []
	for parts in seg:
		star, galaxy = parts
		rets.append(star.move_on_galaxy(galaxy))
	return rets

frames = os.listdir('frames')
frames.sort()
procs = 24
if len(frames) == 0:
	galaxy = [random_star(i+1) for i in range(420*procs)]
	i = -1
else:
	rows = open('frames/' + frames[-1]).readlines()
	galaxy = []
	i = int(frames[-1][5:10])
	for row in rows:
		s = row.split(',')
		galaxy.append(Star(float(s[1]),float(s[2]),float(s[3]),float(s[4]),float(s[5]),float(s[6]),float(s[7]),0,0,0,float(s[0])))

segment = int(len(galaxy)/procs)
pool = Pool(processes=procs)

while True:
	i += 1
	steps = 100
	start = time.time()
	for j in range(100):
		full_args = [(star,galaxy) for star in galaxy]
		args = [full_args[x:x+segment] for x in range(0, len(full_args), segment)]
		gs = pool.map(galmove,args)
		galaxy = []
		for g in gs:
			galaxy += g
	
	print_galaxy(galaxy,i,time.time()-start)
	f = open('frames/frame{:0>5}.csv'.format(i),'w')
	for star in galaxy:
		f.write('{sid},{mass},{x},{y},{z},{vx},{vy},{vz}\n'.format(sid=star.sid, mass=star.mass, x=star.x, y=star.y, z=star.z, vx=star.vx, vy=star.vy, vz=star.vz))
	f.close()



#def pool_step(stars):
#	stars2 = pool.map(calc_star_accel,[(star,stars) for star in stars])
#	stars3 = pool.map(calc_star_move,stars2)
##	for star in stars2:
##		star.calc_move()
#	return stars3
