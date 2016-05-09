from bluesky.plans import relative_inner_product_scan
from bluesky.callbacks import LiveTable

assert slt_mb2.connected

uids = RE(relative_inner_product_scan([em], 5, slt_mb2.o, 0, 1, slt_mb2.i, 0, 1,
          md={'note': 'demo'}),
         LiveTable([slt_mb2.o, slt_mb2.i, em]))


headers = db[uids]
columns = ['time', 'em_chan22']
name_template = '{scan_id}_{note}.csv'
for h in headers:
    db.get_table(headers)[columns].to_csv(name_template.format(**h.start))


# or, in one line:
# db.get_table(db[uids])[['time', 'em_chan22']].to_csv('your_filename_here.csv')
