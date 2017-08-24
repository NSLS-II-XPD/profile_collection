from bluesky.callbacks.broker import LiveTiffExporter


class SubtractedTiffExporter(LiveTiffExporter):
    "Intercept images before saving and subtract dark image"

    def start(self, doc):
        # The metadata refers to the scan uid of the dark scan.
        if 'dark_frame' not in doc:
            raise ValueError("No dark_frame was recorded.")
        uid = doc['dark_frame']
        dark_header = db[uid]
        self.dark_img, = get_images(db[uid], 'pe1_image')
        super().start(doc)

    def event(self, doc):
        img = doc['data'][self.field]
        subtracted_img = img - self.dark_img
        doc['data'][self.field] = subtracted_img
        super().event(doc)

template = "/home/xf28id1/xpdUser/tiff_base/LaB6_EPICS/{start.sa_name}_{start.scan_id}_step{event.seq_num}.tif"
exporter = SubtractedTiffExporter('pe1_image', template)
