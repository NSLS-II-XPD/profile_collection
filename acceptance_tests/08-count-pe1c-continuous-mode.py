"""Before running this, put pe1c in continuous acquisition mode and start
acquiring."""


from bluesky.plans import count
from bluesky.callbacks import LiveTable


uid, = RE(count([pe1c]), LiveTable([pe1c]))

images = db.get_images(db[uid], 'pe1_image')
first_img = images[0]
plt.imshow(first_img)
