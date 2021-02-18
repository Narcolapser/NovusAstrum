# The objective of this script is to take a frame that has been produced by na2 and create a picture.

import math
import random
import time
import sys
from PIL import Image, ImageDraw
import csv
import os

xRes = 640
yRes = 480
#xRes = 320
#yRes = 240
MAX_RAY_DEPTH = 3

gcams = []
gmesh = []
gmats = []

class Outs:
	def __init__(self,name,sizeX,sizeY,ext,counting):
		self.img = Image.new("RGB",(sizeX,sizeY))
		self.draw = ImageDraw.Draw(self.img)
		self.name = name
		self.ext = ext
		if counting:
			self.count = 0
		else:
			self.count = -1

	def drawPixelRGB(self,x,y,r,g,b):
		color = "#{0:02x}{1:02x}{2:02x}".format(int(r*255),int(g*255),int(b*255))
		self.draw.point((x,y),color)

	def drawPixelColor(self,x,y,color):
		#self.drawPixelRGB(x,y,color.r,color.g,color.b)
		self.drawPixelRGB(x,y,color.x,color.y,color.z)

	def drawPixelHash(self,x,y,val):
		self.draw.point((x,y),val)

	def save(self):
		if self.count != -1:
			self.img.save(self.name + str(self.count) + "." + self.ext,self.ext)
			self.count += 1
		else:
			self.img.save(self.name + "." + self.ext,self.ext)

#####	Geometric Objects	###################################################################
class Vector:
	def __init__(self,x,y,z,w=1):
		if not (isinstance(x,float) or isinstance(x,int)):
			message = "recieved wrong type: ".format(str(x))
			raise TypeError(message)
		self.x = x * 1.0
		self.y = y * 1.0
		self.z = z * 1.0
		self.w = w * 1.0

	def __add__(self,val):
		x = val.x + self.x
		y = val.y + self.y
		z = val.z + self.z
		return Point(x,y,z)

	def __neg__(self):
		return Point(-self.x,-self.y,-self.z)
		
	def __sub__(self,val):
		x = self.x - val.x
		y = self.y - val.y
		z = self.z - val.z
		w = self.w - val.w
		return Point(x,y,z,w)

	def __mul__(self,val):
		x = val * self.x
		y = val * self.y
		z = val * self.z
		w = self.w
		return Point(x,y,z,w)
	
	def vector_mul(self,val):
		x = val.x * self.x
		y = val.y * self.y
		z = val.z * self.z
		w = self.w
		return Vector(x,y,z,w)
	
	def mag2(self):
		return self.x**2 + self.y**2 + self.z**2		

	def mag(self):
		return math.sqrt(self.mag2())
		
	def dot(self,val):#dot product
		x = self.x * val.x
		y = self.y * val.y
		z = self.z * val.z
		w = self.w * val.w
		return x + y + z

	def cross(self,val):#cross product
		x = self.y * val.z - self.z * val.y
		y = -(self.x * val.z - self.z * val.x)
		z = self.x * val.y - self.y * val.x
		p = Point(x,y,z)
#		p.normalize()
		return p

	def normalize(self):
		self.w = self.mag()
		if self.w == 0:
			self.w = 1
			self.x /= self.w
			self.y /= self.w
			self.z /= self.w
			self.w = 0
		else:
			self.x /= self.w
			self.y /= self.w
			self.z /= self.w
			self.w = 1

	def __repr__(self):
		return "x: " + str(self.x) + " y: " + str(self.y) + " z: " + str(self.z) + " w: " + str(self.w)

class Point(Vector):
	pass

class Sphere:
	def __init__(self,center,radius,color,reflectivity,transparency):
		self.center = center
		self.position = center
		self.radius = radius
		self.color = color
		self.reflectivity = reflectivity
		self.transparency = transparency

	def RayCollides(self,ray,distance=1000000):
		m = ray.o - self.center
		b = m.dot(ray.d)
		c = m.dot(m) - (self.radius * self.radius)

		
		#Exit if r's origin outside of the sphere (c > 0) and ray is pointing away from sphere (b > 0)
		if c > 0 and b > 0:
			return 0
		discr = b*b - c

		
		#a negative discriminant corresponds to ray missing sphere
		if discr < 0:
			return 0

		# Ray now found to intersect sphere, compute smallest t value of intersection
		t = -b - math.sqrt(discr)

		#if t is negative, ray started inside sphere so clamp t to zero
		if (t < 0):
			t = 0
		q = ray.o + ray.d * t
		return (t,q)

class LineSegment:
	def __init__(self,A,B):
		self.A = A
		self.B = B

class Ray:
	def __init__(self,Origin,Direction):
		self.o = Origin
		self.d = Direction
		self.d.normalize()

	def lineSeg(self,length):
		return LineSegment(self.o,self.o + self.d*(length*1.0))

class Color(Vector):
	def __init__(self,r,g,b,a=1):
		self.x = r
		self.y = g
		self.z = b
		self.w = a
	
	def __mul__(self,val):
		val = abs(val)
		x = self.x * val
		y = self.y * val
		z = self.z * val
		return Color(x,y,z,self.w)
	
	def __repr__(self):
		return "{},{},{}".format(self.x,self.y,self.z)
		
	def __add__(self, other_color):
		x = self.x + other_color.x
		if x > 1: x = 1
		y = self.y + other_color.y
		if y > 1: y = 1
		z = self.z + other_color.z
		if z > 1: z = 1
		w = self.w + other_color.w
		if w > 1: w = 1
		return Color(x,y,z,w)
	
	def copy(self):
		return Color(self.x,self.y,self.z,self.w)
	
	def stack(self,other_color):
		# This attempts to add two colors together, getting a brighter resulting color value that
		# is still less than 1.
		x = math.sqrt(self.x**2 + other_color.x**2)
		y = math.sqrt(self.y**2 + other_color.y**2)
		z = math.sqrt(self.z**2 + other_color.z**2)
		w = math.sqrt(self.w**2 + other_color.w**2)
		return Color(x,y,z,w)
	
	def average(self,other_color):
		x = (self.x+other_color.x)/2
		y = (self.y+other_color.y)/2
		z = (self.z+other_color.z)/2
		w = (self.w+other_color.w)/2
		return Color(x,y,z,w)

class Light:
	def __init__(self,position,color):
		self.position = position
		self.color = color

def scalarTriple(a,b,c):
	return a.cross(b).dot(c)

def render(objects,lights):
	width = xRes
	height = yRes
	image = Outs("rendered_frames/frame",xRes,yRes,"BMP",True)

	invWidth = 1.0 / width
	invHeight = 1.0 / height
	fov = 30
	aspectratio = width / float(height)
	angle = math.tan(math.pi * 0.5 * fov / 180.0);
	# Trace Rays
	frames = os.listdir('./frames')
	frames.sort()
	for frame in frames:
		spheres = []
		galaxy = csv.reader(open(f'frames/{frame}'))
		for star in galaxy:
			x = float(star[2])/10
			y = float(star[3])/10
			z = float(star[4])/10-50
			size = float(star[1])
			spheres.append(Sphere(Point(x,y,z),size/1000,get_star_color(size),0,0))
		
		for y in range(height):
			for x in range(width):
				print_status(x,y,width,height)
				xx = (2 * ((x + 0.5) * invWidth) - 1) * angle * aspectratio
				yy = (1 - 2 * ((y + 0.5) * invHeight)) * angle
				ray = Ray(Point(0,0,0),Point(xx, yy, -1))
				image.drawPixelColor(x,y,trace(ray, spheres, lights, 0))
		image.save()

def print_status(x,y,width,height):
	total = width*height
	pos = 100.0 * y * width + x
	sys.stdout.write("Progress {}%\r".format(int(pos/total)))
	sys.stdout.flush()

def trace(ray,objects,lights,depth):
	min_distance = float("inf")
	collisions = []
	for obj in objects:
		result = obj.RayCollides(ray)
		if result != 0:
			collisions.append((obj, result[1], result[0]))

	if len(collisions):
		color = bg_color.copy()
		for collidee, collision_point, collision_distance in collisions:
			collision_normal = collision_point - collidee.position
			collision_normal.normalize()
			
			# Vector from Ray origin to Sphere Center
			ray_to_sphere = collidee.position - ray.o
			
			# Distance from ray origin to sphere center
			distance = math.sqrt(ray_to_sphere.dot(ray_to_sphere))
			
			# Distance until the ray is at a right angle to the center of the sphere
			ray_projection = ray_to_sphere.dot(ray.d)
			
			# How close to the center of the sphere would the ray have passed
			distance_from_center = math.sqrt(distance**2 - ray_projection**2)
			
			# The percentage from the surface of the sphere to the center of it
			distance_percent = 1 - distance_from_center / collidee.radius
			
			# To make things a little more elegant, use a exponential progression
			wieght = distance_percent**2 #not sure if I like this yet.
			
			# Stack this color with the others.
			color = color.stack(collidee.color * distance_percent)
		return color
	else:
		return bg_color #no collisions, return backgrond

def mix(a,b,mix):
	return b * mix + a * (1 - mix)

def get_distance(p1,p2):
	distance = math.sqrt((p1.x-p2.x)**2+(p1.y-p2.x)**2+(p1.z-p2.z)**2)

def get_star_color(size):
	# We are only going to work with values from 0 -> 1. Scale is a constant that should be set to the largest possible size.
	scaled = size/scale if size < scale else 1
	# Big and bright blue
	big = Color(0.75,0.9,1)
	
	# Small and smuldery
	small = Color(0.5,0,0)
	
	color = big * scaled
	color = color + (small*(1-scaled))
	return color

#bg_color = Color(1,1,1)
bg_color = Color(0,0,0)
scale = 1000

spheres = []
galaxy = csv.reader(open('frames/frame00000.csv'))
for star in galaxy:
	x = float(star[2])/10
	y = float(star[3])/10
	z = float(star[4])/10-50
	size = float(star[1])
	spheres.append(Sphere(Point(x,y,z),size/1000,get_star_color(size),0,0))


light = Light(Point( 0.0, 20, -30), Color(0.00, 0.00, 0.00));
#light = Light(Point( 0.0, 20, 0), Color(0.00, 0.00, 0.00));

start = time.time()

render(spheres,[light])
end = time.time()
print(f'Render time: {int(end-start)}')
