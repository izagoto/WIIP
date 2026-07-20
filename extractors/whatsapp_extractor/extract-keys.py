import argparse
import xml.etree.ElementTree as ET


def extract_encryption_key(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        encryption_key_parts = []

        for node in root.iter("node"):
            if node.attrib.get("class") == "android.widget.EditText":
                text = node.attrib.get("text")
                if text:
                    encryption_key_parts.append(text)

        encryption_key = "".join(encryption_key_parts)
        return encryption_key, None
    except Exception as e:
        return None, str(e)


def main():
    print("-" * 48)
    print("Copyright © 2024 4n6. All rights reserved")
    print("-" * 48)
    parser = argparse.ArgumentParser(description="Extract encryption key from phone.")
    parser.add_argument("--file", type=str, required=True, help="Path to the file containing the encryption key.")
    parser.add_argument(
        "--output", type=str, required=True, help="Path to the output file to save the extracted encryption key."
    )

    args = parser.parse_args()

    encryption_key, error = extract_encryption_key(args.file)

    if encryption_key:
        try:
            with open(args.output, "w") as f:
                f.write(encryption_key)
            print("Encryption key successfully extracted and saved.")
        except Exception as e:
            print(f"Failed to write encryption key to file: {e}")
    else:
        print(f"Failed to extract encryption key: {error}")


if __name__ == "__main__":
    main()