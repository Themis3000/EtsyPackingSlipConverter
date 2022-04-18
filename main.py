from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure
from PIL import Image
import base64
from io import BytesIO

# Begin extraction

page_layout = next(extract_pages("in.pdf"))

# Extract items
items = []
page_iter = iter(page_layout)
while True:
    item_name = next(page_iter).get_text()[:-1]
    if item_name == "Item total":
        break
    item_quantity = next(page_iter).get_text()[:-1]
    items.append({"item_name": item_name, "item_quantity": item_quantity})

# Extract prices
next(page_iter)
next(page_iter)
next(page_iter)
totals = {
    "item_total": next(page_iter).get_text()[:-1],
    "tax": next(page_iter).get_text()[:-1],
    "shipping_total": next(page_iter).get_text()[:-1],
    "order_total": next(page_iter).get_text()[:-1]
}

# Extract shop name
shop_identity = next(page_iter).get_text().split("\n")
name = shop_identity[0]
url = shop_identity[1]

# Extract ship to
next(page_iter)
ship_to = next(page_iter).get_text()[8:-1]

# Extract ship by
ship_by = next(page_iter).get_text()[21:-1]

# Extract from
ship_from = next(page_iter).get_text()[5:-1]

# Extract order #
order_num = next(page_iter).get_text()[6:-1]

# Extract order date
order_date = next(page_iter).get_text()[11:-1]

# Extract buyer
buyer_identity = next(page_iter).get_text().split("\n")
buyer_name = buyer_identity[1]
buyer_id = buyer_identity[2]

# Extract payment method
payment_method = next(page_iter).get_text()[15:-1]

# Extract shipping method
shipping_method = next(page_iter).get_text()[16:-1].replace("\n", "")

# Extract tracking
tracking_data = next(page_iter).get_text().split("\n")
tracking_number = tracking_data[1]
tracking_via = tracking_data[2]

# Extract shop logo
while True:
    element = next(page_iter)
    if isinstance(element, LTFigure):
        img_element = next(iter(element))
        shop_logo = Image.open(BytesIO(img_element.stream.rawdata))
        break

# Extract item thumbnails
for i in range(len(items)):
    while True:
        element = next(page_iter)
        if isinstance(element, LTFigure):
            img_element = next(iter(element))
            items[i - 1]["image"] = Image.open(BytesIO(img_element.stream.rawdata))
            break

item_amount_str = "1 item" if len(items) == 1 else f"{len(items)} items"

# Begin rebuilding
with open("template.html", "r") as f:
    template = f.read()

with open("item_template.html", "r") as f:
    item_template = f.read()


def update_value(key, value, fix_breaks=True):
    global template
    html_value = value.replace("\n", "<br>") if fix_breaks else value
    template = template.replace("{" + key + "}", html_value)


update_value("name", name)
update_value("url", url)
update_value("ship_to", ship_to)
update_value("ship_by", ship_by)
update_value("order_num", order_num)
update_value("buyer_name", buyer_name)
update_value("buyer_id", buyer_id)
update_value("shipping_method", shipping_method)
update_value("ship_from", ship_from)
update_value("order_date", order_date)
update_value("payment_method", payment_method)
update_value("tracking_number", tracking_number)
update_value("tracking_via", tracking_via)
update_value("item_amount_str", item_amount_str)
update_value("item_total", totals["item_total"])
update_value("tax", totals["tax"])
update_value("shipping_total", totals["shipping_total"])
update_value("order_total", totals["order_total"])

items_html = ""
for item in items:
    item_html = item_template


    def update_item_value(key, value):
        global item_html
        item_html = item_html.replace("{" + key + "}", value)


    img_buffer = BytesIO()
    item["image"].save(img_buffer, format="JPEG")
    img_str = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
    update_item_value("img_b64", img_str)
    update_item_value("item_name", item["item_name"])
    update_item_value("item_quantity", item["item_quantity"])
    items_html += item_html

update_value("items", items_html, fix_breaks=False)

with open("out.html", "w") as f:
    f.write(template)
