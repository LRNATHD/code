from fbreader_client import get_client
import json

client = get_client()
xml_data = client.fetch_opds_catalog()

if xml_data:
    print("OPDS Data Length:", len(xml_data))
    with open("opds_dump.xml", "w", encoding="utf-8") as f:
        f.write(xml_data)
    print("Saved to opds_dump.xml")
else:
    print("Failed to fetch OPDS")
