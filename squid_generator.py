import io
import time

try:
    import sys
    ON_FLIPPER = sys.implementation.name == "micropython"
except Exception:
    ON_FLIPPER = True

if ON_FLIPPER:
    import flipperzero as f0  # type: ignore
    BASE_DIR = "/ext/apps_assets/upython/"   
    TEMPLATE_PATH = BASE_DIR + "template.nfc"
    OUTPUT_DIR = "/ext/nfc/"                 
else:
    f0 = None
    TEMPLATE_PATH = "template.nfc"       
    OUTPUT_DIR = ""

OUTPUT_NAME = "tag"
HEX_DIGITS = "0123456789ABCDEF"




def check_bytes(uid): # calculate check bytes
    """uid is a list of 7 ints. Returns the two check bytes as 2-digit hex."""
    bcc0 = 0x88 ^ uid[0] ^ uid[1] ^ uid[2]      # 0x88 = cascade tag (136)
    bcc1 = uid[3] ^ uid[4] ^ uid[5] ^ uid[6]
    return "%02X" % bcc0, "%02X" % bcc1


def hex_encodings(uid_hex):
    """ASCII codes of the 14 UID characters, split 2 / 4 / 4 / 4."""
    codes = ["%02X" % ord(c) for c in uid_hex]
    return (
        " ".join(codes[0:2]),
        " ".join(codes[2:6]),
        " ".join(codes[6:10]),
        " ".join(codes[10:14]),
    )


def fill_template(template, uid_bytes_hex, uid_hex):
    """Replace the HEX1..7, CHECKBYTE1/2 and EN1..4 markers."""
    uid = [int(b, 16) for b in uid_bytes_hex]
    cb1, cb2 = check_bytes(uid)
    en = hex_encodings(uid_hex)

    for i in range(7):
        template = template.replace("HEX%d" % (i + 1), uid_bytes_hex[i])
    template = template.replace("CHECKBYTE1", cb1)
    template = template.replace("CHECKBYTE2", cb2)
    for i in range(4):
        template = template.replace("EN%d" % (i + 1), en[i])
    return template


def file_exists(path):
    try:
        f = io.open(path, "r")
        f.close()
        return True
    except Exception:
        return False


def free_filename():
    """tag.nfc, or tag-0.nfc, tag-1.nfc ... if it already exists."""
    name = OUTPUT_DIR + OUTPUT_NAME
    if not file_exists(name + ".nfc"):
        return name + ".nfc"
    i = 0
    while file_exists("%s%s-%d.nfc" % (OUTPUT_DIR, OUTPUT_NAME, i)):
        i += 1
    return "%s%s-%d.nfc" % (OUTPUT_DIR, OUTPUT_NAME, i)


def create_tag(uid_hex, filename=None):

    uid_hex = uid_hex.upper()
    uid_bytes_hex = [uid_hex[i:i + 2] for i in range(0, 14, 2)]

    f = io.open(TEMPLATE_PATH, "r")
    template = f.read()
    f.close()

    if filename is not None:
        out_path = filename
    else:
        out_path = free_filename()

    f = io.open(out_path, "w")
    f.write(fill_template(template, uid_bytes_hex, uid_hex))
    f.close()
    return out_path




def run_pc():
    raw = input("Enter the UID (7 hex bytes separated by spaces): ")
    parts = raw.split()
    if len(parts) != 7 or any(len(p) != 2 for p in parts):
        print("Need exactly 7 two-digit hex bytes, e.g. 04 A1 B2 C3 D4 E5 F6")
        return
    uid_hex = "".join(parts).upper()
    uid = [int(p, 16) for p in parts]
    cb1, cb2 = check_bytes(uid)
    en = hex_encodings(uid_hex)
    print("1st check byte is:", cb1)
    print("2nd check byte is:", cb2)
    for i in range(4):
        print("hex encoding%d is: %s" % (i + 1, en[i]))
    print("Wrote", create_tag(uid_hex))



digits = [0] * 14     # the 14 hex digits as numbers 0-15
cursor = 0
finished = False
cancelled = False
error = None          


def draw():
    f0.canvas_clear()
    f0.canvas_set_color(f0.COLOR_BLACK)
    f0.canvas_set_text_align(f0.ALIGN_BEGIN, f0.ALIGN_BEGIN)

    f0.canvas_set_font(f0.FONT_SECONDARY)
    f0.canvas_set_text(2, 1, "UID (7 bytes)")
    f0.canvas_set_text(2, 54, "U/D:digit L/R:move OK:go")

    f0.canvas_set_font(f0.FONT_PRIMARY)
    for i in range(14):
        row = 0 if i < 8 else 1
        col = i if i < 8 else i - 8
        x = 6 + col * 12 + (col // 2) * 6     # small gap between bytes
        y = 14 + row * 16
        f0.canvas_set_text(x, y, HEX_DIGITS[digits[i]])
        if i == cursor:
            f0.canvas_draw_line(x, y + 12, x + 8, y + 12)
    f0.canvas_update()


def on_input(button, event):
    global cursor, finished, cancelled, error
    try:
        if button == f0.INPUT_BUTTON_BACK and event == f0.INPUT_TYPE_LONG:
            cancelled = True
            return
        if event != f0.INPUT_TYPE_SHORT and event != f0.INPUT_TYPE_REPEAT:
            return

        if button == f0.INPUT_BUTTON_UP:
            digits[cursor] = (digits[cursor] + 1) % 16
        elif button == f0.INPUT_BUTTON_DOWN:
            digits[cursor] = (digits[cursor] - 1) % 16
        elif button == f0.INPUT_BUTTON_RIGHT:
            cursor = min(cursor + 1, 13)
        elif button == f0.INPUT_BUTTON_LEFT:
            cursor = max(cursor - 1, 0)
        elif button == f0.INPUT_BUTTON_OK and event == f0.INPUT_TYPE_SHORT:
            finished = True
            return
        draw()
    except Exception as e:
        error = e


if ON_FLIPPER:
    f0.on_input(on_input)   

def show_message(header, text):
    f0.dialog_message_set_header(header, 64, 4, f0.ALIGN_CENTER, f0.ALIGN_BEGIN)
    f0.dialog_message_set_text(text, 64, 24, f0.ALIGN_CENTER, f0.ALIGN_BEGIN)
    f0.dialog_message_set_button("OK", f0.INPUT_BUTTON_OK)
    f0.dialog_message_show()


def run_flipper():
    draw()
    while not finished and not cancelled and error is None:
        time.sleep_ms(20)
    if error is not None:
        raise error
    if cancelled:
        return

    uid_hex = "".join(HEX_DIGITS[d] for d in digits)
    path = create_tag(uid_hex)
    show_message("Saved", path.replace(OUTPUT_DIR, ""))


def main():
    if ON_FLIPPER:
        try:
            run_flipper()
        except Exception as e:
            print("error:", repr(e))
            show_message("Error", repr(e)[:60])
    else:
        run_pc()


if __name__ == "__main__":
    main()