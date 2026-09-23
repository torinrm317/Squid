from squid_generator import check_bytes, hex_encodings, fill_template, create_tag
import csv

def run():
    with open("tags.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            uid_hex = "".join(row[0].split()).upper()
            name = row[1].strip()
            create_tag(uid_hex, filename=name + ".nfc")
            print(f"Created tag for UID {uid_hex} with filename {name}.nfc")
if __name__ == "__main__":
    run()