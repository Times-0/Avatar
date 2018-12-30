from PIL import Image

from flask import Flask, send_file, request, abort
from flask_sqlalchemy import SQLAlchemy

from StringIO import StringIO
import requests, os

app = Flask(__name__)
AVAILABLE_SIZES = [60, 88, 95, 120, 300, 600]

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@127.0.0.1/timeline'
database = SQLAlchemy(app)

def downloadImage(image, size = 120):
	path = 'http://icer.ink/mobcdn.clubpenguin.com/game/items/images/paper/image/{}/{}.png'.format(size, image)

	print 'Downloading...', path

	dimg = requests.get(path)
	image_p = 'Avatar/paper/{}/{}.png'.format(size, image)

	p = '/'.join(image_p.split('/')[:-1])
	if not os.path.exists(p): os.makedirs(p)

	sprite = Image.open(StringIO(dimg.content))
	sprite.save(image_p)

	return sprite

def initializeImage(items, size = 120):
	path = 'Avatar/paper/{}/{}.png'.format(size, '{}')

	sprites = list()

	for i in items:
		if i == 0:
			sprites.append(Image.new('RGBA', (size, size), (0, 0, 0, 0)))
			continue 

		if not os.path.exists(path.format(i)):
			sprites.append(downloadImage(i, size))
		else:
			sprite = Image.open(path.format(i))
			sprites.append(sprite)

	return sprites

def buildAvatar(images):
	Avatar = images[0]
	for i in images[1:]:
		Avatar.paste(i, (0, 0), i)

	AvatarIO = StringIO() 
	Avatar.save(AvatarIO, 'PNG', quality = 100)
	AvatarIO.seek(0)

	return AvatarIO

@app.route('/<path:m>/crossdomain.xml', methods = ['GET'])
@app.route('/crossdomain.xml', methods = ['GET'])
def handleCrossdomain(m = None):
	return '<cross-domain-policy><allow-access-from domain="*"/></cross-domain-policy>'

@app.route("/<swid>/cp", methods = ['GET'])
def getAvatar(swid):
	size = 120
	try:
		if request.args.has_key('size'):
			size = int(request.args.get('size'))

		if not size in AVAILABLE_SIZES:
			size = 120
	except:
		pass
    
	details = database.engine.execute("SELECT Photo, Color, Head, Face, Neck, Body, Hand, Feet, Pin FROM avatars a, penguins p WHERE p.id = a.penguin_id and p.swid = %s", swid)
	details = details.first()
	if details is None:
		return abort(404)

	items = initializeImage(list(map(int, details)), size)

	return send_file(buildAvatar(items), mimetype='image/png')

app.run(host = 'cdn.avatar.clubpenguin.com', port = 80, debug = True)
