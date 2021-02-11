# The objective of this script is to take a frame that has been produced by na2 and create a picture.

import math
import random
import time
import sys
from PIL import Image, ImageDraw
import csv

xRes = 640
yRes = 480
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
#		color = '#ffffff'
#		if color != '#000000': print color
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

	def __contains__(self,val):
		return self.RayCollides(val)

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
	
	def __repr__(self):
		return "{},{},{}".format(self.x,self.y,self.z)

class Light:
	def __init__(self,position,color):
		self.position = position
		self.color = color

def scalarTriple(a,b,c):
	return a.cross(b).dot(c)

def render(objects,lights):
	width = xRes
	height = yRes
	image = Outs("Render",xRes,yRes,"BMP",True)

	invWidth = 1.0 / width
	invHeight = 1.0 / height
	fov = 30
	aspectratio = width / float(height)
	angle = math.tan(math.pi * 0.5 * fov / 180.0);
	# Trace Rays
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
	collidee = None
	collision_point = None
	for obj in objects:
		result = obj.RayCollides(ray)
		if result != 0:
			distance = result[0]
			if distance < min_distance:
				collidee = obj
				collision_point = result[1]
				min_distance = distance

	if not collidee:
		return bg_color #no collisions, return backgrond
	else:
		return Color(1,1,1)
#	collision_normal = collision_point - obj.position
#	collision_normal.normalize()
#	bias = 1e-4
#	inside = False
#	if ray.d.dot(collision_normal) > 0:
#		collision_normal = collision_normal * (-1.0)
#		inside = False

##	if (collidee.transparency > 0 or collidee.reflectivity > 0) and depth < MAX_RAY_DEPTH:
###	if False:
##		facingratio = ray.d.dot(collision_normal) * (-1.0)
##		# change the mix value to tweak the effect
##		fresneleffect = mix(math.pow(1 - facingratio, 3), 1, 0.1)
##		# compute reflection direction (not need to normalize because all vectors
##		# are already normalized)
##		refldir = ray.d - collision_normal * 2 * ray.d.dot(collision_normal)
##		refldir.normalize()
##		reflray = Ray(collision_point + collision_normal * bias,refldir)
##		reflection = trace(reflray, objects,lights, depth + 1)
##		
##		refraction = Point(0,0,0)
##		# if the sphere is also transparent compute refraction ray (transmission)
##		if collidee.transparency:
##			ior = 1.1
##			eta = ior if inside else 1 # are we inside or outside the surface?
##			cosi = 0 - collision_normal.dot(ray.d)
##			k = 1 - eta * eta * (1 - cosi * cosi)
##			refrdir = ray.d * eta + collision_normal * (eta * cosi - math.sqrt(k))
##			refrdir.normalize()
##			refrray = Ray(collision_point + collision_normal * bias,refrdir)
##			refraction = trace(refrray, objects, lights, depth + 1)

##		#the result is a mix of reflection and refraction (if the sphere is transparent)
##		flec = reflection * fresneleffect
##		#frac = refraction * (1 - fresneleffect) * collidee.transparency
##		frac = refraction * (1 - fresneleffect)
##		both = flec + frac
##		return both
##		surfaceColor = both.vector_mul(collidee.color)
##		return surfaceColor

##	else:
#	light = lights[0]
#	collision_normal = collision_point - obj.position
#	lightDirection = light.position - collision_point
#	lightDirection.normalize()
#	rayPosition = collision_point + collision_normal * bias
##		rayPosition = collision_point + collision_normal
#	isShadow = False
#	for obj in objects:
#		if obj == collidee:
#			continue
#		result = obj.RayCollides(Ray(rayPosition,lightDirection))
#		if result != 0:
#			isShadow = True
#			break
#			
#	if isShadow:
#		return Color(0,0,0)
##			return collidee.color * 0.1
#	else:
#		return collidee.color

def mix(a,b,mix):
	return b * mix + a * (1 - mix)

def get_distance(p1,p2):
	distance = math.sqrt((p1.x-p2.x)**2+(p1.y-p2.x)**2+(p1.z-p2.z)**2)

#bg_color = Color(1,1,1)
bg_color = Color(0,0,0)

spheres = []
#position, radius, surface color, reflectivity, transparency,
#spheres.append(Sphere(Point(0.0,-10004,-20),10000,Color(0.2,0.2,0.2),0,0))
#spheres.append(Sphere(Point(0.0,0,-10),0.4,Color(1.0,0.32,0.36),1,0.5))
#spheres.append(Sphere(Point(5.0,-1,-15),0.2,Color(0.9,0.76,0.46), 1, 0.0))
#spheres.append(Sphere(Point(5.0, 0, -25), 0.3, Color(0.65, 0.77, 0.97), 1, 0.0))
#spheres.append(Sphere(Point(-5.5,0,-15), 0.3, Color(0.9,0.9,0.9),1,0))
#spheres.append(Sphere(Point(0,0,-15), 0.3, Color(0.9,0.0,0.9),1,0))

galaxy = csv.reader(open('frames/frame00000.csv'))
for star in galaxy:
    x = float(star[2])/10
    y = float(star[3])/10
    z = float(star[4])/10-50
    size = float(star[1])/1000
    spheres.append(Sphere(Point(x,y,z),size,Color(0.2,0.2,0.2),0,0))


light = Light(Point( 0.0, 20, -30), Color(0.00, 0.00, 0.00));
#light = Light(Point( 0.0, 20, 0), Color(0.00, 0.00, 0.00));

start = time.time()

render(spheres,[light])
end = time.time()
print(f'Render time: {int(end-start)}')
